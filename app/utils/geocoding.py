import math
import httpx
from typing import Tuple, Optional
from urllib.parse import quote
from app.config import settings

async def get_lat_lng_from_address(address: str) -> Optional[Tuple[float, float]]:
    """Busca latitude e longitude de um endereço usando Mapbox API."""
    if not settings.MAPBOX_ACCESS_TOKEN:
        print("Warning: MAPBOX_ACCESS_TOKEN not set in environment")
        return None

    encoded_address = quote(address)
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json"
    params = {
        "access_token": settings.MAPBOX_ACCESS_TOKEN,
        "limit": 1
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data and "features" in data and len(data["features"]) > 0:
                feature = data["features"][0]
                # Mapbox returns [longitude, latitude]
                lon, lat = feature["geometry"]["coordinates"]
                return float(lat), float(lon)
    except Exception as e:
        print(f"Geocoding error: {e}")
        pass
    
    return None

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância em km entre duas coordenadas usando a fórmula de Haversine."""
    R = 6371.0 # Raio da terra em km

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
