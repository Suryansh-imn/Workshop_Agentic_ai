# API Endpoints Used in Workshop

## Hacker News Search API (Algolia)
- **Base URL:** `https://hn.algolia.com/api/v1`
- **Search endpoint:** `/search?query={query}&tags=story&numericFilters=created_at_i>{timestamp}`
- **No authentication required**
- **Rate limits:** Generous, no key needed
- **Documentation:** https://hn.algolia.com/api

Example search for recent stories:
```
https://hn.algolia.com/api/v1/search?query=LangGraph&tags=story&numericFilters=created_at_i>1725408000
```

Returns JSON with:
- `hits[]` - array of stories
  - `title` - story title
  - `url` - external URL (if available)
  - `objectID` - HN item ID
  - `created_at_i` - Unix timestamp
  - `author` - username
  - `points` - score

## Web Fetching
- Use standard HTTP libraries (requests, fetch)
- 10 second timeout
- Basic error handling
