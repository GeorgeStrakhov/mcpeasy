"""
Resource registry for dynamic resource discovery and management
"""

import logging
import importlib
import pkgutil
import yaml
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
        self._deployment_config: Optional[Dict[str, Any]] = None
    
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
    
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration from YAML file"""
        if self._deployment_config is not None:
            return self._deployment_config
            
        # Determine config file path based on environment
        env = os.getenv("DEPLOYMENT_ENV", "default")
        config_file = f"config/deployment.{env}.yaml" if env != "default" else "config/deployment.yaml"
        config_path = Path(config_file)
        
        if not config_path.exists():
            logger.warning(f"Deployment config {config_path} not found, using default")
            config_path = Path("config/deployment.yaml")
        
        if not config_path.exists():
            logger.warning("No deployment config found, allowing all resources")
            return {"core_resources": [], "custom_resources": []}
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self._deployment_config = config.get('deployment', {})
                logger.info(f"Loaded deployment config: {self._deployment_config.get('name', 'unknown')}")
                return self._deployment_config
        except Exception as e:
            logger.error(f"Error loading deployment config: {e}")
            return {"core_resources": [], "custom_resources": []}
    
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
        """Discover and register resources from core and custom directories"""
        try:
            # Load deployment configuration
            config = self._load_deployment_config()
            
            # Discover core resources
            core_resources = self._discover_core_resources(resources_package)
            
            # Discover custom resources
            custom_resources = self._discover_custom_resources("src/custom_resources")
            
            # Filter by deployment configuration
            all_discovered_resources = core_resources + custom_resources
            allowed_core_resources = config.get('core_resources', [])
            allowed_custom_resources = config.get('custom_resources', [])
            
            # Register filtered resources
            registered_count = 0
            for resource_class, resource_name in all_discovered_resources:
                # Check if resource is allowed in deployment
                if (resource_name in allowed_core_resources or 
                    any(resource_name == custom_resource for custom_resource in allowed_custom_resources)):
                    # For custom resources, register with the full org/resource_name
                    if "/" in resource_name:  # Custom resource
                        self.register_resource(resource_class, custom_name=resource_name)
                    else:  # Core resource
                        self.register_resource(resource_class)
                    registered_count += 1
                    logger.debug(f"Registered resource: {resource_name}")
                else:
                    logger.debug(f"Skipped resource not in deployment config: {resource_name}")
            
            logger.info(f"Registered {registered_count} resources from {len(all_discovered_resources)} discovered")
                    
        except Exception as e:
            logger.error(f"Error discovering resources: {e}")

    def _discover_core_resources(self, resources_package: str) -> List[tuple]:
        """Discover resources from the core resources package"""
        discovered_resources = []
        try:
            # Import the resources package
            package = importlib.import_module(resources_package)
            package_path = Path(package.__file__).parent
            
            # Walk through all subdirectories in the resources package
            for subdir in package_path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith("__"):
                    resource_class = self._discover_resource_in_directory(resources_package, subdir.name)
                    if resource_class:
                        discovered_resources.append((resource_class, subdir.name))
            
            logger.debug(f"Discovered {len(discovered_resources)} core resources")
            return discovered_resources
                    
        except Exception as e:
            logger.error(f"Error discovering core resources: {e}")
            return []

    def _discover_custom_resources(self, base_path: str) -> List[tuple]:
        """Discover resources from custom resources directories (submodules)"""
        discovered_resources = []
        
        custom_resources_path = Path(base_path)
        if not custom_resources_path.exists():
            logger.debug("Custom resources directory does not exist")
            return []
        
        try:
            # Scan each organization's submodule
            for org_dir in custom_resources_path.iterdir():
                if org_dir.is_dir() and not org_dir.name.startswith('.') and org_dir.name != "__pycache__":
                    # Look for resources directory within the organization
                    resources_dir = org_dir / "resources"
                    if resources_dir.exists():
                        for resource_dir in resources_dir.iterdir():
                            if resource_dir.is_dir() and not resource_dir.name.startswith('.'):
                                resource_name = f"{org_dir.name}/{resource_dir.name}"
                                resource_class = self._discover_custom_resource_in_directory(base_path, org_dir.name, resource_dir.name)
                                if resource_class:
                                    discovered_resources.append((resource_class, resource_name))
            
            logger.debug(f"Discovered {len(discovered_resources)} custom resources")
            return discovered_resources
            
        except Exception as e:
            logger.error(f"Error discovering custom resources: {e}")
            return []
    
    def _discover_resource_in_directory(self, base_package: str, resource_dir: str) -> Optional[Type[BaseResource]]:
        """Discover a resource in a specific core directory"""
        try:
            # Try to import the resource module
            resource_module_name = f"{base_package}.{resource_dir}.resource"
            resource_module = importlib.import_module(resource_module_name)
            
            # Look for classes that inherit from BaseResource
            for attr_name in dir(resource_module):
                attr = getattr(resource_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and
                    any(base.__name__ == 'BaseResource' for base in attr.__mro__) and
                    attr.__name__ != 'BaseResource'):
                    return attr
            return None
                    
        except ImportError:
            logger.debug(f"Could not import resource from {resource_dir}")
            return None
        except Exception as e:
            logger.error(f"Error discovering resource in {resource_dir}: {e}")
            return None

    def _discover_custom_resource_in_directory(self, base_path: str, org_name: str, resource_name: str) -> Optional[Type[BaseResource]]:
        """Discover a custom resource in a specific organization/resource directory"""
        try:
            # Construct module path for custom resource
            # e.g., src.custom_resources.acme.resources.product_catalog.resource
            resource_module_name = f"{base_path.replace('/', '.')}.{org_name}.resources.{resource_name}.resource"
            resource_module = importlib.import_module(resource_module_name)
            
            # Look for classes that inherit from BaseResource
            for attr_name in dir(resource_module):
                attr = getattr(resource_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and
                    any(base.__name__ == 'BaseResource' for base in attr.__mro__) and
                    attr.__name__ != 'BaseResource'):
                    return attr
            return None
                    
        except ImportError as e:
            logger.debug(f"Could not import custom resource {org_name}/{resource_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error discovering custom resource {org_name}/{resource_name}: {e}")
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