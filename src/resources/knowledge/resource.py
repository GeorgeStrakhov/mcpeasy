"""
Knowledge base resource implementation
"""
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from ...database import DatabaseService
from ..base import BaseResource
from ..types import MCPResource, ResourceContent

logger = logging.getLogger(__name__)


class KnowledgeResource(BaseResource):
    """Knowledge base resource with configurable access control"""
    
    def __init__(self, db: DatabaseService = None):
        self.db = db
    
    @property
    def name(self) -> str:
        return "knowledge"
    
    @property
    def description(self) -> str:
        return "Access to knowledge base articles and categories"
    
    @property
    def uri_scheme(self) -> str:
        return "knowledge"
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        """Configuration schema for knowledge resource"""
        return {
            "type": "object",
            "properties": {
                "allowed_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of categories this client can access (empty means all)"
                },
                "max_articles": {
                    "type": "number",
                    "description": "Maximum number of articles to return in listings",
                    "default": 100
                },
                "allow_search": {
                    "type": "boolean",
                    "description": "Allow search functionality",
                    "default": True
                },
                "excluded_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to exclude from results"
                }
            },
            "additionalProperties": False
        }
    
    async def list_resources(self, config: Optional[Dict[str, Any]] = None) -> List[MCPResource]:
        """List knowledge base resources with configuration filtering"""
        if not self.db:
            return []
        
        config = config or {}
        allowed_categories = config.get("allowed_categories", [])
        max_articles = config.get("max_articles", 100)
        excluded_tags = config.get("excluded_tags", [])
        
        try:
            articles = await self.db.list_knowledge_articles()
            resources = []
            
            # Filter articles based on configuration
            filtered_articles = []
            for article in articles:
                # Check category filter
                if allowed_categories and article.category not in allowed_categories:
                    continue
                
                # Check excluded tags
                if excluded_tags and article.tags:
                    if any(tag in excluded_tags for tag in article.tags):
                        continue
                
                filtered_articles.append(article)
            
            # Apply max articles limit
            if max_articles > 0:
                filtered_articles = filtered_articles[:max_articles]
            
            # Add individual article resources
            for article in filtered_articles:
                resources.append(MCPResource(
                    uri=f"knowledge://article/{article.id}",
                    name=f"Article: {article.title}",
                    description=f"{article.category} - {article.title}",
                    mime_type="text/plain"
                ))
            
            # Add category-based resources (filtered)
            if allowed_categories:
                # Only show allowed categories
                categories = set(allowed_categories)
            else:
                # Show all categories from filtered articles
                categories = set(article.category for article in filtered_articles if article.category)
            
            for category in categories:
                resources.append(MCPResource(
                    uri=f"knowledge://category/{category}",
                    name=f"Category: {category.title()}",
                    description=f"All articles in {category} category",
                    mime_type="text/plain"
                ))
            
            # Add search resource if enabled
            if config.get("allow_search", True):
                resources.append(MCPResource(
                    uri="knowledge://search",
                    name="Search Knowledge Base",
                    description="Search through accessible knowledge base articles",
                    mime_type="text/plain"
                ))
            
            logger.debug(f"Listed {len(resources)} knowledge base resources with config: {config}")
            return resources
            
        except Exception as e:
            logger.error(f"Error listing knowledge resources: {e}")
            return []
    
    async def read_resource(self, uri: str, config: Optional[Dict[str, Any]] = None) -> Optional[ResourceContent]:
        """Read knowledge resource content with configuration filtering"""
        if not self.db:
            return None
        
        config = config or {}
        allowed_categories = config.get("allowed_categories", [])
        excluded_tags = config.get("excluded_tags", [])
        allow_search = config.get("allow_search", True)
        
        try:
            parsed = urlparse(uri)
            if parsed.scheme != "knowledge":
                return None
            
            resource_type = parsed.netloc
            path_parts = parsed.path.strip('/').split('/') if parsed.path.strip('/') else []
            
            logger.debug(f"Reading resource URI: {uri}, type: {resource_type}, path: {path_parts}")
            
            if resource_type == "article" and len(path_parts) >= 1:
                # Individual article: knowledge://article/123
                try:
                    article_id = int(path_parts[0])
                    article = await self.db.get_knowledge_article(article_id)
                    
                    if article:
                        # Check access permissions
                        if allowed_categories and article.category not in allowed_categories:
                            logger.warning(f"Article {article_id} category '{article.category}' not allowed")
                            return None
                        
                        if excluded_tags and article.tags:
                            if any(tag in excluded_tags for tag in article.tags):
                                logger.warning(f"Article {article_id} has excluded tags")
                                return None
                        
                        content = f"Title: {article.title}\nCategory: {article.category}\nTags: {', '.join(article.tags or [])}\n\n{article.content}"
                        return ResourceContent(
                            uri=uri,
                            mime_type="text/plain",
                            text=content
                        )
                    else:
                        logger.warning(f"Article {article_id} not found")
                except ValueError:
                    logger.warning(f"Invalid article ID in URI: {uri}")
                    
            elif resource_type == "category" and len(path_parts) >= 1:
                # Category articles: knowledge://category/documentation
                category = path_parts[0]
                
                # Check if category is allowed
                if allowed_categories and category not in allowed_categories:
                    logger.warning(f"Category '{category}' not allowed for this client")
                    return None
                
                articles = await self.db.get_knowledge_by_category(category)
                
                # Filter articles by excluded tags
                if excluded_tags:
                    articles = [
                        article for article in articles
                        if not article.tags or not any(tag in excluded_tags for tag in article.tags)
                    ]
                
                if articles:
                    content_parts = [f"Articles in '{category}' category:\n"]
                    for article in articles:
                        content_parts.append(f"- {article.title}: {article.content}")
                    
                    content = "\n\n".join(content_parts)
                    return ResourceContent(
                        uri=uri,
                        mime_type="text/plain",
                        text=content
                    )
                    
            elif resource_type == "search":
                # Search: knowledge://search?q=query
                if not allow_search:
                    logger.warning("Search not allowed for this client")
                    return ResourceContent(
                        uri=uri,
                        mime_type="text/plain",
                        text="Search functionality is not enabled for this client"
                    )
                
                query_params = parse_qs(parsed.query)
                query = query_params.get('q', [''])[0]
                
                if query:
                    articles = await self.db.search_knowledge(query)
                    
                    # Apply filtering
                    filtered_articles = []
                    for article in articles:
                        # Check category filter
                        if allowed_categories and article.category not in allowed_categories:
                            continue
                        
                        # Check excluded tags
                        if excluded_tags and article.tags:
                            if any(tag in excluded_tags for tag in article.tags):
                                continue
                        
                        filtered_articles.append(article)
                    
                    if filtered_articles:
                        content_parts = [f"Search results for '{query}':\n"]
                        for article in filtered_articles:
                            content_parts.append(f"- {article.title} ({article.category}): {article.content}")
                        
                        content = "\n\n".join(content_parts)
                        return ResourceContent(
                            uri=uri,
                            mime_type="text/plain",
                            text=content
                        )
                    else:
                        return ResourceContent(
                            uri=uri,
                            mime_type="text/plain",
                            text=f"No accessible articles found for query: {query}"
                        )
                else:
                    return ResourceContent(
                        uri=uri,
                        mime_type="text/plain",
                        text="Search requires a 'q' parameter. Example: knowledge://search?q=your-query"
                    )
            
            logger.warning(f"Unknown knowledge resource URI: {uri}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading knowledge resource {uri}: {e}")
            return None
    
    def set_database(self, db: DatabaseService):
        """Set database service (for dependency injection)"""
        self.db = db