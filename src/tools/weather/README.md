# Weather Tool

Provides current weather information for any location using the Open-Meteo API.

## Purpose
Get real-time weather data including temperature, conditions, humidity, wind, and more for any location worldwide.

## Parameters

| Parameter | Type   | Required | Description                                                |
|-----------|--------|----------|------------------------------------------------------------|
| location  | string | Yes      | Location to get weather for (city name, address, or coordinates) |
| units     | string | No       | Temperature units: "celsius" (default) or "fahrenheit"     |

## Configuration
No configuration required.

## Features

- **Flexible Location Input**: Accepts city names, addresses, or coordinates
- **Geocoding**: Converts location names to coordinates via Open-Meteo
- **LLM Fallback**: Uses OpenRouter to handle typos or ambiguous locations
- **Comprehensive Data**: Temperature, conditions, humidity, wind, precipitation, and more
- **Weather Emojis**: Visual representation of weather conditions
- **Unit Conversion**: Support for both Celsius and Fahrenheit

## Example Usage

**Basic Usage:**
```json
{
  "location": "San Francisco"
}
```

**With Fahrenheit:**
```json
{
  "location": "London",
  "units": "fahrenheit"
}
```

## Output Example

```
🌤️ Weather for San Francisco, California, United States

Temperature: 15.2°C (59.4°F)
Feels like: 13.8°C (56.8°F)
Conditions: Partly cloudy

💧 Humidity: 72%
🌧️ Precipitation: 0.0 mm
☁️ Cloud cover: 45%
💨 Wind: 12.5 km/h from SW
```

## Weather Conditions

The tool translates WMO weather codes into readable conditions with emojis:

- ☀️ Clear sky
- 🌤️ Partly cloudy
- ☁️ Overcast
- 🌫️ Fog
- 🌧️ Rain (various intensities)
- 🌨️ Snow (various intensities)
- ⛈️ Thunderstorm

## Wind Directions

Wind direction is converted from degrees to compass directions:
- N (North): 337.5° - 22.5°
- NE (Northeast): 22.5° - 67.5°
- E (East): 67.5° - 112.5°
- SE (Southeast): 112.5° - 157.5°
- S (South): 157.5° - 202.5°
- SW (Southwest): 202.5° - 247.5°
- W (West): 247.5° - 292.5°
- NW (Northwest): 292.5° - 337.5°

## Error Handling

- Location not found errors with suggestions
- API connection errors
- Invalid coordinate handling
- Graceful fallback for missing weather data

## Data Source

Weather data is provided by [Open-Meteo](https://open-meteo.com/), a free weather API with global coverage.