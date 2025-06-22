"""
Website screenshot tool using Firecrawl service
"""

from typing import Any, Dict, Optional
from src.tools.base import BaseTool, ToolResult
from src.services import get_firecrawl_service


class TakeScreenshotTool(BaseTool):
    """Take screenshots of websites powered by Firecrawl"""
    
    @property
    def name(self) -> str:
        return "take_screenshot"
    
    @property
    def description(self) -> str:
        return "Take a screenshot of any website, with optional browser actions before capture"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to screenshot",
                    "format": "uri"
                },
                "actions": {
                    "type": "array",
                    "description": "Browser automation actions to perform before taking screenshot. Execute in sequence to interact with dynamic content, fill forms, navigate, etc.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["wait", "click", "write", "press", "scroll"],
                                "description": "Action type: 'wait' (pause), 'click' (click element), 'write' (type text), 'press' (keyboard key), 'scroll' (scroll page)"
                            },
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for target element. Required for 'click' and 'write' actions. Examples: '#button-id', '.class-name', 'input[type=\"text\"]', 'button:contains(\"Submit\")"
                            },
                            "text": {
                                "type": "string", 
                                "description": "Text to type into the element. Required for 'write' action. Example: 'search query' or 'username@example.com'"
                            },
                            "key": {
                                "type": "string",
                                "description": "Keyboard key to press. Required for 'press' action. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', 'Space'"
                            },
                            "milliseconds": {
                                "type": "integer",
                                "description": "Time to wait in milliseconds. Required for 'wait' action. Recommended: 1000-5000ms for content loading, 500-1000ms between interactions",
                                "minimum": 100,
                                "maximum": 30000
                            }
                        },
                        "required": ["type"],
                        "examples": [
                            {
                                "description": "Wait for page to load",
                                "value": {"type": "wait", "milliseconds": 3000}
                            },
                            {
                                "description": "Click a button",
                                "value": {"type": "click", "selector": "#submit-btn"}
                            },
                            {
                                "description": "Fill a search box",
                                "value": {"type": "write", "selector": "input[name='search']", "text": "firecrawl"}
                            },
                            {
                                "description": "Press Enter key",
                                "value": {"type": "press", "key": "Enter"}
                            },
                            {
                                "description": "Scroll down the page",
                                "value": {"type": "scroll"}
                            }
                        ]
                    },
                    "examples": [
                        {
                            "description": "Take screenshot after searching",
                            "value": [
                                {"type": "wait", "milliseconds": 2000},
                                {"type": "click", "selector": "#search-input"},
                                {"type": "write", "selector": "#search-input", "text": "firecrawl screenshot"},
                                {"type": "press", "key": "Enter"},
                                {"type": "wait", "milliseconds": 3000}
                            ]
                        },
                        {
                            "description": "Navigate menu and take screenshot",
                            "value": [
                                {"type": "click", "selector": ".menu-toggle"},
                                {"type": "wait", "milliseconds": 1000},
                                {"type": "click", "selector": "a[href='/products']"},
                                {"type": "wait", "milliseconds": 2000}
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
        """Execute the screenshot tool"""
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
            # Extract parameters
            actions = arguments.get("actions", [])
            
            # Add default wait for JavaScript-heavy sites if no actions specified
            if not actions:
                actions = [{"type": "wait", "milliseconds": 500}]
            
            # Take screenshot
            result = await firecrawl.take_screenshot(
                url=url,
                actions=actions
            )
            
            # Check if screenshot was successful
            if not result.get("success"):
                return ToolResult.error("Failed to take screenshot")
            
            screenshot_data = result.get("screenshot")
            if not screenshot_data:
                return ToolResult.error("No screenshot data returned")
            
            # Return as file reference with the screenshot URL/data
            return ToolResult.file(
                uri=screenshot_data,  # This should be a base64 data URL or image URL
                mime_type="image/png",
                description=f"Screenshot of {url}"
            )
            
        except Exception as e:
            return ToolResult.error(f"Screenshot failed: {str(e)}")