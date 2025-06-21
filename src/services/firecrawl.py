"""
Firecrawl service for web scraping and crawling
"""

import os
from typing import Any, Dict, List, Optional

try:
    from firecrawl import AsyncFirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False


class FirecrawlService:
    """Service for interacting with Firecrawl API"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not FIRECRAWL_AVAILABLE:
            raise ImportError("Firecrawl library not available. Install with: pip install firecrawl-py")
        
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key is required")
        
        self._client = AsyncFirecrawlApp(api_key=self.api_key)
    
    async def scrape_url(
        self, 
        url: str,
        formats: Optional[List[str]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        agent: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scrape a single URL using Firecrawl
        
        Args:
            url: URL to scrape
            formats: List of formats to return (markdown, html, rawHtml, links, screenshot)
            actions: Browser actions to perform before scraping
            agent: Agent configuration for FIRE-1 browsing
            
        Returns:
            Dictionary with scraped data
        """
        params = {}
        
        # Set formats - keep it simple
        if formats:
            params["formats"] = formats
        
        # Browser actions
        if actions:
            params["actions"] = actions

        if agent:
            params["agent"] = agent
        
        # Perform scraping
        result = await self._client.scrape_url(url, **params)
        
        # Extract data from ScrapeResponse object
        response_data = {
            "success": getattr(result, 'success', True),
            "url": url
        }
        
        # Add available data
        if hasattr(result, 'markdown'):
            response_data["markdown"] = result.markdown
        if hasattr(result, 'html'):
            response_data["html"] = result.html
        if hasattr(result, 'rawHtml'):
            response_data["rawHtml"] = result.rawHtml
        if hasattr(result, 'links'):
            response_data["links"] = result.links
        if hasattr(result, 'screenshot'):
            response_data["screenshot"] = result.screenshot
        if hasattr(result, 'metadata'):
            response_data["metadata"] = result.metadata
        if hasattr(result, 'extract'):
            response_data["extract"] = result.extract
        
        return response_data
    
    async def take_screenshot(
        self,
        url: str,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Take a screenshot of a URL using Firecrawl
        
        Args:
            url: URL to screenshot
            actions: Browser actions to perform before taking screenshot
            
        Returns:
            Dictionary with screenshot data and URL
        """
        params = {
            "formats": ["screenshot"]
        }
        
        # Browser actions
        if actions:
            params["actions"] = actions
        
        # Perform scraping for screenshot
        result = await self._client.scrape_url(url, **params)
        
        # Extract screenshot data
        response_data = {
            "success": getattr(result, 'success', True),
            "url": url,
            "screenshot": getattr(result, 'screenshot', None)
        }
        
        return response_data
    
    ### NB!!! this is broken for now because async version of firecrawl client is not yet supporting agent. it will, so let's wait.
    async def browse_with_agent(
        self,
        url: str,
        instructions: str,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Use FIRE-1 AI agent to browse and interact with websites
        
        Args:
            url: Starting URL to browse
            instructions: Detailed instructions for the agent on what to do
            formats: List of formats to return (markdown, html, etc.)
            
        Returns:
            Dictionary with browsing results
        """
        # Set default formats
        formats = formats or ["markdown"]

        print(f"Scraping URL: {url} with instructions: {instructions}")
        print(f"Formats: {formats}")
        print(f"Instructions: {instructions}")
        
        # Use the service's own scrape_url method with agent
        result = await self.scrape_url(
            url,
            formats=formats,
            agent={
                'model': 'FIRE-1',
                'prompt': instructions
            }
        )
        
        # Add instructions to the response
        result["instructions"] = instructions
        return result
    
    async def crawl_url(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        limit: int = 10,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        allow_backward_links: bool = False,
        allow_external_links: bool = False,
        delay: Optional[int] = None,
        only_main_content: bool = True,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Crawl a website using Firecrawl
        
        Args:
            url: Starting URL to crawl
            formats: List of formats to return for each page
            limit: Maximum number of pages to crawl
            include_paths: Regex patterns for URLs to include
            exclude_paths: Regex patterns for URLs to exclude
            max_depth: Maximum crawl depth
            allow_backward_links: Whether to allow crawling backward links
            allow_external_links: Whether to allow crawling external links
            delay: Delay between requests in milliseconds
            only_main_content: Whether to extract only main content
            include_tags: HTML tags/classes/ids to include
            exclude_tags: HTML tags/classes/ids to exclude
            headers: HTTP headers to send
            
        Returns:
            Dictionary with crawled data
        """
        params = {
            "limit": limit
        }
        
        # Set formats
        if formats:
            params["formats"] = formats
        else:
            params["formats"] = ["markdown"]
        
        # Crawl options
        if include_paths:
            params["includePaths"] = include_paths
        if exclude_paths:
            params["excludePaths"] = exclude_paths
        if max_depth is not None:
            params["maxDepth"] = max_depth
        if allow_backward_links:
            params["allowBackwardLinks"] = allow_backward_links
        if allow_external_links:
            params["allowExternalLinks"] = allow_external_links
        if delay is not None:
            params["delay"] = delay
        
        # Content selection
        params["onlyMainContent"] = only_main_content
        
        # Tag filtering
        if include_tags:
            params["includeTags"] = include_tags
        if exclude_tags:
            params["excludeTags"] = exclude_tags
        
        # Headers
        if headers:
            params["headers"] = headers
        
        # Perform crawling
        result = await self._client.crawl_url(url, **params)
        
        # Extract data from CrawlResponse object
        success = getattr(result, 'success', True)
        data = getattr(result, 'data', []) if hasattr(result, 'data') else []
        
        # Build response
        pages = []
        for page in data:
            page_data = {"url": page.get("url", "")}
            
            # Add available data for each page
            if "markdown" in page:
                page_data["markdown"] = page["markdown"]
            if "html" in page:
                page_data["html"] = page["html"]
            if "rawHtml" in page:
                page_data["rawHtml"] = page["rawHtml"]
            if "links" in page:
                page_data["links"] = page["links"]
            if "screenshot" in page:
                page_data["screenshot"] = page["screenshot"]
            if "metadata" in page:
                page_data["metadata"] = page["metadata"]
            if "extract" in page:
                page_data["extract"] = page["extract"]
                
            pages.append(page_data)
        
        return {
            "success": success,
            "start_url": url,
            "total_pages": len(pages),
            "crawl_limit": limit,
            "pages": pages
        }


def get_firecrawl_service(api_key: Optional[str] = None) -> Optional[FirecrawlService]:
    """
    Get a Firecrawl service instance
    
    Args:
        api_key: Optional API key. If not provided, will try to get from environment
        
    Returns:
        FirecrawlService instance or None if not available
    """
    try:
        return FirecrawlService(api_key)
    except (ImportError, ValueError):
        return None