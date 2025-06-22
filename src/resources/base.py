"""
Base classes for modular MCP resources using Pydantic
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
import csv
import json
import logging
from pathlib import Path
import aiohttp
import asyncio

from .types import MCPResource, ResourceContent

logger = logging.getLogger(__name__)


class ResourceSchema(BaseModel):
    """Pydantic model for MCP resource schema definition"""
    uri: str
    name: str
    description: str
    mime_type: Optional[str] = Field(None, alias="mimeType")
    
    class Config:
        validate_by_name = True


class BaseResource(ABC):
    """Abstract base class for all MCP resources"""
    
    # Optional seed source - can be local file path or URL
    seed_source: Optional[str] = None
    
    def __init__(self):
        self._db = None
        self._initialized = False
    
    def set_database(self, db):
        """Set database service for resources that need it"""
        self._db = db
        # Run initialization on first database set
        if not self._initialized:
            asyncio.create_task(self.initialize())
    
    async def initialize(self):
        """Initialize resource and seed if table is empty"""
        if self._initialized:
            return
            
        self._initialized = True
        
        # Check if we should seed data
        if self.seed_source and self._db:
            try:
                if await self._is_table_empty():
                    logger.info(f"Table empty for resource {self.name}, seeding from {self.seed_source}")
                    await self._seed_data()
            except Exception as e:
                logger.error(f"Failed to seed data for resource {self.name}: {e}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Resource name - must be unique"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Resource description for MCP clients"""
        pass
    
    @property
    @abstractmethod
    def uri_scheme(self) -> str:
        """URI scheme for this resource type (e.g., 'knowledge', 'files')"""
        pass
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        """Return JSON schema for resource configuration, or None if no config needed"""
        return None
    
    @classmethod
    def requires_config(cls) -> bool:
        """Check if resource requires configuration"""
        return cls.get_config_schema() is not None
    
    @abstractmethod
    async def list_resources(self, config: Optional[Dict[str, Any]] = None) -> List[MCPResource]:
        """List all available resources with optional client-specific configuration"""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str, config: Optional[Dict[str, Any]] = None) -> Optional[ResourceContent]:
        """Read resource content with optional client-specific configuration"""
        pass
    
    def validate_uri(self, uri: str) -> bool:
        """Validate if this resource can handle the given URI"""
        return uri.startswith(f"{self.uri_scheme}://")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against the config schema (basic validation)"""
        schema = self.get_config_schema()
        if not schema:
            return True  # No config needed
        
        # Basic validation - could be enhanced with jsonschema
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in config:
                return False
        
        # Check field types (basic)
        for field, value in config.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False
        
        return True
    
    async def _get_model_class(self):
        """Get the SQLAlchemy model class for this resource.
        Subclasses should override this to return their model class.
        """
        return None
    
    async def _is_table_empty(self) -> bool:
        """Check if the resource's table is empty"""
        model_class = await self._get_model_class()
        if not model_class or not self._db:
            return False
            
        try:
            async with self._db.get_session() as session:
                # Check if any records exist
                from sqlalchemy import text
                result = await session.execute(
                    text(f"SELECT EXISTS(SELECT 1 FROM {model_class.__tablename__} LIMIT 1)")
                )
                has_data = result.scalar()
                return not has_data
        except Exception as e:
            logger.debug(f"Error checking if table is empty: {e}")
            return False
    
    async def _seed_data(self):
        """Seed data from seed_source (CSV or JSON file/URL)"""
        if not self.seed_source:
            return
            
        # Fetch data
        data = await self._fetch_seed_data()
        if not data:
            return
            
        # Get model class
        model_class = await self._get_model_class()
        if not model_class:
            logger.warning(f"No model class defined for resource {self.name}")
            return
            
        # Insert data
        async with self._db.get_session() as session:
            try:
                # Create model instances
                instances = []
                for row in data:
                    # Filter out any fields that don't exist in the model and normalize case
                    model_fields = {col.name for col in model_class.__table__.columns}
                    filtered_row = {}
                    
                    for k, v in row.items():
                        # Try exact match first, then lowercase
                        if k in model_fields:
                            filtered_row[k] = v
                        elif k.lower() in model_fields:
                            filtered_row[k.lower()] = v
                    
                    instance = model_class(**filtered_row)
                    instances.append(instance)
                
                # Bulk insert
                session.add_all(instances)
                await session.commit()
                logger.info(f"Successfully seeded {len(instances)} records for resource {self.name}")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to seed data: {e}")
                raise
    
    async def _fetch_seed_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch seed data from local file or URL"""
        if self.seed_source.startswith(('http://', 'https://')):
            return await self._fetch_from_url()
        else:
            return await self._fetch_from_file()
    
    async def _fetch_from_file(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch seed data from local file"""
        # Resolve path relative to resource module
        resource_dir = Path(self.__module__.replace('.', '/')).parent
        file_path = resource_dir / self.seed_source
        
        if not file_path.exists():
            logger.warning(f"Seed file not found: {file_path}")
            return None
            
        if file_path.suffix.lower() == '.csv':
            return self._parse_csv(file_path.read_text())
        elif file_path.suffix.lower() == '.json':
            return json.loads(file_path.read_text())
        else:
            logger.warning(f"Unsupported seed file format: {file_path.suffix}")
            return None
    
    async def _fetch_from_url(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch seed data from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.seed_source) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch seed data from {self.seed_source}: {response.status}")
                        return None
                        
                    content = await response.text()
                    
                    # Determine format from URL or content-type
                    if self.seed_source.endswith('.csv') or 'csv' in response.content_type:
                        return self._parse_csv(content)
                    elif self.seed_source.endswith('.json') or 'json' in response.content_type:
                        return json.loads(content)
                    else:
                        logger.warning(f"Cannot determine format for URL: {self.seed_source}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch seed data from URL: {e}")
            return None
    
    def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV content into list of dictionaries"""
        rows = []
        reader = csv.DictReader(content.strip().splitlines())
        for row in reader:
            # Convert empty strings to None
            cleaned_row = {k: (v if v != '' else None) for k, v in row.items()}
            
            # Skip rows that have None values for required fields
            # (This is a simple check - could be enhanced with schema validation)
            if any(v is None for v in cleaned_row.values()):
                logger.debug(f"Skipping CSV row with empty fields: {cleaned_row}")
                continue
                
            rows.append(cleaned_row)
        return rows