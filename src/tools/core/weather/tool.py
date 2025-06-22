"""
Weather tool implementation using Open-Meteo API
"""

import aiohttp
from typing import Any, Dict, Optional
from pydantic import BaseModel
from src.tools.base import BaseTool, ToolResult
from src.services.openrouter import get_openrouter_service


class LocationResolution(BaseModel):
    """Pydantic model for LLM location resolution"""
    city_name: Optional[str] = None
    country: Optional[str] = None
    confidence: int  # 0-10 scale, 0 means nonsensical input


class WeatherTool(BaseTool):
    """Real weather tool using Open-Meteo API"""
    
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "Get current weather information for a location using Open-Meteo API"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for (city name, address, or coordinates)"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units (celsius or fahrenheit)",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["location"]
        }
    
    async def _geocode_location(self, location: str) -> Optional[Dict[str, Any] | tuple[Dict[str, Any], str]]:
        """Convert location name to coordinates using Open-Meteo geocoding API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://geocoding-api.open-meteo.com/v1/search"
                params = {
                    "name": location,
                    "count": 3,
                    "language": "en",
                    "format": "json"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return await self._llm_location_fallback(location)
                    
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        # Try LLM fallback
                        return await self._llm_location_fallback(location)
                    
                    result = results[0]
                    return {
                        "latitude": result.get("latitude"),
                        "longitude": result.get("longitude"),
                        "name": result.get("name"),
                        "country": result.get("country"),
                        "admin1": result.get("admin1")  # state/province
                    }
        except Exception:
            return await self._llm_location_fallback(location)
    
    async def _llm_location_fallback(self, location: str) -> Optional[tuple[Dict[str, Any], str]]:
        """Use LLM to resolve location to a specific city"""
        openrouter = get_openrouter_service()
        if not openrouter:
            return None
        
        try:
            messages = [
                {
                    "role": "user", 
                    "content": f"""Given the input "{location}", determine if this appears to be a real location name (even with typos) or nonsensical text.

If it appears to be a real location attempt:
- Resolve it to the most appropriate major city for weather purposes
- Set confidence to 7-10 based on how clear the location is
- Examples: "New Zealand" -> city_name: "Auckland", country: "New Zealand", confidence: 9
- Examples: "Califronia" (typo) -> city_name: "Los Angeles", country: "United States", confidence: 8

If it appears to be random text, HTML, complete nonsense, or unintelligible:
- Set confidence to 0
- Leave city_name and country as null
- Examples: "dsf asdkjfh asdlfkjh" -> confidence: 0
- Examples: "<html>random</html>" -> confidence: 0

Only return a city if you're confident this represents a genuine location attempt."""
                }
            ]
            
            result = await openrouter.structured_completion(
                messages=messages,
                response_model=LocationResolution
            )
            
            if result:
                # Check if LLM has confidence in the location
                if result.confidence < 6 or not result.city_name or not result.country:
                    return None
                
                # Try geocoding just the city name first
                geo_data = await self._direct_geocode(result.city_name)
                if geo_data:
                    corrected_name = f"{result.city_name}, {result.country}"
                    return (geo_data, corrected_name)
                # If that fails, try with country
                resolved_location = f"{result.city_name}, {result.country}"
                geo_data = await self._direct_geocode(resolved_location)
                if geo_data:
                    return (geo_data, resolved_location)
            
            return None
        except Exception:
            return None
    
    async def _direct_geocode(self, location: str) -> Optional[Dict[str, Any]]:
        """Direct geocoding without LLM fallback"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://geocoding-api.open-meteo.com/v1/search"
                params = {
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if results:
                        result = results[0]
                        return {
                            "latitude": result.get("latitude"),
                            "longitude": result.get("longitude"),
                            "name": result.get("name"),
                            "country": result.get("country"),
                            "admin1": result.get("admin1")
                        }
                    
                    return None
        except Exception:
            return None
    
    async def _get_weather(self, latitude: float, longitude: float, units: str = "celsius") -> Optional[Dict[str, Any]]:
        """Get weather data from Open-Meteo API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": [
                        "temperature_2m",
                        "relative_humidity_2m", 
                        "apparent_temperature",
                        "precipitation",
                        "weather_code",
                        "cloud_cover",
                        "wind_speed_10m",
                        "wind_direction_10m"
                    ],
                    "temperature_unit": units,
                    "wind_speed_unit": "kmh",
                    "precipitation_unit": "mm"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    return await response.json()
        except Exception:
            return None
    
    def _weather_code_to_description(self, code: int) -> str:
        """Convert WMO weather code to human-readable description"""
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            56: "Light freezing drizzle", 57: "Dense freezing drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            66: "Light freezing rain", 67: "Heavy freezing rain",
            71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        return weather_codes.get(code, f"Unknown weather (code: {code})")
    
    def _wind_direction_to_compass(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the weather tool"""
        location = arguments.get("location")
        units = arguments.get("units", "celsius")
        
        if not location:
            return ToolResult.error("Location is required")
        
        # First, geocode the location
        geocode_result = await self._geocode_location(location)
        if not geocode_result:
            return ToolResult.error(f"Could not find coordinates for location: {location}")
        
        # Handle both regular geocoding and LLM fallback results
        if isinstance(geocode_result, tuple):
            geo_data, corrected_location_name = geocode_result
        else:
            geo_data = geocode_result
            corrected_location_name = None
        
        # Get weather data
        weather_data = await self._get_weather(
            geo_data["latitude"], 
            geo_data["longitude"], 
            units
        )
        
        if not weather_data:
            return ToolResult.error("Failed to retrieve weather data")
        
        # Parse current weather
        current = weather_data.get("current", {})
        
        # Format location name (use corrected name if available)
        if corrected_location_name:
            location_name = corrected_location_name
        else:
            location_name = geo_data["name"]
            if geo_data.get("admin1"):
                location_name += f", {geo_data['admin1']}"
            if geo_data.get("country"):
                location_name += f", {geo_data['country']}"
        
        # Format weather description
        temp_unit = "°C" if units == "celsius" else "°F"
        weather_desc = self._weather_code_to_description(current.get("weather_code", 0))
        wind_dir = self._wind_direction_to_compass(current.get("wind_direction_10m", 0))
        
        weather_report = f"""🌤️ Weather in {location_name}

📍 Location: {geo_data['latitude']:.2f}, {geo_data['longitude']:.2f}
🌡️ Temperature: {current.get('temperature_2m', 'N/A')}{temp_unit}
🌡️ Feels like: {current.get('apparent_temperature', 'N/A')}{temp_unit}
☁️ Conditions: {weather_desc}
💧 Humidity: {current.get('relative_humidity_2m', 'N/A')}%
☔ Precipitation: {current.get('precipitation', 'N/A')} mm
☁️ Cloud cover: {current.get('cloud_cover', 'N/A')}%
💨 Wind: {current.get('wind_speed_10m', 'N/A')} km/h {wind_dir}

Data provided by Open-Meteo.com"""
        
        return ToolResult.text(weather_report)