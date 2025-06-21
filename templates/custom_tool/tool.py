"""
Template for creating custom MCP tools

This template provides a starting point for implementing custom tools.
Replace TOOL_NAME with your actual tool name and implement the execute method.
"""

from typing import Dict, Any, Optional
from src.tools.base import BaseTool
from src.tools.types import ToolResult

# Using existing mcpeasy dependencies
import requests  # Already available in mcpeasy
import logging   # Standard library

# Using custom dependencies (add these to requirements.txt)
try:
    import stripe  # Custom dependency - add "stripe==5.4.0" to requirements.txt
except ImportError:
    stripe = None  # Graceful fallback if dependency not installed


class TOOL_NAMETool(BaseTool):
    """
    Custom tool template - replace with your tool description
    
    This tool demonstrates how to:
    - Use existing mcpeasy dependencies
    - Implement configuration schema (optional)
    - Handle tool execution with proper error handling
    - Return structured results
    """
    
    @property
    def name(self) -> str:
        return "TOOL_NAME"  # Replace with your tool name (no spaces, lowercase)
    
    @property
    def description(self) -> str:
        return "Description of what your tool does"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_text": {
                    "type": "string",
                    "description": "Text input for the tool"
                }
            },
            "required": ["input_text"]
        }
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        """
        Define the configuration schema for this tool.
        Return None if no configuration is needed.
        """
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "API key for external service (if needed)"
                },
                "base_url": {
                    "type": "string", 
                    "description": "Base URL for API calls",
                    "default": "https://api.example.com"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                }
            },
            "required": ["api_key"]  # Mark required fields
        }
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """
        Validate tool arguments before execution.
        Override this method to add custom validation logic.
        """
        # Example validation
        required_args = ["input_text"]  # Replace with your required arguments
        
        for arg in required_args:
            if arg not in arguments:
                return False
        
        # Add more validation as needed
        # if "email" in arguments and "@" not in arguments["email"]:
        #     return False
        
        return True
    
    async def execute(self, arguments: Dict[str, Any], config: Dict[str, Any] = None) -> ToolResult:
        """
        Execute the tool with given arguments and configuration.
        
        Args:
            arguments: Tool input arguments (from MCP client)
            config: Tool configuration (from database, per-client)
            
        Returns:
            ToolResult: Success or error result
        """
        try:
            # Extract arguments
            input_text = arguments.get("input_text", "")
            
            # Extract configuration (if provided)
            if config:
                api_key = config.get("api_key")
                base_url = config.get("base_url", "https://api.example.com")
                timeout = config.get("timeout", 30)
            else:
                # Handle case where no configuration is provided
                return ToolResult.error("Tool configuration is required")
            
            # TODO: Implement your tool logic here
            # Examples:
            
            # 1. Using existing mcpeasy dependency (requests)
            response = requests.get(
                f"{base_url}/endpoint",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout
            )
            response.raise_for_status()
            api_result = response.json()
            
            # 2. Using custom dependency (stripe)
            if stripe and api_key:
                stripe.api_key = api_key
                try:
                    # Example: Create a payment intent
                    payment_intent = stripe.PaymentIntent.create(
                        amount=1000,
                        currency='usd',
                        metadata={'input': input_text}
                    )
                    result = f"Payment intent created: {payment_intent.id}"
                except stripe.error.StripeError as e:
                    result = f"Stripe error: {str(e)}"
            else:
                result = f"Processed with API: {api_result.get('message', input_text.upper())}"
            
            # 3. Database query (using existing database connection)
            # if hasattr(self, '_context') and 'db' in self._context:
            #     db = self._context['db']
            #     async with db.get_session() as session:
            #         # Your database query here
            #         pass
            
            # Return structured JSON result (recommended for LLM processing)
            return ToolResult.json({
                "status": "success",
                "result": result,
                "input": input_text,
                "api_response": api_result
            })
            
            # Alternative: Return plain text result
            # return ToolResult.text(result)
            
        except Exception as e:
            # Log error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in {self.name}: {e}")
            
            # Return user-friendly error
            return ToolResult.error(f"Tool execution failed: {str(e)}")