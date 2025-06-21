# DateTime Tool

Provides current date and time information for any location worldwide with timezone support.

## Purpose
Get accurate datetime information for any location, with proper timezone handling and multiple output formats.

## Parameters

| Parameter | Type   | Required | Description                                                    |
|-----------|--------|----------|----------------------------------------------------------------|
| location  | string | Yes      | Location name (e.g., "Tokyo", "New York") or timezone ID (e.g., "America/New_York") |
| format    | string | No       | Output format: "full" (default), "date", "time", or "iso"     |

## Configuration
No configuration required.

## Features
- **Smart Location Resolution**: Handles city names, countries, and timezone identifiers
- **Geocoding Support**: Uses Open-Meteo API to convert location names to coordinates
- **LLM Fallback**: Uses OpenRouter to handle typos or ambiguous locations
- **Timezone Validation**: Validates against pytz timezone database
- **Rich Output**: Includes weekday, day of year, and week of year information

## Example Usage

**Basic Usage:**
```json
{
  "location": "Paris"
}
```

**With Format:**
```json
{
  "location": "Tokyo",
  "format": "iso"
}
```

## Output Formats

### Full Format (default)
```
Current date and time in Tokyo, Japan:
Date: Monday, January 15, 2025
Time: 10:30:45 PM JST
Full: 2025-01-15 22:30:45 JST
Day of year: 15, Week of year: 3
```

### Date Format
```
Monday, January 15, 2025
```

### Time Format
```
10:30:45 PM JST
```

### ISO Format
```
2025-01-15T22:30:45+09:00
```

## Error Handling
- Returns error if location cannot be resolved
- Handles invalid timezone identifiers gracefully
- Provides helpful error messages for debugging