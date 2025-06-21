"""
Template for creating custom MCP resources

This template provides a starting point for implementing custom resources.
Replace RESOURCE_NAME with your actual resource name and implement the methods.
"""

from typing import Dict, Any, Optional, List
from src.resources.base import BaseResource
from src.resources.types import MCPResource, ResourceContent

# Using existing mcpeasy dependencies
import requests  # Already available in mcpeasy
import logging   # Standard library

# Using custom dependencies (add these to requirements.txt)
try:
    import pandas as pd  # Custom dependency - add "pandas>=1.5.0" to requirements.txt
except ImportError:
    pd = None  # Graceful fallback if dependency not installed


class RESOURCE_NAMEResource(BaseResource):
    """
    Custom resource template - replace with your resource description
    
    This resource demonstrates how to:
    - Use existing mcpeasy dependencies
    - Implement configuration schema (optional)
    - List available resources with filtering
    - Read resource content with proper error handling
    - Handle different MIME types
    """
    
    name = "RESOURCE_NAME"  # Replace with your resource name (no spaces, lowercase)
    description = "Description of what your resource provides"
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        """
        Define the configuration schema for this resource.
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
                "max_items": {
                    "type": "integer",
                    "description": "Maximum number of items to return",
                    "default": 100
                },
                "allowed_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of allowed categories for this client"
                }
            },
            "required": ["api_key"]  # Mark required fields
        }
    
    def validate_uri(self, uri: str) -> bool:
        """
        Check if this resource can handle the given URI.
        
        Args:
            uri: Resource URI to validate
            
        Returns:
            bool: True if this resource can handle the URI
        """
        # Example: Handle URIs that start with your resource scheme
        return uri.startswith("resource_name://")  # Replace with your scheme
        
        # More examples:
        # return uri.startswith("company://products/")
        # return uri.endswith(".company-format")
        # return "your-service" in uri
    
    async def list_resources(self, config: Dict[str, Any] = None) -> List[MCPResource]:
        """
        List available resources based on configuration.
        
        Args:
            config: Resource configuration (from database, per-client)
            
        Returns:
            List[MCPResource]: List of available resources
        """
        try:
            resources = []
            
            # Extract configuration
            max_items = 100
            allowed_categories = []
            if config:
                max_items = config.get("max_items", 100)
                allowed_categories = config.get("allowed_categories", [])
            
            # TODO: Implement your resource listing logic here
            # Examples:
            
            # 1. Static list of resources
            static_resources = [
                {
                    "id": "item1",
                    "name": "Example Item 1",
                    "category": "documents",
                    "description": "First example item"
                },
                {
                    "id": "item2", 
                    "name": "Example Item 2",
                    "category": "images",
                    "description": "Second example item"
                }
            ]
            
            # 2. Fetch from API (using existing requests dependency)
            api_key = config.get("api_key") if config else None
            base_url = config.get("base_url", "https://api.example.com")
            
            if api_key:
                response = requests.get(
                    f"{base_url}/resources",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"limit": max_items}
                )
                response.raise_for_status()
                api_resources = response.json().get("items", [])
                
                # 3. Process with custom dependency (pandas)
                if pd is not None and api_resources:
                    # Example: Use pandas to process and filter data
                    df = pd.DataFrame(api_resources)
                    # Filter and sort using pandas
                    if 'priority' in df.columns:
                        df = df.sort_values('priority', ascending=False)
                    static_resources = df.to_dict('records')
                else:
                    static_resources = api_resources
            
            # 3. Query database (using existing database connection)
            # if hasattr(self, '_db') and self._db:
            #     async with self._db.get_session() as session:
            #         # Your database query here
            #         pass
            
            # Filter by allowed categories (if configured)
            if allowed_categories:
                static_resources = [
                    item for item in static_resources 
                    if item.get("category") in allowed_categories
                ]
            
            # Convert to MCPResource objects
            for item in static_resources[:max_items]:
                resources.append(MCPResource(
                    uri=f"resource_name://{item['id']}",  # Replace with your URI scheme
                    name=item["name"],
                    description=item.get("description", ""),
                    mimeType=self._get_mime_type(item)
                ))
            
            return resources
            
        except Exception as e:
            # Log error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error listing resources for {self.name}: {e}")
            
            # Return empty list on error
            return []
    
    async def read_resource(self, uri: str, config: Dict[str, Any] = None) -> ResourceContent:
        """
        Read content of a specific resource.
        
        Args:
            uri: Resource URI to read
            config: Resource configuration (from database, per-client)
            
        Returns:
            ResourceContent: Resource content and metadata
        """
        try:
            # Extract resource ID from URI
            # Example: "resource_name://item1" -> "item1"
            if not self.validate_uri(uri):
                raise ValueError(f"Invalid URI for {self.name}: {uri}")
            
            resource_id = uri.replace("resource_name://", "")  # Replace with your scheme
            
            # TODO: Implement your resource reading logic here
            # Examples:
            
            # 1. Static content
            if resource_id == "item1":
                content = "This is the content of item 1"
                mime_type = "text/plain"
            elif resource_id == "item2":
                content = '{"type": "image", "url": "https://example.com/image.jpg"}'
                mime_type = "application/json"
            else:
                raise ValueError(f"Resource not found: {resource_id}")
            
            # 2. Fetch from API (using existing requests dependency)
            # import requests
            # api_key = config.get("api_key") if config else None
            # base_url = config.get("base_url", "https://api.example.com")
            # 
            # response = requests.get(
            #     f"{base_url}/resources/{resource_id}",
            #     headers={"Authorization": f"Bearer {api_key}"}
            # )
            # response.raise_for_status()
            # 
            # content = response.text
            # mime_type = response.headers.get("content-type", "text/plain")
            
            # 3. Query database (using existing database connection)
            # if hasattr(self, '_db') and self._db:
            #     async with self._db.get_session() as session:
            #         # Your database query here
            #         result = await session.execute(...)
            #         content = result.scalar()
            
            return ResourceContent(
                uri=uri,
                mimeType=mime_type,
                text=content  # Use 'text' for text content or 'blob' for binary
            )
            
        except Exception as e:
            # Log error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error reading resource {uri} for {self.name}: {e}")
            
            # Re-raise for proper error handling
            raise
    
    def _get_mime_type(self, item: Dict[str, Any]) -> str:
        """
        Determine MIME type for a resource item.
        
        Args:
            item: Resource item data
            
        Returns:
            str: MIME type
        """
        # Implement logic to determine MIME type based on item
        category = item.get("category", "")
        
        if category == "documents":
            return "text/plain"
        elif category == "images":
            return "image/jpeg"
        elif category == "json":
            return "application/json"
        else:
            return "text/plain"  # Default