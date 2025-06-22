"""
SQLAlchemy-based database service
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, or_, and_, cast, String
from contextlib import asynccontextmanager

from .models import Base, Admin, KnowledgeBase, Client, APIKey, ToolConfiguration, ResourceConfiguration, ToolCall, SystemPrompt

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQLAlchemy-based database service"""
    
    def __init__(self, database_url: str):
        # Ensure we're using asyncpg driver
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        
        # Handle SSL parameters for cloud databases like Neon
        engine_kwargs = {
            "echo": False,
            "pool_size": 10,  # Number of connections to maintain in the pool
            "max_overflow": 20,  # Additional connections allowed beyond pool_size
            "pool_timeout": 30,  # Timeout for getting connection from pool
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Verify connections before use
        }
        
        # If URL contains SSL parameters, configure them properly
        if "sslmode" in database_url:
            # Remove sslmode from URL and handle it in connect_args
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # Extract SSL mode
            sslmode = query_params.get('sslmode', ['prefer'])[0]
            
            # Remove sslmode from query string
            filtered_params = {k: v for k, v in query_params.items() if k != 'sslmode'}
            new_query = urllib.parse.urlencode(filtered_params, doseq=True)
            
            # Rebuild URL without sslmode
            new_parsed = parsed._replace(query=new_query)
            database_url = urllib.parse.urlunparse(new_parsed)
            
            # Configure SSL in connect_args
            if sslmode in ['require', 'verify-full', 'verify-ca']:
                engine_kwargs["connect_args"] = {"ssl": True}
        
        # Add connection pool settings following Neon best practices
        engine_kwargs.update({
            "pool_size": 1,      # Neon recommends starting with smaller pools
            "max_overflow": 9,   # Total max connections = 10 (following Neon guide)
            "pool_timeout": 30,
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Validate connections before use
            "echo": False,         # Set to True for SQL debugging
        })
        
        self.engine = create_async_engine(database_url, **engine_kwargs)
        self.async_session = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def initialize(self):
        """Initialize database - create superadmin"""
        # Create superadmin if no admins exist
        await self._create_superadmin_if_needed()

    
    async def close(self):
        """Close database engine"""
        await self.engine.dispose()
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            async with self.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.debug(f"Database health check failed: {e}")
            return False
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        async with self.async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # Admin Management Methods
    async def _create_superadmin_if_needed(self):
        """Create superadmin user if no admins exist"""
        import os
        import bcrypt
        
        try:
            async with self.get_session() as session:
                # Check if any admins exist
                result = await session.execute(select(Admin).limit(1))
                existing_admin = result.scalar_one_or_none()
                
                if existing_admin:
                    logger.debug("Admins already exist, skipping superadmin creation")
                    return
                
                # Get superadmin password from environment
                superadmin_password = os.getenv("SUPERADMIN_PASSWORD")
                if not superadmin_password:
                    logger.warning("SUPERADMIN_PASSWORD not set in environment")
                    return
                
                # Hash the password
                password_hash = bcrypt.hashpw(
                    superadmin_password.encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                # Create superadmin
                superadmin = Admin(
                    username="superadmin",
                    email="admin@localhost",  # Default email, can be changed later
                    password_hash=password_hash,
                    created_by_id=None  # No creator for superadmin
                )
                
                session.add(superadmin)
                await session.commit()
                logger.info("Created superadmin user")
                
        except Exception as e:
            logger.error(f"Error creating superadmin: {e}")
    
    # Admin Management Methods
    
    async def create_admin(self, username: str, email: str, password: str, created_by_id: int) -> Optional[Admin]:
        """Create a new admin user"""
        import bcrypt
        
        try:
            async with self.get_session() as session:
                # Hash the password
                password_hash = bcrypt.hashpw(
                    password.encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                admin = Admin(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    created_by_id=created_by_id
                )
                
                session.add(admin)
                await session.commit()
                await session.refresh(admin)
                return admin
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            return None
    
    async def get_admin_by_username(self, username: str) -> Optional[Admin]:
        """Get admin by username"""
        async with self.get_session() as session:
            stmt = select(Admin).where(Admin.username == username, Admin.is_active == True)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def verify_admin_password(self, username: str, password: str) -> Optional[Admin]:
        """Verify admin password and return admin if valid"""
        import bcrypt
        
        admin = await self.get_admin_by_username(username)
        if not admin:
            return None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
            return admin
        
        return None
    
    async def list_admins(self) -> List[Admin]:
        """List all active admins"""
        async with self.get_session() as session:
            stmt = select(Admin).where(Admin.is_active == True).order_by(Admin.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def delete_admin(self, username: str) -> bool:
        """Soft delete an admin (mark as inactive). Cannot delete superadmin."""
        if username == "superadmin":
            return False  # Cannot delete superadmin
        
        async with self.get_session() as session:
            stmt = select(Admin).where(Admin.username == username, Admin.is_active == True)
            result = await session.execute(stmt)
            admin = result.scalar_one_or_none()
            
            if not admin:
                return False
            
            admin.is_active = False
            await session.commit()
            return True
    
    async def change_admin_password(self, username: str, new_password: str) -> bool:
        """Change admin password"""
        import bcrypt
        
        async with self.get_session() as session:
            stmt = select(Admin).where(Admin.username == username, Admin.is_active == True)
            result = await session.execute(stmt)
            admin = result.scalar_one_or_none()
            
            if not admin:
                return False
            
            # Hash the new password
            password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            admin.password_hash = password_hash
            await session.commit()
            return True
    
    # Knowledge Base Methods
    
    async def get_knowledge_article(self, article_id: int) -> Optional[KnowledgeBase]:
        """Get a specific knowledge base article"""
        try:
            async with self.get_session() as session:
                stmt = select(KnowledgeBase).where(KnowledgeBase.id == article_id)
                result = await session.execute(stmt)
                article = result.scalar_one_or_none()
                logger.debug(f"Database query for article {article_id}: {'found' if article else 'not found'}")
                return article
        except Exception as e:
            logger.error(f"Error getting knowledge article {article_id}: {e}")
            return None
    
    async def get_knowledge_by_category(self, category: str) -> List[KnowledgeBase]:
        """Get knowledge base articles by category"""
        async with self.get_session() as session:
            stmt = select(KnowledgeBase).where(KnowledgeBase.category == category)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def search_knowledge(self, query: str) -> List[KnowledgeBase]:
        """Search knowledge base articles"""
        async with self.get_session() as session:
            # Simple text search in title and content
            search_term = f"%{query}%"
            stmt = select(KnowledgeBase).where(
                (KnowledgeBase.title.ilike(search_term)) |
                (KnowledgeBase.content.ilike(search_term))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def list_knowledge_articles(self) -> List[KnowledgeBase]:
        """List all knowledge base articles"""
        async with self.get_session() as session:
            stmt = select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    # Multi-tenant Client Methods
    
    async def create_client(self, name: str, description: str = None) -> Optional[Client]:
        """Create a new client"""
        try:
            async with self.get_session() as session:
                client = Client(name=name, description=description)
                session.add(client)
                await session.commit()
                await session.refresh(client)
                return client
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            return None
    
    async def get_client(self, client_id: Union[str, uuid.UUID]) -> Optional[Client]:
        """Get client by ID"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
        
        async with self.get_session() as session:
            stmt = select(Client).where(Client.id == client_id, Client.is_active == True)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_client_by_api_key(self, api_key: str) -> Optional[Client]:
        """Get client by API key"""
        async with self.get_session() as session:
            from sqlalchemy import or_
            stmt = select(Client).join(APIKey).where(
                APIKey.key_value == api_key,
                APIKey.is_active == True,
                Client.is_active == True,
                or_(APIKey.expires_at.is_(None), APIKey.expires_at > datetime.now())
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def list_clients(self) -> List[Client]:
        """List all active clients"""
        async with self.get_session() as session:
            stmt = select(Client).where(Client.is_active == True).order_by(Client.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def update_client(self, client_id: Union[str, uuid.UUID], name: str = None, description: str = None) -> bool:
        """Update client information"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(Client).where(Client.id == client_id, Client.is_active == True)
            result = await session.execute(stmt)
            client = result.scalar_one_or_none()
            
            if not client:
                return False
            
            if name:
                client.name = name
            if description is not None:
                client.description = description
            
            await session.commit()
            return True
    
    async def delete_client(self, client_id: Union[str, uuid.UUID]) -> bool:
        """Soft delete a client (mark as inactive) and clean up related data"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        try:
            async with self.get_session() as session:
                # Get client
                stmt = select(Client).where(Client.id == client_id, Client.is_active == True)
                result = await session.execute(stmt)
                client = result.scalar_one_or_none()
                
                if not client:
                    return False
                
                # Deactivate client
                client.is_active = False
                
                # Deactivate all API keys for this client
                api_keys_stmt = select(APIKey).where(
                    APIKey.client_id == client_id,
                    APIKey.is_active == True
                )
                api_keys_result = await session.execute(api_keys_stmt)
                api_keys = api_keys_result.scalars().all()
                
                for api_key in api_keys:
                    api_key.is_active = False
                
                # Delete all tool configurations for this client
                tool_configs_stmt = select(ToolConfiguration).where(
                    ToolConfiguration.client_id == client_id
                )
                tool_configs_result = await session.execute(tool_configs_stmt)
                tool_configs = tool_configs_result.scalars().all()
                
                for tool_config in tool_configs:
                    await session.delete(tool_config)
                
                # Delete all resource configurations for this client
                resource_configs_stmt = select(ResourceConfiguration).where(
                    ResourceConfiguration.client_id == client_id
                )
                resource_configs_result = await session.execute(resource_configs_stmt)
                resource_configs = resource_configs_result.scalars().all()
                
                for resource_config in resource_configs:
                    await session.delete(resource_config)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting client {client_id}: {e}")
            return False
    
    # API Key Methods
    
    async def create_api_key(self, client_id: Union[str, uuid.UUID], key_value: str, name: str, expires_at: Optional[datetime] = None) -> Optional[APIKey]:
        """Create a new API key for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        try:
            async with self.get_session() as session:
                api_key = APIKey(
                    client_id=client_id,
                    key_value=key_value,
                    name=name,
                    expires_at=expires_at
                )
                session.add(api_key)
                await session.commit()
                await session.refresh(api_key)
                return api_key
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return None
    
    async def get_api_key(self, key_value: str) -> Optional[APIKey]:
        """Get API key by value"""
        async with self.get_session() as session:
            from sqlalchemy import or_
            stmt = select(APIKey).where(
                APIKey.key_value == key_value, 
                APIKey.is_active == True,
                or_(APIKey.expires_at.is_(None), APIKey.expires_at > datetime.now())
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def list_api_keys_for_client(self, client_id: Union[str, uuid.UUID]) -> List[APIKey]:
        """List all active API keys for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(APIKey).where(
                APIKey.client_id == client_id,
                APIKey.is_active == True
            ).order_by(APIKey.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def delete_api_key(self, key_value: str) -> bool:
        """Soft delete an API key (mark as inactive)"""
        async with self.get_session() as session:
            stmt = select(APIKey).where(APIKey.key_value == key_value, APIKey.is_active == True)
            result = await session.execute(stmt)
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                return False
            
            api_key.is_active = False
            await session.commit()
            return True
    
    # Tool Configuration Methods
    
    async def get_tool_configurations(self, client_id: Union[str, uuid.UUID]) -> Dict[str, Dict[str, Any]]:
        """Get all tool configurations for a client as a dict"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ToolConfiguration).where(ToolConfiguration.client_id == client_id)
            result = await session.execute(stmt)
            configs = result.scalars().all()
            
            return {
                config.tool_name: config.configuration or {}
                for config in configs
            }
    
    async def set_tool_configuration(self, client_id: Union[str, uuid.UUID], tool_name: str, configuration: Optional[Dict[str, Any]]) -> bool:
        """Set tool configuration for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        try:
            async with self.get_session() as session:
                # Try to find existing configuration
                stmt = select(ToolConfiguration).where(
                    ToolConfiguration.client_id == client_id,
                    ToolConfiguration.tool_name == tool_name
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing
                    existing.configuration = configuration
                else:
                    # Create new
                    tool_config = ToolConfiguration(
                        client_id=client_id,
                        tool_name=tool_name,
                        configuration=configuration
                    )
                    session.add(tool_config)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting tool configuration: {e}")
            return False
    
    async def get_tool_configuration(self, client_id: Union[str, uuid.UUID], tool_name: str) -> Optional[Dict[str, Any]]:
        """Get specific tool configuration for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ToolConfiguration).where(
                ToolConfiguration.client_id == client_id,
                ToolConfiguration.tool_name == tool_name
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            return config.configuration if config else None
    
    async def list_tool_configurations_for_client(self, client_id: Union[str, uuid.UUID]) -> List[ToolConfiguration]:
        """List all tool configurations for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ToolConfiguration).where(
                ToolConfiguration.client_id == client_id
            ).order_by(ToolConfiguration.tool_name)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def delete_tool_configuration(self, client_id: Union[str, uuid.UUID], tool_name: str) -> bool:
        """Delete a tool configuration for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ToolConfiguration).where(
                ToolConfiguration.client_id == client_id,
                ToolConfiguration.tool_name == tool_name
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if not config:
                return False
            
            await session.delete(config)
            await session.commit()
            return True
    
    # Resource Configuration Methods
    
    async def get_resource_configurations(self, client_id: Union[str, uuid.UUID]) -> Dict[str, Dict[str, Any]]:
        """Get all resource configurations for a client as a dict"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ResourceConfiguration).where(ResourceConfiguration.client_id == client_id)
            result = await session.execute(stmt)
            configs = result.scalars().all()
            
            return {
                config.resource_name: config.configuration or {}
                for config in configs
            }
    
    async def set_resource_configuration(self, client_id: Union[str, uuid.UUID], resource_name: str, configuration: Optional[Dict[str, Any]]) -> bool:
        """Set resource configuration for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        try:
            async with self.get_session() as session:
                # Try to find existing configuration
                stmt = select(ResourceConfiguration).where(
                    ResourceConfiguration.client_id == client_id,
                    ResourceConfiguration.resource_name == resource_name
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing
                    existing.configuration = configuration
                else:
                    # Create new
                    resource_config = ResourceConfiguration(
                        client_id=client_id,
                        resource_name=resource_name,
                        configuration=configuration
                    )
                    session.add(resource_config)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting resource configuration: {e}")
            return False
    
    async def get_resource_configuration(self, client_id: Union[str, uuid.UUID], resource_name: str) -> Optional[Dict[str, Any]]:
        """Get specific resource configuration for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ResourceConfiguration).where(
                ResourceConfiguration.client_id == client_id,
                ResourceConfiguration.resource_name == resource_name
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            return config.configuration if config else None
    
    async def list_resource_configurations_for_client(self, client_id: Union[str, uuid.UUID]) -> List[ResourceConfiguration]:
        """List all resource configurations for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ResourceConfiguration).where(
                ResourceConfiguration.client_id == client_id
            ).order_by(ResourceConfiguration.resource_name)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def delete_resource_configuration(self, client_id: Union[str, uuid.UUID], resource_name: str) -> bool:
        """Delete a resource configuration for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            stmt = select(ResourceConfiguration).where(
                ResourceConfiguration.client_id == client_id,
                ResourceConfiguration.resource_name == resource_name
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if not config:
                return False
            
            await session.delete(config)
            await session.commit()
            return True
    
    # Tool Call Tracking Methods
    
    async def create_tool_call(
        self, 
        client_id: Union[str, uuid.UUID], 
        api_key_id: int,
        tool_name: str,
        input_data: Dict[str, Any],
        output_text: Optional[Dict[str, Any]] = None,
        output_json: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> Optional[ToolCall]:
        """Create a tool call record for tracking"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        try:
            async with self.get_session() as session:
                tool_call = ToolCall(
                    client_id=client_id,
                    api_key_id=api_key_id,
                    tool_name=tool_name,
                    input_data=input_data,
                    output_text=output_text,
                    output_json=output_json,
                    error_message=error_message,
                    execution_time_ms=execution_time_ms
                )
                session.add(tool_call)
                await session.commit()
                await session.refresh(tool_call)
                return tool_call
        except Exception as e:
            logger.error(f"Error creating tool call record: {e}")
            return None
    
    async def list_tool_calls(
        self,
        client_id: Optional[Union[str, uuid.UUID]] = None,
        tool_name: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "desc"
    ) -> Tuple[List[ToolCall], int]:
        """List tool calls with optional filtering, pagination and search"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            # Base query
            query = select(ToolCall)
            count_query = select(func.count(ToolCall.id))
            
            # Apply filters
            if client_id:
                query = query.where(ToolCall.client_id == client_id)
                count_query = count_query.where(ToolCall.client_id == client_id)
            
            if tool_name:
                query = query.where(ToolCall.tool_name == tool_name)
                count_query = count_query.where(ToolCall.tool_name == tool_name)
            
            if search:
                search_filter = or_(
                    ToolCall.tool_name.ilike(f"%{search}%"),
                    ToolCall.error_message.ilike(f"%{search}%"),
                    cast(ToolCall.input_data, String).ilike(f"%{search}%"),
                    cast(ToolCall.output_text, String).ilike(f"%{search}%"),
                    cast(ToolCall.output_json, String).ilike(f"%{search}%")
                )
                query = query.where(search_filter)
                count_query = count_query.where(search_filter)
            
            # Apply ordering
            if order_by == "created_at":
                order_col = ToolCall.created_at
            elif order_by == "tool_name":
                order_col = ToolCall.tool_name
            elif order_by == "execution_time_ms":
                order_col = ToolCall.execution_time_ms
            else:
                order_col = ToolCall.created_at
            
            if order_dir == "desc":
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute queries
            result = await session.execute(query)
            tool_calls = result.scalars().all()
            
            count_result = await session.execute(count_query)
            total_count = count_result.scalar()
            
            return list(tool_calls), total_count
    
    async def get_tool_call_stats(
        self,
        client_id: Optional[Union[str, uuid.UUID]] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get tool call statistics"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            # Date filter for last N days
            since_date = datetime.utcnow() - timedelta(days=days)
            
            base_filter = ToolCall.created_at >= since_date
            if client_id:
                base_filter = and_(base_filter, ToolCall.client_id == client_id)
            
            # Total calls
            total_query = select(func.count(ToolCall.id)).where(base_filter)
            total_result = await session.execute(total_query)
            total_calls = total_result.scalar()
            
            # Successful calls
            success_query = select(func.count(ToolCall.id)).where(
                and_(base_filter, ToolCall.error_message.is_(None))
            )
            success_result = await session.execute(success_query)
            successful_calls = success_result.scalar()
            
            # Failed calls
            failed_calls = total_calls - successful_calls
            
            # Average execution time
            avg_time_query = select(func.avg(ToolCall.execution_time_ms)).where(
                and_(base_filter, ToolCall.execution_time_ms.is_not(None))
            )
            avg_time_result = await session.execute(avg_time_query)
            avg_execution_time = avg_time_result.scalar()
            
            # Top tools by usage
            top_tools_query = select(
                ToolCall.tool_name,
                func.count(ToolCall.id).label('count')
            ).where(base_filter).group_by(ToolCall.tool_name).order_by(
                func.count(ToolCall.id).desc()
            ).limit(10)
            top_tools_result = await session.execute(top_tools_query)
            top_tools = [{"tool_name": row.tool_name, "count": row.count} 
                        for row in top_tools_result]
            
            return {
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                "avg_execution_time_ms": float(avg_execution_time) if avg_execution_time else None,
                "top_tools": top_tools,
                "period_days": days
            }
    
    # System Prompt Methods
    async def create_system_prompt(
        self,
        client_id: Union[str, uuid.UUID],
        prompt_text: str,
        user_requirements: str,
        generation_context: Dict[str, Any],
        parent_version_id: Optional[int] = None
    ) -> SystemPrompt:
        """Create a new system prompt version"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            # Get next version number for this client
            version_query = select(func.coalesce(func.max(SystemPrompt.version), 0) + 1).where(
                SystemPrompt.client_id == client_id
            )
            version_result = await session.execute(version_query)
            next_version = version_result.scalar()
            
            # Create new system prompt
            system_prompt = SystemPrompt(
                client_id=client_id,
                prompt_text=prompt_text,
                version=next_version,
                user_requirements=user_requirements,
                generation_context=generation_context,
                parent_version_id=parent_version_id,
                is_active=False  # Don't auto-activate, let user choose
            )
            
            session.add(system_prompt)
            await session.commit()
            await session.refresh(system_prompt)
            
            return system_prompt
    
    async def get_active_system_prompt(self, client_id: Union[str, uuid.UUID]) -> Optional[SystemPrompt]:
        """Get the active system prompt for a client"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            query = select(SystemPrompt).where(
                and_(
                    SystemPrompt.client_id == client_id,
                    SystemPrompt.is_active == True
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def get_system_prompt(self, prompt_id: int) -> Optional[SystemPrompt]:
        """Get a specific system prompt by ID"""
        async with self.get_session() as session:
            query = select(SystemPrompt).where(SystemPrompt.id == prompt_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def list_system_prompts(self, client_id: Union[str, uuid.UUID]) -> List[SystemPrompt]:
        """List all system prompts for a client, ordered by version desc"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            query = select(SystemPrompt).where(
                SystemPrompt.client_id == client_id
            ).order_by(SystemPrompt.version.desc())
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def set_active_system_prompt(self, client_id: Union[str, uuid.UUID], prompt_id: int) -> bool:
        """Set a system prompt as active (deactivating others)"""
        if isinstance(client_id, str):
            client_id = uuid.UUID(client_id)
            
        async with self.get_session() as session:
            # First, deactivate all prompts for this client
            deactivate_query = select(SystemPrompt).where(
                and_(
                    SystemPrompt.client_id == client_id,
                    SystemPrompt.is_active == True
                )
            )
            deactivate_result = await session.execute(deactivate_query)
            for prompt in deactivate_result.scalars():
                prompt.is_active = False
            
            # Then activate the specified prompt
            activate_query = select(SystemPrompt).where(
                and_(
                    SystemPrompt.id == prompt_id,
                    SystemPrompt.client_id == client_id
                )
            )
            activate_result = await session.execute(activate_query)
            prompt_to_activate = activate_result.scalar_one_or_none()
            
            if prompt_to_activate:
                prompt_to_activate.is_active = True
                await session.commit()
                return True
            
            return False