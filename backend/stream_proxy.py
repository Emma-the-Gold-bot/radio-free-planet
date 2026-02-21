# backend/stream_proxy.py
"""
Stream Proxy - Routes streams through backend to bypass CORS
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import aiohttp
import ssl
from typing import Optional

router = APIRouter()

# SSL context that ignores cert errors (for development)
# In production, use proper certs
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def fetch_stream(url: str, station_id: Optional[str] = None):
    """
    Fetch stream from source with error handling
    Returns tuple of (content_iterator, headers, status_code)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; RadioAgnostic/1.0)",
                    "Accept": "audio/mpeg,audio/aac,audio/ogg,*/*",
                    "Icy-Metadata": "1"  # Request metadata
                }
            ) as resp:
                
                if resp.status != 200:
                    return None, None, resp.status
                
                # Extract relevant headers
                headers = {}
                for key in ["Content-Type", "icy-name", "icy-genre", "icy-br", "icy-metaint"]:
                    if key in resp.headers:
                        headers[key] = resp.headers[key]
                
                # Add CORS header for browser
                headers["Access-Control-Allow-Origin"] = "*"
                headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                
                return resp.content.iter_chunked(8192), headers, 200
                
    except aiohttp.ClientError as e:
        print(f"Client error fetching {url}: {e}")
        return None, None, 502
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None, 500

@router.get("/stream/{station_id}")
async def proxy_station_stream(station_id: str):
    """
    Proxy stream for a specific station
    This bypasses CORS restrictions by routing through our backend
    """
    from main import stations_db
    
    station = stations_db.get(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    # Get primary stream URL
    stream_url = None
    for stream in station.streams:
        if stream.is_primary:
            stream_url = stream.url
            break
    
    if not stream_url and station.streams:
        stream_url = station.streams[0].url
    
    if not stream_url:
        raise HTTPException(status_code=404, detail="No stream URL available")
    
    content_iter, headers, status = await fetch_stream(stream_url, station_id)
    
    if status != 200:
        raise HTTPException(status_code=status, detail=f"Stream unavailable")
    
    return StreamingResponse(
        content_iter,
        media_type=headers.get("Content-Type", "audio/mpeg"),
        headers=headers
    )

@router.get("/health/{station_id}")
async def check_stream_health(station_id: str):
    """
    Check if a station's stream is healthy without consuming bandwidth
    """
    from main import stations_db
    
    station = stations_db.get(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    stream_url = None
    for stream in station.streams:
        if stream.is_primary:
            stream_url = stream.url
            break
    
    if not stream_url:
        return {"healthy": False, "error": "No stream URL"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(
                stream_url,
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True
            ) as resp:
                healthy = resp.status == 200
                return {
                    "healthy": healthy,
                    "status": resp.status,
                    "content_type": resp.headers.get("Content-Type"),
                    "icy_name": resp.headers.get("icy-name")
                }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

@router.options("/{path:path}")
async def cors_preflight(path: str):
    """Handle CORS preflight requests"""
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Icy-Metadata",
        }
    )
