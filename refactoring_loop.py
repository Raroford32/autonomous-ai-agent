"""
Autonomous Refactoring Loop
Continuously analyzes and improves agent's own code
"""

import logging
import ast
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RefactoringLoop:
    """
    Autonomous refactoring system that improves agent code
    """

    def __init__(self, agent_ref):
        self.agent = agent_ref
        self.refactoring_history: List[Dict] = []
        self.code_quality_metrics: Dict[str, float] = {}

        logger.info("Refactoring Loop initialized")

    async def analyze_codebase(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze codebase for improvement opportunities"""
        logger.info(f"Analyzing {len(file_paths)} files")

        analysis = {
            'files_analyzed': len(file_paths),
            'issues_found': [],
            'suggestions': [],
            'metrics': {}
        }

        for filepath in file_paths:
            file_analysis = await self._analyze_file(filepath)
            analysis['issues_found'].extend(file_analysis['issues'])
            analysis['suggestions'].extend(file_analysis['suggestions'])
            analysis['metrics'][filepath] = file_analysis['metrics']

        return analysis

    async def _analyze_file(self, filepath: str) -> Dict:
        """Analyze a single file"""
        try:
            with open(filepath, 'r') as f:
                code = f.read()

            # Parse AST
            tree = ast.parse(code)

            # Calculate metrics
            metrics = self._calculate_code_metrics(tree, code)

            # Identify issues
            issues = self._identify_issues(tree, code, metrics)

            # Generate suggestions
            suggestions = await self._generate_suggestions(filepath, code, issues, metrics)

            return {
                'issues': issues,
                'suggestions': suggestions,
                'metrics': metrics
            }

        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {e}")
            return {'issues': [], 'suggestions': [], 'metrics': {}}

    def _calculate_code_metrics(self, tree: ast.AST, code: str) -> Dict[str, float]:
        """Calculate code quality metrics"""
        metrics = {
            'lines_of_code': len(code.split('\n')),
            'num_functions': 0,
            'num_classes': 0,
            'max_complexity': 0,
            'avg_function_length': 0,
            'documentation_ratio': 0.0
        }

        function_lengths = []
        docstring_count = 0
        total_definitions = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics['num_functions'] += 1
                total_definitions += 1

                # Function length
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    func_len = node.end_lineno - node.lineno
                    function_lengths.append(func_len)

                # Docstring
                if ast.get_docstring(node):
                    docstring_count += 1

                # Complexity (simple approximation)
                complexity = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While, ast.Try)))
                metrics['max_complexity'] = max(metrics['max_complexity'], complexity)

            elif isinstance(node, ast.ClassDef):
                metrics['num_classes'] += 1
                total_definitions += 1
                if ast.get_docstring(node):
                    docstring_count += 1

        if function_lengths:
            metrics['avg_function_length'] = sum(function_lengths) / len(function_lengths)

        if total_definitions > 0:
            metrics['documentation_ratio'] = docstring_count / total_definitions

        return metrics

    def _identify_issues(self, tree: ast.AST, code: str, metrics: Dict) -> List[Dict]:
        """Identify code issues"""
        issues = []

        # Long functions
        if metrics['avg_function_length'] > 50:
            issues.append({
                'type': 'long_functions',
                'severity': 'medium',
                'description': 'Functions are too long (avg > 50 lines)'
            })

        # High complexity
        if metrics['max_complexity'] > 10:
            issues.append({
                'type': 'high_complexity',
                'severity': 'high',
                'description': f"High cyclomatic complexity ({metrics['max_complexity']})"
            })

        # Poor documentation
        if metrics['documentation_ratio'] < 0.5:
            issues.append({
                'type': 'poor_documentation',
                'severity': 'low',
                'description': f"Low documentation ratio ({metrics['documentation_ratio']:.2%})"
            })

        # Check for code smells
        code_lower = code.lower()
        if code.count('try:') > code.count('except'):
            issues.append({
                'type': 'bare_except',
                'severity': 'medium',
                'description': 'Possible bare except clauses'
            })

        return issues

    async def _generate_suggestions(self, filepath: str, code: str, issues: List[Dict], metrics: Dict) -> List[str]:
        """Generate refactoring suggestions"""
        if not issues:
            return []

        prompt = f"""Analyze this code and provide specific refactoring suggestions:

        File: {filepath}
        Issues found: {json.dumps(issues, indent=2)}
        Metrics: {json.dumps(metrics, indent=2)}

        Code snippet (first 1000 chars):
        {code[:1000]}

        Provide 3-5 specific, actionable refactoring suggestions:"""

        response = await self.agent.llm.query(prompt)
        suggestions = [line.strip() for line in response.split('\n') if line.strip() and line.strip()[0].isdigit()]

        return suggestions

    async def auto_refactor(self, filepath: str, backup: bool = True) -> bool:
        """Automatically refactor a file"""
        logger.info(f"Auto-refactoring: {filepath}")

        try:
            # Read original code
            with open(filepath, 'r') as f:
                original_code = f.read()

            # Backup if requested
            if backup:
                backup_path = f"{filepath}.backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                with open(backup_path, 'w') as f:
                    f.write(original_code)
                logger.info(f"Backup created: {backup_path}")

            # Generate refactored code
            refactored = await self._refactor_code(original_code, filepath)

            # Validate refactored code
            if await self._validate_refactoring(original_code, refactored):
                # Write refactored code
                with open(filepath, 'w') as f:
                    f.write(refactored)

                logger.info(f"Successfully refactored: {filepath}")

                # Record refactoring
                self.refactoring_history.append({
                    'filepath': filepath,
                    'timestamp': datetime.utcnow().isoformat(),
                    'success': True
                })

                return True
            else:
                logger.warning(f"Refactoring validation failed: {filepath}")
                return False

        except Exception as e:
            logger.error(f"Auto-refactoring failed: {e}")
            return False

    async def _refactor_code(self, code: str, filepath: str) -> str:
        """Generate refactored code"""
        prompt = f"""Refactor this Python code to improve quality:

        Requirements:
        - Maintain all functionality
        - Improve readability
        - Reduce complexity
        - Add documentation
        - Follow best practices
        - Keep the same interface/API

        Original code:
        {code}

        Provide the complete refactored code:"""

        refactored = await self.agent.llm.query(prompt)
        return refactored

    async def _validate_refactoring(self, original: str, refactored: str) -> bool:
        """Validate that refactoring maintains functionality"""
        try:
            # Check syntax
            ast.parse(refactored)

            # Check that it doesn't remove major functionality
            # (simplified check)
            original_funcs = len([n for n in ast.walk(ast.parse(original)) if isinstance(n, ast.FunctionDef)])
            refactored_funcs = len([n for n in ast.walk(ast.parse(refactored)) if isinstance(n, ast.FunctionDef)])

            if refactored_funcs < original_funcs * 0.8:
                logger.warning("Refactoring removed too many functions")
                return False

            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
