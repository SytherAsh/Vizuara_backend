"""
Wikipedia Service
Handles Wikipedia search and content extraction
"""

import wikipedia
import logging
import time
import re
from typing import Dict, List, Union, Any
from datetime import datetime

logger = logging.getLogger("VidyAI_Flask")


class WikipediaService:
    """Service for Wikipedia operations"""
    
    def __init__(self, language: str = "en"):
        """
        Initialize Wikipedia service
        
        Args:
            language: Wikipedia language code
        """
        self.language = language
        wikipedia.set_lang(language)
        logger.info(f"WikipediaService initialized with language: {language}")
    
    def set_language(self, language: str):
        """Change Wikipedia language"""
        self.language = language
        wikipedia.set_lang(language)
        logger.info(f"Wikipedia language changed to: {language}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize string for filename use"""
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
        return sanitized[:200]
    
    def search_wikipedia(self, query: str, results_limit: int = 15, retries: int = 3) -> Union[List[str], Dict[str, str]]:
        """
        Search Wikipedia for a query
        
        Args:
            query: Search query
            results_limit: Maximum number of results
            retries: Number of retry attempts
            
        Returns:
            List of search results or error dict
        """
        if not query or not query.strip():
            return {'error': 'Please enter a valid search term'}
        
        query = query.strip()
        logger.info(f"Searching Wikipedia for: {query}")
        
        attempt = 0
        while attempt < retries:
            try:
                search_results = wikipedia.search(query, results=results_limit)
                
                if not search_results:
                    suggestions = wikipedia.suggest(query)
                    if suggestions:
                        logger.info(f"No results found. Suggesting: {suggestions}")
                        return {'error': f'No exact results found. Did you mean: {suggestions}?'}
                    logger.info("No results found and no suggestions available")
                    return {'error': 'No results found for your search'}
                
                logger.info(f"Found {len(search_results)} results for query: {query}")
                return search_results
                
            except ConnectionError as e:
                attempt += 1
                wait_time = 2 ** attempt
                logger.warning(f"Connection error (attempt {attempt}/{retries}): {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Search error: {str(e)}")
                return {'error': f'An error occurred while searching: {str(e)}'}
        
        return {'error': 'Failed to connect to Wikipedia after multiple attempts. Please check your internet connection'}
    
    def get_page_info(self, title: str, retries: int = 3) -> Dict[str, Any]:
        """
        Get detailed information about a Wikipedia page
        
        Args:
            title: Page title
            retries: Number of retry attempts
            
        Returns:
            Dictionary with page information or error details
        """
        logger.info(f"Getting page info for: {title}")
        
        attempt = 0
        while attempt < retries:
            try:
                # Try with exact title match
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                except wikipedia.DisambiguationError as e:
                    logger.info(f"Disambiguation error for '{title}'. Returning options.")
                    return {
                        'error': 'Disambiguation Error',
                        'options': e.options[:15],
                        'message': 'Multiple matches found. Please be more specific.'
                    }
                except wikipedia.PageError:
                    logger.info(f"Exact page '{title}' not found. Trying with auto-suggest.")
                    try:
                        page = wikipedia.page(title)
                    except Exception as inner_e:
                        logger.error(f"Page retrieval error: {str(inner_e)}")
                        return {
                            'error': 'Page Error',
                            'message': f"Page '{title}' does not exist."
                        }
                
                # Create page info dictionary
                page_info = {
                    'title': page.title,
                    'url': page.url,
                    'content': page.content,
                    'summary': page.summary,
                    'references': page.references,
                    'categories': page.categories,
                    'links': page.links,
                    'images': page.images,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Successfully retrieved page info for: {title}")
                return page_info
                
            except ConnectionError as e:
                attempt += 1
                wait_time = 2 ** attempt
                logger.warning(f"Connection error (attempt {attempt}/{retries}): {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error getting page info: {str(e)}")
                return {
                    'error': 'General Error',
                    'message': f'An error occurred: {str(e)}'
                }
        
        return {
            'error': 'Connection Error',
            'message': 'Failed to connect to Wikipedia after multiple attempts. Please check your internet connection.'
        }


# Create service instance
wikipedia_service = WikipediaService()

