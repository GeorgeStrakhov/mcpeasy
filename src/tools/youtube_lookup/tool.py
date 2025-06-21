"""
YouTube lookup tool implementation - vector similarity search through YouTube video chunks
"""

import json
from typing import Any, Dict, Optional
from sqlalchemy import text
from ..base import BaseTool, ToolResult
from ...services.embeddings import get_embeddings_service
from ...services.openrouter import get_openrouter_service
from ...models.youtube import YouTubeChunk


class YouTubeLookupTool(BaseTool):
    """Tool for searching YouTube video chunks using vector similarity"""
    
    def __init__(self):
        self._context = {}
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set execution context including database access"""
        self._context = context
    
    @property
    def name(self) -> str:
        return "youtube_lookup"
    
    @property
    def description(self) -> str:
        return "Search YouTube video chunks from a pre-processed database of youtube video chunks using semantic similarity. Returns relevant video segments with timestamps and similarity scores."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find similar video content"
                }
            },
            "required": ["query"]
        }
    
    @classmethod
    def get_config_schema(cls) -> Optional[Dict[str, Any]]:
        return {
            "type": "object",
            "properties": {
                "project_slug": {
                    "type": "string",
                    "description": "Project identifier to restrict search scope"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "min_similarity": {
                    "type": "number",
                    "description": "Minimum similarity threshold (0.0 to 1.0)",
                    "default": 0.01,
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "enhance_query": {
                    "type": "boolean",
                    "description": "Use LLM to expand queries for better semantic matching",
                    "default": True
                },
                "hybrid_search": {
                    "type": "boolean",
                    "description": "Combine vector similarity with keyword search for better results",
                    "default": True
                },
                "keyword_weight": {
                    "type": "number",
                    "description": "Weight for keyword search vs vector search (0.0-1.0)",
                    "default": 0.5,
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "query_expansion_prompt": {
                    "type": "string",
                    "description": "Custom prompt template for query expansion. Use {query} as placeholder for the original query. If not provided, uses default prompt.",
                    "default": None
                }
            },
            "required": ["project_slug"]
        }
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute YouTube similarity search"""
        
        # Validate configuration
        if not config or "project_slug" not in config:
            return ToolResult.error("Tool configuration must include 'project_slug'")
        
        project_slug = config["project_slug"]
        max_results = int(config.get("max_results", 10))
        min_similarity = float(config.get("min_similarity", 0.01))
        enhance_query = config.get("enhance_query", True)
        hybrid_search = config.get("hybrid_search", True)
        keyword_weight = float(config.get("keyword_weight", 0.5))
        query_expansion_prompt = config.get("query_expansion_prompt")
        query = arguments.get("query", "").strip()
        
        if not query:
            return ToolResult.error("Query cannot be empty")
        
        try:
            # Get embeddings service
            embeddings_service = get_embeddings_service()
            if not embeddings_service:
                return ToolResult.error("Embeddings service not available - check CLOUDFLARE_API_KEY and CLOUDFLARE_ACCOUNT_ID")
            
            # Initialize enhanced_query to original query
            enhanced_query = query
            
            # Enhance query if enabled
            if enhance_query:
                openrouter_service = get_openrouter_service()
                if not openrouter_service:
                    return ToolResult.error("OpenRouter service not available for query enhancement - check OPENROUTER_API_KEY")
                
                # Enhance query using LLM to expand short queries into more detailed descriptions
                llm_enhanced = await self._enhance_query(query, openrouter_service, query_expansion_prompt)
                if llm_enhanced:
                    enhanced_query = llm_enhanced
            
            # Generate query embedding using enhanced query
            query_embedding = await embeddings_service.create_embedding(enhanced_query)
            if not query_embedding:
                return ToolResult.error("Failed to generate embedding for query")
            
            # Get database connection from context
            db = self._context.get('db')
            if not db:
                return ToolResult.error("Database connection not available")
            
            # Perform search (vector only or hybrid)
            # Convert embedding to string format (not JSON) as required by pgvector
            embedding_str = str(query_embedding)
            
            if hybrid_search:
                # Hybrid search: combine vector similarity with keyword search
                search_query = text("""
                    SELECT 
                        video_id,
                        title,
                        start_timestamp,
                        text,
                        1 - (embedding <=> :embedding) as vector_score,
                        ts_rank(to_tsvector('english', text || ' ' || title), plainto_tsquery('english', :original_query)) as keyword_score,
                        -- Combined score: weighted average of vector and keyword scores
                        ((1 - (embedding <=> :embedding)) * (1 - :keyword_weight)) + 
                        (ts_rank(to_tsvector('english', text || ' ' || title), plainto_tsquery('english', :original_query)) * :keyword_weight) as combined_score
                    FROM youtube_chunks
                    WHERE embedding IS NOT NULL 
                      AND project_slug = :project_slug
                      AND (
                        (1 - (embedding <=> :embedding)) >= :min_similarity OR
                        to_tsvector('english', text || ' ' || title) @@ plainto_tsquery('english', :original_query)
                      )
                    ORDER BY combined_score DESC
                    LIMIT :max_results
                """)
                
                query_params = {
                    'embedding': embedding_str,
                    'original_query': query,  # Use original query for keyword search
                    'project_slug': project_slug,
                    'max_results': max_results,
                    'min_similarity': min_similarity,
                    'keyword_weight': keyword_weight
                }
            else:
                # Vector-only search
                search_query = text("""
                    SELECT 
                        video_id,
                        title,
                        start_timestamp,
                        text,
                        1 - (embedding <=> :embedding) as vector_score,
                        0.0 as keyword_score,
                        1 - (embedding <=> :embedding) as combined_score
                    FROM youtube_chunks
                    WHERE embedding IS NOT NULL 
                      AND project_slug = :project_slug
                      AND (1 - (embedding <=> :embedding)) >= :min_similarity
                    ORDER BY combined_score DESC
                    LIMIT :max_results
                """)
                
                query_params = {
                    'embedding': embedding_str,
                    'project_slug': project_slug,
                    'max_results': max_results,
                    'min_similarity': min_similarity
                }
            
            async with db.get_session() as session:
                result = await session.execute(search_query, query_params)
                rows = result.fetchall()
            
            if not rows:
                json_response = {
                    "original_query": query,
                    "enhanced_query": enhanced_query if enhanced_query != query else None,
                    "enhancement_used": enhanced_query != query,
                    "hybrid_search": hybrid_search,
                    "keyword_weight": keyword_weight if hybrid_search else None,
                    "project_slug": project_slug,
                    "min_similarity": min_similarity,
                    "results_count": 0,
                    "results": []
                }
                return ToolResult.json(json_response)
            
            # Format results - include scores from hybrid search
            results = []
            for row in rows:
                # Debug: print row attributes to see what's available
                # print(f"Row attributes: {dir(row)}")
                # print(f"Start timestamp: {row.start_timestamp}")
                
                chunk_data = {
                    "title": row.title,
                    "vector_score": float(row.vector_score),
                    "keyword_score": float(row.keyword_score),
                    "combined_score": float(row.combined_score),
                    "youtube_url": f"https://www.youtube.com/watch?v={row.video_id}&t={int(row.start_timestamp)}s",
                    "text": row.text,
                    "start_timestamp": row.start_timestamp  # Also include raw timestamp for debugging
                }
                results.append(chunk_data)
            
            # Return structured JSON response
            json_response = {
                "original_query": query,
                "enhanced_query": enhanced_query if enhanced_query != query else None,
                "enhancement_used": enhanced_query != query,
                "hybrid_search": hybrid_search,
                "keyword_weight": keyword_weight if hybrid_search else None,
                "project_slug": project_slug,
                "min_similarity": min_similarity,
                "results_count": len(results),
                "results": results
            }
            
            return ToolResult.json(json_response)
            
        except Exception as e:
            return ToolResult.error(f"YouTube lookup failed: {str(e)}")
    
    async def _enhance_query(self, original_query: str, openrouter_service, custom_prompt: Optional[str] = None) -> Optional[str]:
        """Enhance user query by expanding it into a more detailed description using LLM"""
        try:
            if custom_prompt:
                # Use custom prompt template, replacing {query} placeholder
                enhancement_prompt = custom_prompt.format(query=original_query)
            else:
                # Use default prompt
                enhancement_prompt = f"""
You are helping to improve search quality for YouTube video content. The user will give you a short query, your job is to make it more specific and detailed to enhance the search results. Include a lot of synonyms and variations of the original query but keep true to the user's intent.

Original query: "{original_query}"

ONLY RETURN THE ENHANCED QUERY, NO OTHER TEXT.
"""

            messages = [
                {"role": "user", "content": enhancement_prompt}
            ]
            
            enhanced = await openrouter_service.completion(
                messages=messages,
                temperature=0.3,  # Some creativity but stay focused
                max_tokens=150    # Keep it concise
            )
            
            if enhanced and len(enhanced.strip()) > len(original_query):
                return enhanced.strip()
            else:
                return None
                
        except Exception as e:
            print(f"Query enhancement failed: {e}")
            return None