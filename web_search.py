"""
Web Search Module
Provides web search capabilities using multiple search engines
"""

import aiohttp
import logging
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class WebSearcher:
    """Handles web search operations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize web searcher

        Args:
            config: Configuration with search engine and API keys
        """
        self.config = config
        self.engine = config.get('engine', 'duckduckgo')
        self.max_results = config.get('max_results', 10)

        logger.info(f"Web Searcher initialized with engine: {self.engine}")

    async def search(self, query: str, num_results: int = None) -> Dict[str, Any]:
        """
        Search the web for a query

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            Search results dictionary
        """
        num_results = num_results or self.max_results
        logger.info(f"Searching for: {query} (max {num_results} results)")

        if self.engine == 'duckduckgo':
            return await self._search_duckduckgo(query, num_results)
        elif self.engine == 'google':
            return await self._search_google(query, num_results)
        else:
            raise ValueError(f"Unsupported search engine: {self.engine}")

    async def _search_duckduckgo(self, query: str, num_results: int) -> Dict:
        """Search using DuckDuckGo"""
        try:
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

            results = []

            # Extract abstract
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'DuckDuckGo Result'),
                    'snippet': data.get('Abstract', ''),
                    'url': data.get('AbstractURL', ''),
                    'source': data.get('AbstractSource', '')
                })

            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', '')
                    })

            return {
                'query': query,
                'engine': 'duckduckgo',
                'num_results': len(results),
                'results': results
            }

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {'query': query, 'error': str(e), 'results': []}

    async def _search_google(self, query: str, num_results: int) -> Dict:
        """
        Search using Google Custom Search API
        Requires API key in config
        """
        api_key = self.config.get('google_api_key')
        search_engine_id = self.config.get('google_search_engine_id')

        if not api_key or not search_engine_id:
            return {
                'error': 'Google API credentials not configured',
                'results': []
            }

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': min(num_results, 10)
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'url': item.get('link', ''),
                    'source': item.get('displayLink', '')
                })

            return {
                'query': query,
                'engine': 'google',
                'num_results': len(results),
                'results': results
            }

        except Exception as e:
            logger.error(f"Google search error: {e}")
            return {'query': query, 'error': str(e), 'results': []}

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL

        Args:
            url: URL to scrape

        Returns:
            Scraped content dictionary
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')

            # Extract text content
            text = soup.get_text(separator='\n', strip=True)

            # Extract title
            title = soup.title.string if soup.title else ''

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''

            return {
                'url': url,
                'title': title,
                'description': description,
                'text': text[:5000],  # Limit text length
                'success': True
            }

        except Exception as e:
            logger.error(f"URL scraping error for {url}: {e}")
            return {'url': url, 'success': False, 'error': str(e)}
