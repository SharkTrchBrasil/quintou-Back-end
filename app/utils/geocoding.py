"""
Geocoding utilities using Mapbox API
"""
import httpx
import logging
from typing import Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


async def get_lat_lng_from_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Converte endereço em coordenadas lat/lng usando Mapbox Geocoding API.
    
    Args:
        address: Endereço completo (rua, cidade, estado, CEP)
    
    Returns:
        Tuple (latitude, longitude) ou None se falhar
    """
    mapbox_token = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
    
    if not mapbox_token:
        logger.warning("MAPBOX_ACCESS_TOKEN not configured. Geocoding disabled.")
        return None
    
    try:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
        params = {
            "access_token": mapbox_token,
            "country": "BR",  # Restringe ao Brasil
            "limit": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("features") and len(data["features"]) > 0:
                coordinates = data["features"][0]["geometry"]["coordinates"]
                # Mapbox retorna [longitude, latitude]
                lng, lat = coordinates
                logger.info(f"Geocoded address: {address} -> ({lat}, {lng})")
                return (lat, lng)
            else:
                logger.warning(f"No geocoding results for address: {address}")
                return None
                
    except httpx.TimeoutException:
        logger.error(f"Timeout geocoding address: {address}")
        return None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error geocoding address: {address} - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error geocoding address: {address} - {str(e)}")
        return None


async def get_address_from_lat_lng(lat: float, lng: float) -> Optional[dict]:
    """
    Reverse geocoding: converte coordenadas em endereço.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Dicionário com componentes do endereço ou None se falhar
    """
    mapbox_token = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
    
    if not mapbox_token:
        logger.warning("MAPBOX_ACCESS_TOKEN not configured. Reverse geocoding disabled.")
        return None
    
    try:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lng},{lat}.json"
        params = {
            "access_token": mapbox_token,
            "types": "address",
            "limit": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("features") and len(data["features"]) > 0:
                feature = data["features"][0]
                
                # Extrai componentes do endereço
                address = {
                    "place_name": feature.get("place_name"),
                    "address_line": feature.get("address"),
                    "neighborhood": None,
                    "city": None,
                    "state": None,
                    "zip_code": None
                }
                
                # Parse context para extrair cidade, estado, etc
                for ctx in feature.get("context", []):
                    if "postcode" in ctx.get("id", ""):
                        address["zip_code"] = ctx.get("text")
                    elif "place" in ctx.get("id", ""):
                        address["city"] = ctx.get("text")
                    elif "region" in ctx.get("id", ""):
                        address["state"] = ctx.get("short_code", "").split("-")[-1].upper()
                    elif "neighborhood" in ctx.get("id", ""):
                        address["neighborhood"] = ctx.get("text")
                
                logger.info(f"Reverse geocoded: ({lat}, {lng}) -> {address['place_name']}")
                return address
            else:
                logger.warning(f"No reverse geocoding results for: ({lat}, {lng})")
                return None
                
    except httpx.TimeoutException:
        logger.error(f"Timeout reverse geocoding: ({lat}, {lng})")
        return None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error reverse geocoding: ({lat}, {lng}) - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error reverse geocoding: ({lat}, {lng}) - {str(e)}")
        return None


def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula distância entre dois pontos usando fórmula de Haversine.
    
    Args:
        lat1, lng1: Coordenadas do ponto 1
        lat2, lng2: Coordenadas do ponto 2
    
    Returns:
        Distância em quilômetros
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Converte para radianos
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    # Fórmula de Haversine
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    
    # Raio da Terra em km
    r = 6371
    
    return c * r
