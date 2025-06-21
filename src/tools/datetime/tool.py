"""
DateTime tool implementation with timezone support by location
"""

import aiohttp
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, available_timezones
from pydantic import BaseModel
from ..base import BaseTool, ToolResult
from ...services.openrouter import get_openrouter_service


class LocationResolution(BaseModel):
    """Pydantic model for LLM location resolution"""
    city_name: Optional[str] = None
    country: Optional[str] = None
    confidence: int  # 0-10 scale, 0 means nonsensical input


class DateTimeTool(BaseTool):
    """Get current date and time for any location with timezone support"""
    
    @property
    def name(self) -> str:
        return "get_datetime"
    
    @property
    def description(self) -> str:
        return "Get current date and time for a location with proper timezone"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string", 
                    "description": "Location name (city, country) or timezone (e.g., 'America/New_York')"
                },
                "format": {
                    "type": "string",
                    "description": "Output format: 'full', 'date', 'time', or 'iso'",
                    "enum": ["full", "date", "time", "iso"],
                    "default": "full"
                }
            },
            "required": ["location"]
        }
    
    async def _geocode_timezone(self, location: str) -> Optional[str | tuple[str, str]]:
        """Get timezone for a location using geocoding API"""
        print(f"🔍 Geocoding location: {location}")
        try:
            async with aiohttp.ClientSession() as session:
                # Use Open-Meteo geocoding to get coordinates
                url = "https://geocoding-api.open-meteo.com/v1/search"
                params = {
                    "name": location,
                    "count": 3,
                    "language": "en",
                    "format": "json"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        print(f"❌ Geocoding API returned status: {response.status}")
                        return await self._llm_location_fallback(location)
                    
                    data = await response.json()
                    results = data.get("results", [])
                    print(f"📍 Found {len(results)} geocoding results")
                    
                    if not results:
                        print("📍 No geocoding results, trying LLM fallback")
                        return await self._llm_location_fallback(location)
                    
                    # First try to find a result with a timezone
                    for i, result in enumerate(results):
                        timezone = result.get("timezone")
                        print(f"  Result {i+1}: {result.get('name', 'Unknown')} - Timezone: {timezone}")
                        if timezone:
                            print(f"✅ Found timezone: {timezone}")
                            return timezone
                    
                    # If no timezone found, try LLM fallback
                    print("📍 No timezone in results, trying LLM fallback")
                    return await self._llm_location_fallback(location)
        except Exception as e:
            print(f"❌ Geocoding exception: {e}")
            return await self._llm_location_fallback(location)
    
    async def _llm_location_fallback(self, location: str) -> Optional[tuple[str, str]]:
        """Use LLM to resolve location to a specific city"""
        print(f"🤖 Trying LLM fallback for: {location}")
        openrouter = get_openrouter_service()
        if not openrouter:
            print("❌ OpenRouter service not available (check OPENROUTER_API_KEY)")
            return None
        
        try:
            messages = [
                {
                    "role": "user", 
                    "content": f"""Given the input "{location}", determine if this appears to be a real location name (even with typos) or nonsensical text.

If it appears to be a real location attempt:
- Resolve it to the most appropriate major city for timezone purposes
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
            
            print("🤖 Calling LLM for location resolution...")
            result = await openrouter.structured_completion(
                messages=messages,
                response_model=LocationResolution
            )
            
            if result:
                print(f"🤖 LLM result for '{location}': confidence={result.confidence}, city='{result.city_name}', country='{result.country}'")
                
                # Check if LLM has confidence in the location
                if result.confidence < 6 or not result.city_name or not result.country:
                    print(f"❌ LLM rejected location '{location}' (confidence: {result.confidence})")
                    return None
                
                print(f"🤖 LLM resolved '{location}' -> '{result.city_name}, {result.country}'")
                # Try geocoding just the city name first
                timezone = await self._direct_geocode(result.city_name)
                if timezone:
                    corrected_name = f"{result.city_name}, {result.country}"
                    return (timezone, corrected_name)
                # If that fails, try with country
                resolved_location = f"{result.city_name}, {result.country}"
                timezone = await self._direct_geocode(resolved_location)
                if timezone:
                    return (timezone, resolved_location)
            else:
                print("❌ LLM returned no result")
            
            return None
        except Exception as e:
            print(f"❌ LLM fallback exception: {e}")
            return None
    
    async def _direct_geocode(self, location: str) -> Optional[str]:
        """Direct geocoding without LLM fallback"""
        print(f"🔍 Direct geocoding: {location}")
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://geocoding-api.open-meteo.com/v1/search"
                params = {
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        print(f"❌ Direct geocoding failed with status: {response.status}")
                        return None
                    
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if results:
                        result = results[0]
                        timezone = result.get("timezone")
                        print(f"✅ Direct geocoding found: {result.get('name')} - Timezone: {timezone}")
                        return timezone
                    else:
                        print("❌ Direct geocoding found no results")
                    
                    return None
        except Exception as e:
            print(f"❌ Direct geocoding exception: {e}")
            return None
    
    def _is_valid_timezone(self, timezone: str) -> bool:
        """Check if timezone string is valid"""
        return timezone in available_timezones()
    
    def _format_datetime(self, dt: datetime, format_type: str, location_name: str) -> str:
        """Format datetime according to specified format"""
        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "date":
            return dt.strftime("%A, %B %d, %Y")
        elif format_type == "time":
            return dt.strftime("%I:%M:%S %p %Z")
        else:  # full
            return f"""🕐 Current Date & Time in {location_name}

📅 Date: {dt.strftime("%A, %B %d, %Y")}
🕐 Time: {dt.strftime("%I:%M:%S %p")}
🌍 Timezone: {dt.strftime("%Z")} (UTC{dt.strftime("%z")})
📊 ISO Format: {dt.isoformat()}

Weekday: {dt.strftime("%A")}
Day of year: {dt.strftime("%j")}
Week of year: {dt.strftime("%U")}"""
    
    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the datetime tool"""
        location = arguments.get("location")
        format_type = arguments.get("format", "full")
        
        if not location:
            return ToolResult.error("Location is required")
        
        timezone_str = None
        location_name = location
        
        # Check if location is already a valid timezone
        if self._is_valid_timezone(location):
            timezone_str = location
            location_name = location.replace("_", " ").split("/")[-1]
        else:
            # Try to geocode the location to get timezone
            geocode_result = await self._geocode_timezone(location)
            if not geocode_result:
                return ToolResult.error(f"Could not determine timezone for location: {location}")
            
            if isinstance(geocode_result, tuple):
                timezone_str, location_name = geocode_result
            else:
                timezone_str = geocode_result
        
        try:
            # Get current time in the specified timezone
            tz = ZoneInfo(timezone_str)
            current_time = datetime.now(tz)
            
            # Return structured datetime data
            datetime_data = {
                "location": location_name,
                "timezone": timezone_str,
                "datetime": {
                    "iso": current_time.isoformat(),
                    "date": current_time.strftime("%A, %B %d, %Y"),
                    "time": current_time.strftime("%I:%M:%S %p"),
                    "timezone_name": current_time.strftime("%Z"),
                    "timezone_offset": current_time.strftime("%z"),
                    "weekday": current_time.strftime("%A"),
                    "day_of_year": int(current_time.strftime("%j")),
                    "week_of_year": int(current_time.strftime("%U"))
                },
                "coordinates": None,
                "format_requested": format_type
            }
            
            # If specific format requested, also include formatted text
            if format_type != "full":
                formatted_time = self._format_datetime(current_time, format_type, location_name)
                datetime_data["formatted_output"] = formatted_time
            
            return ToolResult.json(datetime_data)
            
        except Exception as e:
            return ToolResult.error(f"Failed to get datetime for {location}: {str(e)}")