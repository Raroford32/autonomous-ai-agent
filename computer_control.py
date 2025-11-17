"""
Computer Control Module
Provides capabilities to control mouse, keyboard, screen capture, and system operations
"""

import pyautogui
import subprocess
import platform
import logging
from typing import Dict, Any, List, Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)


class ComputerController:
    """Handles all computer control operations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize computer controller

        Args:
            config: Configuration with allowed actions and safety settings
        """
        self.config = config
        self.allowed_actions = config.get('allowed_actions', ['screenshot'])
        self.safe_mode = config.get('safe_mode', True)

        # Set up PyAutoGUI safety features
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        logger.info(f"Computer Controller initialized with actions: {self.allowed_actions}")

    async def execute_action(self, action_type: str, params: Dict) -> Any:
        """
        Execute a computer control action

        Args:
            action_type: Type of action (mouse, keyboard, screenshot, etc.)
            params: Parameters for the action

        Returns:
            Result of the action
        """
        if action_type not in self.allowed_actions:
            raise PermissionError(f"Action {action_type} not allowed")

        if action_type == 'screenshot':
            return await self.take_screenshot(params.get('region'))

        elif action_type == 'mouse_move':
            return await self.mouse_move(params['x'], params['y'])

        elif action_type == 'mouse_click':
            return await self.mouse_click(params.get('button', 'left'))

        elif action_type == 'keyboard_type':
            return await self.keyboard_type(params['text'])

        elif action_type == 'keyboard_press':
            return await self.keyboard_press(params['key'])

        elif action_type == 'run_command':
            return await self.run_command(params['command'])

        elif action_type == 'find_on_screen':
            return await self.find_on_screen(params['image_path'])

        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def take_screenshot(self, region: Tuple[int, int, int, int] = None) -> str:
        """
        Take a screenshot of the screen or a region

        Args:
            region: Optional (x, y, width, height) tuple

        Returns:
            Path to saved screenshot
        """
        logger.info(f"Taking screenshot, region: {region}")

        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        # Save screenshot
        filepath = f'/tmp/screenshot_{hash(str(region))}.png'
        screenshot.save(filepath)

        return filepath

    async def mouse_move(self, x: int, y: int, duration: float = 0.5) -> Dict:
        """Move mouse to coordinates"""
        if self.safe_mode:
            logger.info(f"Safe mode: Would move mouse to ({x}, {y})")
            return {'action': 'simulated', 'x': x, 'y': y}

        pyautogui.moveTo(x, y, duration=duration)
        return {'action': 'completed', 'x': x, 'y': y}

    async def mouse_click(self, button: str = 'left', clicks: int = 1) -> Dict:
        """Click mouse button"""
        if self.safe_mode:
            logger.info(f"Safe mode: Would click {button} button {clicks} times")
            return {'action': 'simulated', 'button': button, 'clicks': clicks}

        pyautogui.click(button=button, clicks=clicks)
        return {'action': 'completed', 'button': button, 'clicks': clicks}

    async def keyboard_type(self, text: str, interval: float = 0.05) -> Dict:
        """Type text using keyboard"""
        if self.safe_mode:
            logger.info(f"Safe mode: Would type text: {text[:50]}...")
            return {'action': 'simulated', 'text': text}

        pyautogui.typewrite(text, interval=interval)
        return {'action': 'completed', 'text': text}

    async def keyboard_press(self, key: str) -> Dict:
        """Press a specific key"""
        if self.safe_mode:
            logger.info(f"Safe mode: Would press key: {key}")
            return {'action': 'simulated', 'key': key}

        pyautogui.press(key)
        return {'action': 'completed', 'key': key}

    async def run_command(self, command: str) -> Dict:
        """
        Run a system command

        Args:
            command: Command to run

        Returns:
            Command output and return code
        """
        if self.safe_mode:
            logger.warning(f"Safe mode: Would run command: {command}")
            return {'action': 'simulated', 'command': command}

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                'action': 'completed',
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'action': 'failed', 'error': 'Command timeout'}
        except Exception as e:
            return {'action': 'failed', 'error': str(e)}

    async def find_on_screen(self, image_path: str) -> Dict:
        """
        Find an image on screen using template matching

        Args:
            image_path: Path to template image

        Returns:
            Coordinates if found, None otherwise
        """
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.8)

            if location:
                center = pyautogui.center(location)
                return {
                    'found': True,
                    'x': center.x,
                    'y': center.y,
                    'box': location
                }
            else:
                return {'found': False}
        except Exception as e:
            return {'found': False, 'error': str(e)}

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions"""
        return pyautogui.size()

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        return pyautogui.position()
