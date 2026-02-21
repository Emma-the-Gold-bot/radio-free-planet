#!/usr/bin/env python3
"""Stream Validator - Tests 40+ radio streams for CORS, availability, format"""

import asyncio
import aiohttp
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
import json
from datetime import datetime

@dataclass
class StreamTest:
    station_id: str
    station_name: str
    url: str
    status: str = "pending"
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    cors_allowed: Optional[bool] = None
    cors_origin: Optional[str] = None
    icy_name: Optional[str] = None
    icy_genre: Optional[str] = None
    bitrate: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    tested_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

# 40+ Test streams
TEST_STREAMS = [
    # Major public radio
    {"id": "kexp", "name": "KEXP Seattle", "url": "https://kexp-mp3-128.streamguys1.com/kexp128.mp3"},
    {"id": "kcrw", "name": "KCRW Los Angeles", "url": "https://kcrw.streamguys1.com/kcrw_192k_mp3_on_air"},
    {"id": "wbur", "name": "WBUR Boston", "url": "https://audio.wbur.org/stream/live"},
    {"id": "wnyc", "name": "WNYC New York", "url": "https://wnyc.streamguys1.com/wnyc"},
    {"id": "wbez", "name": "WBEZ Chicago", "url": "https://wbez.streamguys1.com/wbez"},
    {"id": "kut", "name": "KUT Austin", "url": "https://kut.streamguys1.com/kut"},
    {"id": "wunc", "name": "WUNC Chapel Hill", "url": "https://wunc.streamguys1.com/wunc"},
    {"id": "wamu", "name": "WAMU Washington DC", "url": "https://wamu.streamguys1.com/wamu"},
    {"id": "wdav", "name": "WDAV Classical NC", "url": "https://wdav.streamguys1.com/wdav"},
    {"id": "wksu", "name": "WKSU Kent OH", "url": "https://wksu.streamguys1.com/wksu1"},
    
    # College radio  
    {"id": "kalx", "name": "KALX Berkeley", "url": "http://stream.kalx.berkeley.edu:8000/kalx-128.mp3"},
    {"id": "wxpn", "name": "WXPN Philadelphia", "url": "https://xpn2hi.streamguys1.com/xpn2hi"},
    {"id": "wfuv", "name": "WFUV New York", "url": "https://wfuv-onair.streamguys1.com/wfuvonair"},
    {"id": "kutx", "name": "KUTX Austin", "url": "https://kutx-streams.streamguys1.com/kutx-mp3"},
    {"id": "ktru", "name": "KTRU Rice Radio", "url": "https://ktru.streamguys1.com/ktru"},
    {"id": "kxlu", "name": "KXLU Los Angeles", "url": "https://kxlu.streamguys1.com/kxlu"},
    {"id": "kuci", "name": "KUCI Irvine", "url": "https://kuci.streamguys1.com/kuci"},
    {"id": "kspc", "name": "KSPC Claremont", "url": "https://kspc.streamguys1.com/kspc"},
    {"id": "wmse", "name": "WMSE Milwaukee", "url": "https://wmse.streamguys1.com/wmse128mp3"},
    {"id": "wrfl", "name": "WRFL Lexington", "url": "https://wrfl.fm/stream.mp3"},
    
    # WFMU streams
    {"id": "wfmu_main", "name": "WFMU Main", "url": "https://stream0.wfmu.org/freeform-128k"},
    {"id": "wfmu_ich", "name": "WFMU Ichiban", "url": "https://stream0.wfmu.org/ichiban"},
    {"id": "wfmu_drum", "name": "WFMU Drumheller", "url": "https://stream0.wfmu.org/drumheller"},
    {"id": "wfmu_gtd", "name": "WFMU Give Drummer", "url": "https://stream0.wfmu.org/gtd"},
    {"id": "wfmu_ut", "name": "WFMU Utrillo", "url": "https://stream0.wfmu.org/ut"},
    {"id": "wfmu_soul", "name": "WFMU Downtown Soul", "url": "https://stream0.wfmu.org/downtown"},
    
    # Canadian
    {"id": "cjsw", "name": "CJSW Calgary", "url": "https://stream.cjsw.com/cjsw.mp3"},
    {"id": "kgnu", "name": "KGNU Boulder", "url": "https://kgnu.streamguys1.com/kgnu"},
    {"id": "ckut", "name": "CKUT Montreal", "url": "http://128.ckut.ca:8000/ckut-live-192.mp3"},
    {"id": "ciut", "name": "CIUT Toronto", "url": "https://stream.zeno.fm/8artf9krrg0uv"},
    {"id": "chuo", "name": "CHUO Ottawa", "url": "https://chuo.streamguys1.com/chuo"},
    {"id": "cfmu", "name": "CFMU Hamilton", "url": "http://138.197.148.215:8000/ckcu-temp-128kbps.aac"},
    
    # More college/community
    {"id": "kdvs", "name": "KDVS Davis", "url": "http://archives.kdvs.org:8000/kdvs128mp3"},
    {"id": "kfsr", "name": "KFSR Fresno", "url": "https://kfsr.streamguys1.com/kfsr"},
    {"id": "kbeach", "name": "KBeach Long Beach", "url": "https://kbeach.streamguys1.com/kbeach"},
    {"id": "wncw", "name": "WNCW Spindale NC", "url": "https://wncw.streamguys1.com/wncw"},
    {"id": "wtul", "name": "WTUL New Orleans", "url": "https://wtul.streamguys1.com/wtul"},
    {"id": "wzrd", "name": "WZRD Chicago", "url": "http://wzrd.broadcasttoolbox.com:8000/WZRD"},
    {"id": "wsou", "name": "WSOU Seton Hall", "url": "https://wsou.streamguys1.com/wsou"},
    {"id": "kpcr", "name": "KPCR Santa Monica", "url": "https://kpcr.streamguys1.com/kpcr"},
    {"id": "ksbr", "name": "KSBR Orange County", "url": "https://ksbr.streamguys1.com/ksbr"},
]

async def test_stream(session: aiohttp.ClientSession, stream: Dict) -> StreamTest:
    test = StreamTest(
        station_id=stream["id"],
        station_name=stream["name"],
        url=stream["url"]
    )
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with session.head(
            stream["url"], 
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"},
            allow_redirects=True
        ) as response:
            test.http_status = response.status
            test.response_time_ms = round((asyncio.get_event_loop().time() - start_time) * 1000)
            
            if response.status == 200:
                test.status = "ok"
                test.content_type = response.headers.get("Content-Type")
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                test.cors_origin = cors_origin
                test.cors_allowed = cors_origin == "*"
                test.icy_name = response.headers.get("icy-name")
                test.icy_genre = response.headers.get("icy-genre")
                test.icy_br = response.headers.get("icy-br")
                if test.icy_br:
                    try:
                        test.bitrate = int(test.icy_br)
                    except:
                        pass
            elif response.status == 400:
                test.status = "head_rejected"
            else:
                test.status = "http_error"
                test.error_message = f"HTTP {response.status}"
                
    except asyncio.TimeoutError:
        test.status = "timeout"
        test.error_message = "Connection timed out"
    except Exception as e:
        test.status = "error"
        test.error_message = str(e)
    
    test.tested_at = datetime.now().isoformat()
    return test

async def test_stream_get(session: aiohttp.ClientSession, test: StreamTest) -> StreamTest:
    if test.status not in ["head_rejected", "http_error"]:
        return test
    
    try:
        async with session.get(
            test.url,
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"},
            allow_redirects=True
        ) as response:
            test.http_status = response.status
            if response.status == 200:
                test.status = "ok"
                test.content_type = response.headers.get("Content-Type")
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                test.cors_origin = cors_origin
                test.cors_allowed = cors_origin == "*"
                test.icy_name = response.headers.get("icy-name")
                test.icy_genre = response.headers.get("icy-genre")
                
                # Check if actually audio
                chunk = await response.content.read(1024)
                if len(chunk) < 100:
                    test.status = "empty_response"
                    test.error_message = "Empty response"
            else:
                test.status = "http_error"
                test.error_message = f"HTTP {response.status} (GET)"
    except Exception as e:
        if test.status == "head_rejected":
            test.status = "error"
            test.error_message = str(e)
    
    return test

async def validate_all_streams():
    print(f"Testing {len(TEST_STREAMS)} streams...")
    
    async with aiohttp.ClientSession() as session:
        tests = await asyncio.gather(*[test_stream(session, s) for s in TEST_STREAMS])
        tests = await asyncio.gather(*[test_stream_get(session, t) for t in tests])
    
    return tests

def categorize_results(tests: List[StreamTest]) -> Dict:
    categories = {
        "working_browser": [],
        "working_proxy": [],
        "unavailable": [],
        "timeout": [],
        "needs_investigation": []
    }
    
    for test in tests:
        if test.status == "ok":
            if test.cors_allowed:
                categories["working_browser"].append(test)
            else:
                categories["working_proxy"].append(test)
        elif test.status == "timeout":
            categories["timeout"].append(test)
        elif test.status in ["unavailable", "error", "client_error"]:
            categories["unavailable"].append(test)
        else:
            categories["needs_investigation"].append(test)
    
    return categories

def print_results(tests: List[StreamTest], categories: Dict):
    print("\n" + "="*80)
    print("STREAM VALIDATION RESULTS")
    print("="*80)
    
    print(f"\n✅ WORKS IN BROWSER ({len(categories['working_browser'])}):")
    for test in categories["working_browser"]:
        bitrate = f"{test.bitrate}kbps" if test.bitrate else "?kbps"
        print(f"  🌐 {test.station_name:25} | {bitrate:8} | {test.icy_genre or 'n/a'}")
    
    print(f"\n🔒 NEEDS CORS PROXY ({len(categories['working_proxy'])}):")
    for test in categories["working_proxy"]:
        print(f"  🔒 {test.station_name:25} | CORS: {test.cors_origin or 'none'}")
    
    print(f"\n❌ UNAVAILABLE ({len(categories['unavailable'])}):")
    for test in categories["unavailable"]:
        print(f"  ❌ {test.station_name:25} | {test.error_message[:40]}")
    
    print(f"\n⏱️ TIMEOUT ({len(categories['timeout'])}):")
    for test in categories["timeout"]:
        print(f"  ⏱️  {test.station_name:25}")
    
    print(f"\n❓ NEEDS INVESTIGATION ({len(categories['needs_investigation'])}):")
    for test in categories["needs_investigation"]:
        print(f"  ❓ {test.station_name:25} | {test.status}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total = len(tests)
    working = len(categories['working_browser'])
    proxy = len(categories['working_proxy'])
    dead = len(categories['unavailable']) + len(categories['timeout'])
    
    print(f"Total tested:     {total}")
    print(f"Browser-ready:    {working} ({working/total*100:.1f}%)")
    print(f"Needs proxy:      {proxy} ({proxy/total*100:.1f}%)")
    print(f"Dead/unreachable: {dead} ({dead/total*100:.1f}%)")

def save_results(tests: List[StreamTest], filename: str = "stream_results_40.json"):
    data = {
        "tested_at": datetime.now().isoformat(),
        "total": len(tests),
        "streams": [test.to_dict() for test in tests]
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {filename}")

async def main():
    tests = await validate_all_streams()
    categories = categorize_results(tests)
    print_results(tests, categories)
    save_results(tests)

if __name__ == "__main__":
    asyncio.run(main())
