# YouTube Lookup Tool

Search through YouTube video chunks using semantic similarity powered by vector embeddings.

## Description

This tool enables semantic search across pre-processed YouTube video transcripts. It uses vector embeddings to find content similar to your query and returns relevant video segments with timestamps and similarity scores.

## Data Requirements

This tool requires that YouTube video chunks have been pre-processed and stored in the PostgreSQL database by an external script. The database must contain:

- **YouTube video transcripts** segmented into chunks with timestamps
- **Vector embeddings** generated using Cloudflare AI (@cf/baai/bge-m3 model)
- **Project isolation** via `project_slug` for multi-tenant access
- **Database schema** with pgvector extension enabled

### Database Schema

The tool expects data in the `youtube_chunks` table with the following structure:

```sql
CREATE TABLE youtube_chunks (
    id SERIAL PRIMARY KEY,
    project_slug VARCHAR(255) NOT NULL,
    video_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    start_timestamp INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1024),  -- Cloudflare AI bge-m3 embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Embedding Model

- **Model**: `@cf/baai/bge-m3` (Cloudflare AI)
- **Dimensions**: 1024
- **Type**: Dense vector embeddings optimized for semantic search
- **Distance metric**: Cosine similarity

## Configuration

The tool requires the following configuration when added to a client:

```json
{
  "project_slug": "my_youtube_project",
  "max_results": 10,
  "min_similarity": 0.01,
  "enhance_query": true,
  "hybrid_search": true,
  "keyword_weight": 0.5,
  "query_expansion_prompt": null
}
```

### Configuration Parameters

- **`project_slug`** (required): Project identifier that restricts search to specific dataset
- **`max_results`** (optional): Maximum number of results to return (default: 10, max: 50)
- **`min_similarity`** (optional): Minimum similarity threshold 0.0-1.0 (default: 0.01)
- **`enhance_query`** (optional): Use LLM to expand queries for better matching (default: true)
- **`hybrid_search`** (optional): Combine vector similarity with keyword search (default: true)
- **`keyword_weight`** (optional): Weight for keyword vs vector search 0.0-1.0 (default: 0.5)
- **`query_expansion_prompt`** (optional): Custom prompt template for query expansion. Use `{query}` as placeholder for the original query. If not provided, uses default prompt.

## Usage

### Input Parameters

- **`query`** (required): Search query to find similar video content

### Example Usage

```json
{
  "query": "product launch strategy"
}
```

## Response Format

The tool returns structured JSON data with:

1. **Search metadata** - Query information and search settings
2. **YouTube URLs** with timestamp links for direct access  
3. **Similarity scores** for relevance ranking (filtered by minimum threshold)
4. **Complete result data** for programmatic access

### Example Response

```json
{
  "original_query": "product launch strategy",
  "enhanced_query": "Product launch strategy planning including market analysis, timing, marketing campaigns and competitive positioning for successful product introductions",
  "enhancement_used": true,
  "hybrid_search": true,
  "keyword_weight": 0.5,
  "project_slug": "my_youtube_project",
  "min_similarity": 0.01,
  "results_count": 3,
  "results": [
    {
      "title": "Successful Product Launch Framework | Business Strategy",
      "vector_score": 0.112,
      "keyword_score": 0.244,
      "combined_score": 0.178,
      "youtube_url": "https://www.youtube.com/watch?v=abc123&t=145s",
      "text": "A successful product launch requires careful planning and execution across multiple channels. You need to understand your target market, develop compelling messaging, coordinate marketing campaigns, and have a clear timeline for rollout. The key is to build anticipation while ensuring you can deliver on your promises."
    },
    {
      "title": "Market Research for New Products",
      "vector_score": 0.089,
      "keyword_score": 0.241,
      "combined_score": 0.165,
      "youtube_url": "https://www.youtube.com/watch?v=def456&t=67s",
      "text": "Understanding your target market is crucial before any product launch. This involves analyzing customer needs, competitor offerings, market size, and pricing strategies. Without proper research, even the best products can fail in the marketplace."
    },
    {
      "title": "Launch Timing and Competitive Analysis",
      "vector_score": 0.076,
      "keyword_score": 0.209,
      "combined_score": 0.143,
      "youtube_url": "https://www.youtube.com/watch?v=ghi789&t=234s",
      "text": "The timing of your product launch can make or break its success. Consider seasonal factors, competitor activities, market conditions, and your own resource availability. A well-timed launch can give you significant competitive advantages."
    }
  ]
}
```

## Features

- **Hybrid search**: Combines semantic similarity with keyword matching for best results
- **Semantic search**: Finds conceptually similar content, not just keyword matches
- **Keyword search**: Full-text search for exact term matching using PostgreSQL
- **Query enhancement**: Uses LLM to expand short queries into detailed descriptions
- **Configurable weighting**: Adjust balance between vector and keyword search (0.0-1.0)
- **Project isolation**: Each client only searches their configured dataset
- **Quality filtering**: Configurable minimum similarity threshold to filter weak matches
- **Timestamp precision**: Direct links to relevant video moments
- **Multi-score ranking**: Shows vector, keyword, and combined scores for transparency
- **Clean output**: Simplified response with only essential information
- **Flexible configuration**: Toggle hybrid search, query enhancement, and scoring weights

## Technical Details

- Uses Cloudflare AI embeddings (@cf/baai/bge-m3)
- OpenRouter LLM service for query enhancement (google/gemma-3-27b-it)
- PostgreSQL with pgvector for similarity search
- PostgreSQL full-text search with tsvector/tsquery for keyword matching
- Cosine similarity for embedding comparison
- HNSW indexes for fast vector search performance
- Weighted score combination: `(vector_score * (1-weight)) + (keyword_score * weight)`

## Query Enhancement

The tool automatically expands short queries using an LLM to improve search quality:

**Example:**
- **Original**: "marketing tips"
- **Enhanced**: "Digital marketing strategies and tips including social media campaigns, content marketing, SEO optimization, email marketing best practices, and customer acquisition techniques"

This helps match against longer video transcript chunks by providing more semantic context and domain-specific terminology.

### Custom Query Expansion

You can customize the query expansion behavior by providing a custom prompt template in the configuration:

```json
{
  "query_expansion_prompt": "You are a domain expert in business and entrepreneurship. Expand this search query to include relevant business terminology, synonyms, and related concepts: '{query}'. Return only the expanded query, no explanations."
}
```

**Example custom prompts for different domains:**

**Business/Marketing:**
```
"Expand this business query with industry terminology and related concepts: '{query}'. Include synonyms for business terms, marketing strategies, and entrepreneurship concepts. Return only the enhanced query."
```

**Technology:**
```
"You are a tech expert. Expand this query with technical terminology, programming concepts, and related technology topics: '{query}'. Include relevant tech jargon and synonyms. Return only the expanded query."
```

**Education:**
```
"Expand this educational query with learning concepts, teaching methods, and academic terminology: '{query}'. Include educational synonyms and related pedagogical terms. Return only the enhanced query."
```

## Data Population

To use this tool, you must first populate the database with YouTube video chunks using an external script. The script should:

1. **Extract video transcripts** from YouTube videos (using YouTube API or transcript extraction tools)
2. **Segment transcripts** into chunks with proper timestamps and indexing
3. **Generate embeddings** using Cloudflare AI's `@cf/baai/bge-m3` model
4. **Store chunks** in the `youtube_chunks` table with all required fields
5. **Organize by project** using `project_slug` for multi-tenant isolation

### Required Data Fields

Each chunk must include:
- `project_slug`: Identifies the dataset/client
- `video_id`: YouTube video identifier  
- `title`: Video title for context
- `start_timestamp`: Timestamp in seconds for the chunk
- `chunk_index`: Sequential chunk number within the video
- `text`: Transcript text content
- `embedding`: 1024-dimension vector from Cloudflare AI