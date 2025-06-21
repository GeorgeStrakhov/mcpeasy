- SERVICE: perplexity

- SERVICE: Exa

- SERVICE: serpapi

- TOOL: scientific_search (using various searches and then combining results + optional prompt enhancement)

- TOOL: save_memory, get_memory. Memory needs to be saved per client, but also optionally have userId column where LLM can put this user this belongs to. calculate embeddings automatically. smart hybrid search on get_memory

- SERVICE: firecrawl

- TOOL: scrape / crawl webstuff

- TOOL: execute code (e2b or pyodide, whatever easier. consider how data can be passed)

- ARCHITECTURE: consider task queue for scalability on execute tool