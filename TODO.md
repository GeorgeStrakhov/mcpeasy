- CLEANUP: delete old knowledge model and pre-population logic

- ADMIN: export / import tool configs in the admin. export / import entire DB in the admin.

- TOOL: search (behind the scenes can use exa, serpapi, firecrawl)

- SERVICE: perplexity

- SERVICE: Exa

- SERVICE: serpapi

- SERVICE: replicate

- SERVICE: fal

- TOOL: scientific_search (using various searches and then combining results + optional prompt enhancement)

- TOOL: save_memory, get_memory. Memory needs to be saved per client, but also optionally have userId column where LLM can put this user this belongs to. calculate embeddings automatically. smart hybrid search on get_memory

- SERVICE: e2b (for code execution)

- TOOL: execute code (e2b or pyodide, whatever easier. consider how data can be passed)