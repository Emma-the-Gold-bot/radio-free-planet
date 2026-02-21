#!/usr/bin/env python3
"""Stream Validator - Testing NON-CDN fallback URLs"""

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

# NON-CDN FALLBACK STREAMS - Direct from stations
FALLBACK_STREAMS = [
    # WNYC / WQXR (found from wnyc.org/audio/other-formats)
    {"id": "wnyc_fm", "name": "WNYC 93.9 FM", "url": "https://fm939.wnyc.org/wnycfm"},
    {"id": "wnyc_am", "name": "WNYC 820 AM", "url": "https://am820.wnyc.org/wnycam"},
    {"id": "wqxr", "name": "WQXR 105.9 FM", "url": "https://stream.wqxr.org/wqxr"},
    {"id": "wqxr_newsounds", "name": "WQXR New Sounds", "url": "https://q2stream.wqxr.org/q2"},
    {"id": "wqxr_operavore", "name": "WQXR Operavore", "url": "https://opera-stream.wqxr.org/operavore"},
    {"id": "wqxr_standards", "name": "WQXR New Standards", "url": "https://tjc.wnyc.org/js-stream"},
    
    # KUT / KUTX (found from kut.org/streams - moved off streamguys)
    {"id": "kut", "name": "KUT Austin", "url": "https://streams.kut.org/4426_128.mp3?aw_0_1st.playerid=kut-free"},
    {"id": "kutx", "name": "KUTX Austin", "url": "https://streams.kut.org/4428_192.mp3?aw_0_1st.playerid=kutx-free"},
    
    # Additional hopefuls - HTTP instead of HTTPS
    {"id": "kcrw_http", "name": "KCRW Los Angeles (HTTP)", "url": "http://kcrw.streamguys1.com/kcrw_192k_mp3_on_air"},
    {"id": "wbur_http", "name": "WBUR Boston (HTTP)", "url": "http://audio.wbur.org/stream/live"},
    {"id": "wxpn_http", "name": "WXPN Philadelphia (HTTP)", "url": "http://xpn2hi.streamguys1.com/xpn2hi"},
    {"id": "wfuv_http", "name": "WFUV New York (HTTP)", "url": "http://wfuv-onair.streamguys1.com/wfuvonair"},
    
    # Alternative CDNs / direct icecast
    {"id": "wbgo_alt", "name": "WBGO Jazz (Alt)", "url": "https://wbgo.streamguys1.com/wbgo"},
    {"id": "wksu_alt", "name": "WKSU Kent (Alt)", "url": "https://wksu.streamguys1.com/wksu"},
    {"id": "wunc_alt", "name": "WUNC Chapel Hill (Alt)", "url": "https://wunc.streamguys1.com/wunc"},
    {"id": "wamu_alt", "name": "WAMU DC (Alt)", "url": "https://wamu.streamguys1.com/wamu"},
    
    # More college stations - direct icecast/shoutcast
    {"id": "kdvs_alt", "name": "KDVS Davis (Direct)", "url": "http://kdvs.ucdavis.edu:8000/kdvs128mp3"},
    {"id": "kdvs_ice", "name": "KDVS Davis (Icecast)", "url": "http://icecast.kdvs.org:8000/kdvs128mp3"},
    {"id": "kzsu", "name": "KZSU Stanford", "url": "http://kzsu-streams.stanford.edu/kzsu-1-128.mp3"},
    {"id": "ksco", "name": "KSCO Santa Cruz", "url": "http://streaming.ksco.com:8000/ksco"},
    {"id": "kkup", "name": "KKUP San Jose", "url": "http://streams.kkup.org:8000/kkup-128.mp3"},
    {"id": "kper", "name": "KPER Union City", "url": "http://kper-ice.streamguys1.com/kper"},
    
    # East Coast college
    {"id": "wcbn", "name": "WCBN Ann Arbor", "url": "http://floyd.wcbn.org:8000/wcbn-hi.mp3"},
    {"id": "wtul_alt", "name": "WTUL New Orleans", "url": "http://stream.wtul.neworleans.com:8000/stream.mp3"},
    {"id": "wncw_alt", "name": "WNCW Spindale", "url": "http://audio-ice.wncw.org:8000/wncw"},
    {"id": "wrfl_alt", "name": "WRFL Lexington (Direct)", "url": "http://wrfl.fm/stream.mp3"},
    
    # Canadian alternatives
    {"id": "ciut_alt", "name": "CIUT Toronto", "url": "http://stream2.ciut.fm:8000/ciut-fm-192.mp3"},
    {"id": "ckut_alt", "name": "CKUT Montreal (Direct)", "url": "http://icecast.ckut.ca:8000/ckut-live-192.mp3"},
    {"id": "cfmu_alt", "name": "CFMU Hamilton", "url": "http://138.197.148.215:8000/stream"},
    {"id": "chuo_alt", "name": "CHUO Ottawa (Direct)", "url": "http://icecast.chuo.ca:8000/chuo"},
    
    # Additional WFMU substreams (HTTP versions)
    {"id": "wfmu_ich_http", "name": "WFMU Ichiban (HTTP)", "url": "http://stream0.wfmu.org/ichiban"},
    {"id": "wfmu_drum_http", "name": "WFMU Drumheller (HTTP)", "url": "http://stream0.wfmu.org/drumheller"},
    {"id": "wfmu_gtd_http", "name": "WFMU Give Drummer (HTTP)", "url": "http://stream0.wfmu.org/gtd"},
    {"id": "wfmu_ut_http", "name": "WFMU Utrillo (HTTP)", "url": "http://stream0.wfmu.org/ut"},
    {"id": "wfmu_soul_http", "name": "WFMU Downtown Soul (HTTP)", "url": "http://stream0.wfmu.org/downtown"},
    
    # NPR Network (non-streamguys)
    {"id": "npr_direct", "name": "NPR Program Stream", "url": "https://npr-ice.streamguys1.com/live.mp3"},
    {"id": "npr_news_direct", "name": "NPR News Now", "url": "https://npr-ice.streamguys1.com/news.mp3"},
    
    # Test stations that worked before
    {"id": "kexp_confirm", "name": "KEXP (Confirm)", "url": "https://kexp-mp3-128.streamguys1.com/kexp128.mp3"},
    {"id": "cjsw_confirm", "name": "CJSW (Confirm)", "url": "https://stream.cjsw.com/cjsw.mp3"},
    {"id": "wmse_confirm", "name": "WMSE (Confirm)", "url": "https://wmse.streamguys1.com/wmse128mp3"},
    {"id": "wrfl_confirm", "name": "WRFL (Confirm)", "url": "https://wrfl.fm/stream.mp3"},
]

async def test_stream(session: aiohttp.ClientSession, stream: Dict) -> StreamTest:
    test = StreamTest(
        station_id=stream["id"],
        station_name=stream["name"],
        url=stream["url"]
    )
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Test with HEAD first
        async with session.head(
            stream["url"], 
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            ssl=False  # Try without SSL verification for HTTP fallbacks
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
                icy_br = response.headers.get("icy-br")
                if icy_br:
                    try:
                        test.bitrate = int(icy_br)
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
        test.error_message = str(e)[:50]
    
    test.tested_at = datetime.now().isoformat()
    return test

async def test_stream_get(session: aiohttp.ClientSession, test: StreamTest) -> StreamTest:
    if test.status not in ["head_rejected", "http_error", "error"]:
        return test
    
    try:
        async with session.get(
            test.url,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"Origin": "http://localhost:3000", "User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            ssl=False
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
                
                # Verify it's actually audio
                chunk = await response.content.read(1024)
                if len(chunk) < 100:
                    test.status = "empty_response"
                    test.error_message = "Empty response"
            else:
                test.status = "http_error"
                test.error_message = f"HTTP {response.status} (GET)"
    except Exception as e:
        if test.status in ["head_rejected", "http_error"]:
            test.status = "error"
            test.error_message = str(e)[:50]
    
    return test

async def validate_all_streams():
    print(f"Testing {len(FALLBACK_STREAMS)} fallback streams...")
    
    async with aiohttp.ClientSession() as session:
        tests = await asyncio.gather(*[test_stream(session, s) for s in FALLBACK_STREAMS])
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
    print("FALLBACK STREAM VALIDATION RESULTS")
    print("="*80)
    
    print(f"\n✅ WORKS IN BROWSER ({len(categories['working_browser'])}):")
    for test in categories["working_browser"]:
        bitrate = f"{test.bitrate}kbps" if test.bitrate else "?kbps"
        print(f"  🌐 {test.station_name:30} | {bitrate:8}")
    
    print(f"\n🔒 NEEDS CORS PROXY ({len(categories['working_proxy'])}):")
    for test in categories["working_proxy"]:
        print(f"  🔒 {test.station_name:30} | CORS: {test.cors_origin or 'none'}")
    
    print(f"\n❌ UNAVAILABLE ({len(categories['unavailable'])}):")
    for test in categories["unavailable"]:
        print(f"  ❌ {test.station_name:30} | {test.error_message[:35]}")
    
    print(f"\n⏱️ TIMEOUT ({len(categories['timeout'])}):")
    for test in categories["timeout"]:
        print(f"  ⏱️  {test.station_name:30}")
    
    print(f"\n❓ NEEDS INVESTIGATION ({len(categories['needs_investigation'])}):")
    for test in categories["needs_investigation"]:
        print(f"  ❓ {test.station_name:30} | {test.status}")
    
    print("\n" + "="*80)
    total = len(tests)
    working = len(categories['working_browser'])
    proxy = len(categories['working_proxy'])
    dead = len(categories['unavailable']) + len(categories['timeout'])
    
    print(f"Total tested:     {total}")
    print(f"Browser-ready:    {working} ({working/total*100:.1f}%)")
    print(f"Needs proxy:      {proxy} ({proxy/total*100:.1f}%)")
    print(f"Dead/unreachable: {dead} ({dead/total*100:.1f}%)")

def save_results(tests: List[StreamTest], filename: str = "fallback_results.json"):
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
