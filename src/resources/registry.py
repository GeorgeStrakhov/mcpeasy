"""
Resource registry for dynamic resource discovery and management
"""

import logging
import importlib
import os
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .base import BaseResource, ResourceSchema
from .types import MCPResource, ResourceContent
from ..database import DatabaseService

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """Registry for managing and discovering MCP resources"""
    
    def __init__(self):
        self._resources: Dict[str, BaseResource] = {}
        self._resource_classes: Dict[str, Type[BaseResource]] = {}
        self._db: Optional[DatabaseService] = None
    
    def set_database(self, db: DatabaseService) -> None:
        """Set the database service and propagate to resources that need it"""
        self._db = db
        
        # Propagate database to resources that need it
        for resource in self._resources.values():
            if hasattr(resource, 'set_database'):
                resource.set_database(db)
        
        logger.info(f"Database set for resource registry with {len(self._resources)} resources")
    
    def initialize(self, db: DatabaseService) -> None:
        """Initialize the registry with database and discover resources"""
        # Set database
        self.set_database(db)
        
        # Discover resources
        self.discover_resources()
        
        logger.info(f"Resource registry initialized with resources: {list(self._resources.keys())}")
    
    def register_resource(self, resource_class: Type[BaseResource], custom_name: str = None) -> None:
        """Register a resource class with optional custom name for namespacing"""
        resource_instance = resource_class()
        resource_name = custom_name if custom_name else resource_instance.name
        
        if resource_name in self._resources:
            logger.warning(f"Resource '{resource_name}' already registered, overwriting")
        
        # Set database if available
        if self._db and hasattr(resource_instance, 'set_database'):
            resource_instance.set_database(self._db)
        
        self._resources[resource_name] = resource_instance
        self._resource_classes[resource_name] = resource_class
    
    def get_resource(self, name: str) -> Optional[BaseResource]:
        """Get a resource by name"""
        return self._resources.get(name)
    
    def get_resource_by_uri(self, uri: str) -> Optional[BaseResource]:
        """Get a resource that can handle the given URI"""
        for resource in self._resources.values():
            if resource.validate_uri(uri):
                return resource
        return None
    
    def _get_enabled_resources(self) -> List[str]:
        """Get list of enabled resources from RESOURCES environment variable"""
        resources_env = os.getenv("RESOURCES", "")
        if not resources_env:
            logger.warning("No RESOURCES environment variable set, no resources will be enabled")
            return []
        
        # Check for special __all__ value to enable all discovered resources
        if resources_env.strip() == "__all__":
            logger.info("RESOURCES=__all__ detected, discovering all available resources")
            return self._discover_all_available_resources()
        
        # Split by comma and strip whitespace
        resources = [r.strip() for r in resources_env.split(",") if r.strip()]
        logger.info(f"Enabled resources from environment: {resources}")
        return resources

    def _discover_all_available_resources(self, resources_package: str = "src.resources") -> List[str]:
        """Discover all available resources by scanning the filesystem"""
        available_resources = []
        
        # Get the resources directory path
        resources_path = Path(resources_package.replace(".", "/"))
        if not resources_path.exists():
            logger.warning(f"Resources directory {resources_path} does not exist")
            return []
        
        # First, check for simple resources in the root directory
        for resource_dir in resources_path.iterdir():
            if not resource_dir.is_dir() or resource_dir.name.startswith("_"):
                continue
                
            # Check if this is a namespace directory or a resource directory
            resource_file = resource_dir / "resource.py"
            if resource_file.exists():
                # Simple resource (e.g., "knowledge")
                available_resources.append(resource_dir.name)
                logger.debug(f"Found available resource: {resource_dir.name}")
            else:
                # This might be a namespace directory, scan it
                namespace = resource_dir.name
                for namespaced_resource_dir in resource_dir.iterdir():
                    if not namespaced_resource_dir.is_dir() or namespaced_resource_dir.name.startswith("_"):
                        continue
                        
                    resource_name = namespaced_resource_dir.name
                    
                    # Check if resource.py exists
                    resource_file = namespaced_resource_dir / "resource.py"
                    if resource_file.exists():
                        full_resource_name = f"{namespace}/{resource_name}"
                        available_resources.append(full_resource_name)
                        logger.debug(f"Found available resource: {full_resource_name}")
        
        logger.info(f"Discovered {len(available_resources)} available resources: {available_resources}")
        return available_resources
    
    async def list_resources(self, enabled_resources: List[str] = None, resource_configs: Dict[str, Dict[str, Any]] = None) -> List[MCPResource]:
        """List available resources, optionally filtered by enabled_resources"""
        if enabled_resources is None:
            enabled_resources = list(self._resources.keys())
        
        if resource_configs is None:
            resource_configs = {}
        
        all_resources = []
        for resource_name in enabled_resources:
            if resource_name in self._resources:
                resource = self._resources[resource_name]
                config = resource_configs.get(resource_name, {})
                try:
                    resources = await resource.list_resources(config)
                    all_resources.extend(resources)
                except Exception as e:
                    logger.error(f"Error listing resources for '{resource_name}': {e}")
            else:
                logger.warning(f"Enabled resource '{resource_name}' not found in registry")
        
        return all_resources
    
    def discover_resources(self, resources_package: str = "src.resources") -> None:
        """Discover and register resources based on RESOURCES environment variable"""
        try:
            # Get enabled resources from environment
            enabled_resources = self._get_enabled_resources()
            if not enabled_resources:
                logger.warning("No resources enabled in RESOURCES environment variable")
                return
            
            # Discover and register each enabled resource
            registered_count = 0
            for resource_name in enabled_resources:
                resource_class = self._discover_resource(resources_package, resource_name)
                if resource_class:
                    # Always register with the exact resource name (simple or namespaced)
                    self.register_resource(resource_class, custom_name=resource_name)
                    registered_count += 1
                    logger.debug(f"Registered resource: {resource_name}")
                else:
                    logger.warning(f"Resource '{resource_name}' not found")
            
            logger.info(f"Registered {registered_count} resources from {len(enabled_resources)} requested")
                    
        except Exception as e:
            logger.error(f"Error discovering resources: {e}")

    def _discover_resource(self, base_package: str, resource_name: str) -> Optional[Type[BaseResource]]:
        """Discover a resource by name (handles both simple and namespaced names)"""
        try:
            if "/" in resource_name:
                # Namespaced resource (e.g., "acme/product_catalog")
                namespace, resource = resource_name.split("/", 1)
                # Construct module path: src.resources.acme.product_catalog.resource
                resource_module_name = f"{base_package}.{namespace}.{resource}.resource"
            else:
                # Simple resource (e.g., "knowledge")
                # Construct module path: src.resources.knowledge.resource
                resource_module_name = f"{base_package}.{resource_name}.resource"
            
            resource_module = importlib.import_module(resource_module_name)
            
            # Look for classes that inherit from BaseResource
            for attr_name in dir(resource_module):
                attr = getattr(resource_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and
                    any(base.__name__ == 'BaseResource' for base in attr.__mro__) and
                    attr.__name__ != 'BaseResource'):
                    return attr
            
            logger.warning(f"No BaseResource subclass found in {resource_module_name}")
            return None
                    
        except ImportError as e:
            logger.debug(f"Could not import resource {resource_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error discovering resource {resource_name}: {e}")
            return None
    
    async def read_resource(self, uri: str, enabled_resources: List[str] = None, resource_configs: Dict[str, Dict[str, Any]] = None) -> Optional[ResourceContent]:
        """Read resource content with enabled resources filtering"""
        if enabled_resources is None:
            enabled_resources = list(self._resources.keys())
        
        if resource_configs is None:
            resource_configs = {}
        
        # Find resource that can handle this URI
        resource = self.get_resource_by_uri(uri)
        if not resource:
            logger.warning(f"No resource found for URI: {uri}")
            return None
        
        # Check if this resource is enabled for the client
        if resource.name not in enabled_resources:
            logger.warning(f"Resource '{resource.name}' not enabled for this client")
            return None
        
        # Get client-specific configuration
        config = resource_configs.get(resource.name, {})
        
        try:
            return await resource.read_resource(uri, config)
        except Exception as e:
            logger.error(f"Error reading resource '{resource.name}' for URI {uri}: {e}")
            return None
    
    def get_resource_config_schemas(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get configuration schemas for all registered resources"""
        schemas = {}
        for resource_name, resource in self._resources.items():
            resource_class = self._resource_classes[resource_name]
            schemas[resource_name] = resource_class.get_config_schema()
        return schemas
    
    def get_resource_config_schema(self, resource_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration schema for a specific resource"""
        if resource_name not in self._resource_classes:
            return None
        
        resource_class = self._resource_classes[resource_name]
        return resource_class.get_config_schema()


# Global registry instance
resource_registry = ResourceRegistry()