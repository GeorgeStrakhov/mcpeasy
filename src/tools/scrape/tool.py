"""
Web scraping tool using Firecrawl service
"""

from typing import Any, Dict, Optional
from ..base import BaseTool, ToolResult
from ...services import get_firecrawl_service


class ScrapeTool(BaseTool):
    """Web scraping tool powered by Firecrawl"""
    
    @property
    def name(self) -> str:
        return "scrape"
    
    @property
    def description(self) -> str:
        return "Scrape web pages and convert to clean markdown or extract structured data"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to scrape",
                    "format": "uri"
                },
                "formats": {
                    "type": "array",
                    "description": "Data formats to return",
                    "items": {
                        "type": "string",
                        "enum": ["markdown", "html", "rawHtml", "links", "screenshot"]
                    },
                    "default": ["markdown"]
                },
                "actions": {
                    "type": "array",
                    "description": "Browser automation actions to perform before scraping. Execute in sequence to interact with dynamic content, navigate through SPAs, fill forms, handle authentication, etc.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["wait", "click", "write", "press", "scroll"],
                                "description": "Action type: 'wait' (pause for loading), 'click' (click element), 'write' (type text), 'press' (keyboard key), 'scroll' (scroll page)"
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for target element. Required for 'click' and 'write' actions. Examples: '#login-btn', '.search-input', 'button[aria-label=\"Menu\"]', 'a:contains(\"Next\")"
                            },
                            "text": {
                                "type": "string", 
                                "description": "Text to type into the element. Required for 'write' action. Examples: search terms, form inputs, usernames, etc."
                            },
                            "key": {
                                "type": "string",
                                "description": "Keyboard key to press. Required for 'press' action. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', 'Space', 'PageDown'"
                            },
                            "milliseconds": {
                                "type": "integer",
                                "description": "Wait duration in milliseconds. Required for 'wait' action. Use 2000-5000ms for content loading, 500-1000ms between interactions",
                                "minimum": 100,
                                "maximum": 30000
                            }
                        },
                        "required": ["type"],
                        "examples": [
                            {
                                "description": "Wait for dynamic content to load",
                                "value": {"type": "wait", "milliseconds": 3000}
                            },
                            {
                                "description": "Click to expand content",
                                "value": {"type": "click", "selector": ".expand-button"}
                            },
                            {
                                "description": "Fill search form",
                                "value": {"type": "write", "selector": "input[placeholder='Search...']", "text": "documentation"}
                            },
                            {
                                "description": "Submit with Enter",
                                "value": {"type": "press", "key": "Enter"}
                            },
                            {
                                "description": "Scroll to load more content",
                                "value": {"type": "scroll"}
                            }
                        ]
                    },
                    "examples": [
                        {
                            "description": "Scrape search results page",
                            "value": [
                                {"type": "click", "selector": "#search-input"},
                                {"type": "write", "selector": "#search-input", "text": "API documentation"},
                                {"type": "press", "key": "Enter"},
                                {"type": "wait", "milliseconds": 3000}
                            ]
                        },
                        {
                            "description": "Navigate and scrape protected content",
                            "value": [
                                {"type": "click", "selector": ".login-link"},
                                {"type": "wait", "milliseconds": 2000},
                                {"type": "click", "selector": "#continue-as-guest"},
                                {"type": "wait", "milliseconds": 3000}
                            ]
                        }
                    ]
                }
            },
            "required": ["url"]
        }
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Configuration schema for per-client Firecrawl settings"""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Firecrawl API key (get one at https://firecrawl.dev)"
                }
            },
            "required": ["api_key"]
        }
    
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the scrape tool"""
        url = arguments.get("url")
        
        # Get API key from config or environment
        api_key = None
        if config:
            api_key = config.get("api_key")
        
        # Get Firecrawl service
        firecrawl = get_firecrawl_service(api_key)
        if not firecrawl:
            return ToolResult.error("Firecrawl service not available. Check API key and installation.")
        
        try:
            # Extract parameters - keep it simple
            formats = arguments.get("formats")
            actions = arguments.get("actions")
            
            # Perform scraping
            result = await firecrawl.scrape_url(
                url=url,
                formats=formats,
                actions=actions
            )
            
            return ToolResult.json(result)
            
        except Exception as e:
            return ToolResult.error(f"Scraping failed: {str(e)}")