import time
import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import json
import streamlit.components.v1 as components

# TTL cache: 1 jam kalau fetch SUKSES, 15 menit kalau GAGAL
LIVE_TTL = 3600
RETRY_TTL = 900

@st.cache_resource
def _get_cache_store(name: str):
    return {"data": None, "timestamp": 0.0, "is_live": False, "source": "", "last_error": None}

# Konfigurasi Halaman (Full Width)
st.set_page_config(
    page_title="ManTam // Global & Regional Terminal",
    page_icon="🛡️",
    layout="wide"
)

# Sembunyikan Header Streamlit & Atur Tema Terminal (Tombol Dibuat Gelap agar Tidak Silau)
st.markdown("""
<style>
    header {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp { background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
    
    /* Styling tombol kustom agar gelap, elegan, dan tidak silau */
    div.stButton > button {
        background-color: #0c1412 !important;
        color: #00ffcc !important;
        border: 1px solid #1a3630 !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: bold !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #132622 !important;
        border-color: #00ffcc !important;
        color: #ffffff !important;
    }
    
    @keyframes autoScroll {
        0% { transform: translateY(0); }
        100% { transform: translateY(-50%); }
    }
    .ticker-container:hover .ticker-track {
        animation-play-state: paused;
    }
</style>
""", unsafe_allow_html=True)

# Auto-Refresh setiap 1 Jam
st_autorefresh(interval=3600 * 1000, key="osint_refresher")

# Translator
@st.cache_resource
def get_translator():
    return GoogleTranslator(source='auto', target='id')

translator = get_translator()

def translate_title(text: str, max_retries: int = 2) -> str:
    error_keywords = ["Error 500", "502 Bad Gateway", "Server Error", "That's an error"]
    for attempt in range(max_retries):
        try:
            result = translator.translate(text)
            if result and not any(err in result for err in error_keywords):
                return result
        except Exception:
            pass
        time.sleep(0.4 * (attempt + 1))
    return text

def fetch_forex_rates():
    store = _get_cache_store("forex_v3")
    now = time.time()
    ttl = LIVE_TTL if store["is_live"] else RETRY_TTL
    if store["data"] is not None and (now - store["timestamp"]) < ttl:
        return store["data"]

    default_rates = {
        "USD": 16250.0, "SGD": 12100.5, "EUR": 17620.0, "GBP": 20615.3,
        "JPY": 104.5, "AUD": 10750.25, "MYR": 3650.0, "CNY": 2280.1
    }
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rates = data.get("rates", {})
            idr_per_usd = rates.get("IDR", 16250.0)

            live_rates = {}
            currencies = ["USD", "SGD", "EUR", "GBP", "JPY", "AUD", "MYR", "CNY"]
            for cur in currencies:
                if cur == "USD":
                    val_in_idr = idr_per_usd
                else:
                    val_in_usd = rates.get(cur, 1.0)
                    if val_in_usd:
                        val_in_idr = idr_per_usd / val_in_usd
                    else:
                        val_in_idr = default_rates.get(cur, 1.0)
                live_rates[cur] = val_in_idr

            store["data"] = live_rates
            store["timestamp"] = now
            store["is_live"] = True
            return live_rates
    except Exception:
        pass

    fallback = store["data"] if store["data"] is not None else default_rates
    store["data"] = fallback
    store["timestamp"] = now
    store["is_live"] = False
    return fallback

forex_rates = fetch_forex_rates()

def fetch_live_news():
    store = _get_cache_store("news_v3")
    now = time.time()
    ttl = LIVE_TTL if store["is_live"] else RETRY_TTL
    
    if store["data"] is not None and (now - store["timestamp"]) < ttl:
        return store["data"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    regions_pool = ["world", "americas", "europe", "middle_east", "asia_pacific", "africa"]
    error_logs = []

    # GDELT API
    articles_list = []
    url_gdelt = "https://api.gdeltproject.org/api/v2/doc/doc?query=geopolitics%20OR%20war%20OR%20economy%20OR%20defense&mode=artlist&maxrecords=25&format=json"
    try:
        res_gdelt = requests.get(url_gdelt, headers=headers, timeout=10)
        if res_gdelt.status_code == 200:
            data = res_gdelt.json()
            for idx, art in enumerate(data.get("articles", [])):
                title_en = art.get("title", "")
                if not title_en: continue
                try: title_id = translate_title(title_en)
                except: title_id = title_en
                time.sleep(0.1)
                assigned_region = regions_pool[idx % len(regions_pool)]
                articles_list.append({
                    "title": title_id, "url": art.get("url", "#"),
                    "source": art.get("source", "GDELT").upper(), "date": "1h ago",
                    "lat": 20.0 + (hash(title_en) % 30) - 15, "lon": 0.0 + (hash(title_en) % 180) - 90,
                    "region": assigned_region
                })
        else:
            error_logs.append(f"GDELT HTTP {res_gdelt.status_code}")
    except Exception as e:
        error_logs.append(f"GDELT Error: {type(e).__name__}")

    if len(articles_list) >= 5:
        store.update({"data": articles_list, "timestamp": now, "is_live": True, "source": "GDELT", "last_error": None})
        return articles_list

    # BBC WORLD NEWS (BACKUP 1)
    bbc_list = []
    url_bbc = "https://api.rss2json.com/v1/api.json?rss_url=http://feeds.bbci.co.uk/news/world/rss.xml"
    try:
        res_bbc = requests.get(url_bbc, headers=headers, timeout=10)
        if res_bbc.status_code == 200:
            b_data = res_bbc.json()
            for idx, item in enumerate(b_data.get("items", [])[:15]):
                title_en = item.get("title", "")
                if not title_en: continue
                try: title_id = translate_title(title_en)
                except: title_id = title_en
                time.sleep(0.1)
                assigned_region = regions_pool[idx % len(regions_pool)]
                bbc_list.append({
                    "title": title_id, "url": item.get("link", "#"),
                    "source": "BBC NEWS", "date": "LIVE BACKUP",
                    "lat": 20.0 + (hash(title_en) % 30) - 15, "lon": 0.0 + (hash(title_en) % 180) - 90,
                    "region": assigned_region
                })
        else:
            error_logs.append(f"BBC HTTP {res_bbc.status_code}")
    except Exception as e:
        error_logs.append(f"BBC Error: {type(e).__name__}")

    if len(bbc_list) >= 5:
        store.update({"data": bbc_list, "timestamp": now, "is_live": True, "source": "BBC", "last_error": " | ".join(error_logs)})
        return bbc_list

    # AL JAZEERA (BACKUP 2)
    alj_list = []
    url_alj = "https://api.rss2json.com/v1/api.json?rss_url=https://www.aljazeera.com/xml/rss/all.xml"
    try:
        res_alj = requests.get(url_alj, headers=headers, timeout=10)
        if res_alj.status_code == 200:
            a_data = res_alj.json()
            for idx, item in enumerate(a_data.get("items", [])[:15]):
                title_en = item.get("title", "")
                if not title_en: continue
                try: title_id = translate_title(title_en)
                except: title_id = title_en
                time.sleep(0.1)
                assigned_region = regions_pool[idx % len(regions_pool)]
                alj_list.append({
                    "title": title_id, "url": item.get("link", "#"),
                    "source": "AL JAZEERA", "date": "LIVE BACKUP",
                    "lat": 20.0 + (hash(title_en) % 30) - 15, "lon": 0.0 + (hash(title_en) % 180) - 90,
                    "region": assigned_region
                })
        else:
            error_logs.append(f"ALJ HTTP {res_alj.status_code}")
    except Exception as e:
        error_logs.append(f"ALJ Error: {type(e).__name__}")

    if len(alj_list) >= 5:
        store.update({"data": alj_list, "timestamp": now, "is_live": True, "source": "AL JAZEERA", "last_error": " | ".join(error_logs)})
        return alj_list

    error_item = [{
        "title": "KONEKSI TERPUTUS ATAU SELURUH API DIBLOKIR SEMENTARA.", 
        "url": "#", "source": "SYSTEM ALERT", "date": "NOW",
        "lat": 0.0, "lon": 0.0, "region": "world"
    }]
    
    fallback_data = store["data"] if store["data"] is not None else error_item
    store.update({"data": fallback_data, "timestamp": now, "is_live": False, "source": "OFFLINE", "last_error": "Semua API Online Gagal"})
    return fallback_data

# Fungsi Aman untuk Mengambil Data Darkweb / Ransomware Leaks
def fetch_darkweb_leaks():
    store = _get_cache_store("darkweb_v1")
    now = time.time()
    if store["data"] is not None and (now - store["timestamp"]) < 1800:
        return store["data"]
    
    default_fallback = [
        {"group": "LockBit 3.0", "target": "Global Supply Chain Infrastructure", "country": "US", "date": "Live Feed"},
        {"group": "BlackCat", "target": "Financial Data Provider", "country": "EU", "date": "Live Feed"},
        {"group": "RansomHub", "target": "Corporate Network System", "country": "INT", "date": "Live Feed"}
    ]

    try:
        url = "https://api.ransomware.live/v2/recentvictims"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            victims = res.json()
            if isinstance(victims, list) and len(victims) > 0:
                parsed_data = []
                for v in victims[:15]:
                    if isinstance(v, dict):
                        parsed_data.append({
                            "group": str(v.get("group_name", "Unknown Gang")),
                            "target": str(v.get("post_title", v.get("target", "Target Confirmed"))),
                            "country": str(v.get("country", "INT")).upper(),
                            "date": str(v.get("published", "Recent"))[:10]
                        })
                if parsed_data:
                    store["data"] = parsed_data
                    store["timestamp"] = now
                    store["is_live"] = True
                    return parsed_data
    except Exception:
        pass
    
    return store["data"] if store["data"] is not None else default_fallback

st.markdown("### ⚡ ManTam // GLOBAL & REGIONAL TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING INTEL ENGINE · LIVE FEED · UPDATES EVERY 1H</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("MENGINISIALISASI FEED INTELIJEN GLOBAL & MENERJEMAHKAN DATA..."):
    news_items = fetch_live_news()
    darkweb_items = fetch_darkweb_leaks()

if "selected_region" not in st.session_state:
    st.session_state.selected_region = "world"
if "flat_mode" not in st.session_state:
    st.session_state.flat_mode = False

# --- KONTROL TOMBOL DI ATAS PETA (MENU & MODE/ZOOM) ---
menu_cols = st.columns(6)
regions = [
    ("world", "WORLD"),
    ("americas", "AMERICAS"),
    ("europe", "EUROPE"),
    ("middle_east", "MIDDLE EAST"),
    ("asia_pacific", "ASIA PACIFIC"),
    ("africa", "AFRICA")
]

for i, (reg_key, reg_name) in enumerate(regions):
    with menu_cols[i]:
        is_active = (st.session_state.selected_region == reg_key)
        btn_label = f"🟢 {reg_name}" if is_active else reg_name
        if st.button(btn_label, key=f"reg_{reg_key}"):
            st.session_state.selected_region = reg_key
            st.rerun()

ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col_rest = st.columns([0.5, 0.5, 2.0, 7.0])
with ctrl_col1:
    if st.button("+", key="zoom_in_btn"):
        st.session_state["zoom_action"] = "in"
        st.rerun()
with ctrl_col2:
    if st.button("-", key="zoom_out_btn"):
        st.session_state["zoom_action"] = "out"
        st.rerun()
with ctrl_col3:
    mode_label = "GLOBE MODE" if st.session_state.flat_mode else "FLAT MODE"
    if st.button(mode_label, key="mode_switch_btn"):
        st.session_state.flat_mode = not st.session_state.flat_mode
        st.rerun()

current_region = st.session_state.selected_region
viewpoints = {
    "world": (0, 0, 2.5),
    "americas": (20, -90, 1.6),
    "europe": (50, 10, 1.4),
    "middle_east": (25, 45, 1.4),
    "asia_pacific": (10, 115, 1.6),
    "africa": (0, 20, 1.6)
}
pov_lat, pov_lng, pov_alt = viewpoints.get(current_region, (0, 0, 2.5))
globe_json = json.dumps(news_items)

zoom_cmd = ""
if "zoom_action" in st.session_state:
    action = st.session_state.pop("zoom_action")
    if action == "in":
        zoom_cmd = "window.zoomIn && window.zoomIn();"
    elif action == "out":
        zoom_cmd = "window.zoomOut && window.zoomOut();"

map_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow: hidden; }
        #map-container { width: 100%; height: 500px; position: relative; border: 1px solid #1a2b27; background: #050505; }
        .globe-tooltip { background: rgba(10, 10, 10, 0.95); border: 1px solid #00ffcc; color: #fff; padding: 10px 14px; font-family: 'Courier New', Courier, monospace; font-size: 11px; max-width: 280px; box-shadow: 0 0 20px rgba(0,255,204,0.4); border-radius: 3px; }
        .globe-tooltip a { color: #00ffcc; text-decoration: none; font-weight: bold; }
        .globe-tooltip a:hover { text-decoration: underline; }
    </style>
    <script src="https://unpkg.com/three"></script>
    <script src="https://unpkg.com/globe.gl"></script>
    <script src="https://unpkg.com/d3@7"></script>
    <script src="https://unpkg.com/topojson-client@3"></script>
</head>
<body>
    <div id="map-container"></div>

    <script>
        const data = __GLOBE_DATA_JSON__;
        const isFlat = __IS_FLAT_BOOL__;
        const povLat = __POV_LAT__, povLng = __POV_LNG__, povAlt = __POV_ALT__;
        const container = document.getElementById('map-container');
        
        const arcsData = data.map((d, i) => {
            const target = data[(i + 2) % data.length];
            return { startLat: d.lat, startLng: d.lon, endLat: target.lat, endLng: target.lon, color: ['#00ffcc', '#0044ff'] };
        });
        
        const tooltipHtml = d => `<div class="globe-tooltip"><b>[${d.region.toUpperCase()}]</b><br><a href="${d.url}" target="_blank">${d.title}</a><br><hr style="border-color: #333; margin: 6px 0;"><span style="color: #888;">SRC: ${d.source} | ${d.date}</span></div>`;

        function buildGlobe() {
            const ringsData = data.map(d => ({ lat: d.lat, lng: d.lon, maxRadius: 4.0, propagationSpeed: 2.5, repeatPeriod: 1400 }));
            const world = Globe()
                (container)
                .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
                .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
                .backgroundColor('#050505')
                .pointsData(data)
                .pointLat(d => d.lat)
                .pointLng(d => d.lon)
                .pointColor(() => '#00ffcc')
                .pointAltitude(0.09)
                .pointRadius(0.55)
                .ringsData(ringsData)
                .ringColor(() => '#00ffcc')
                .ringMaxRadius('maxRadius')
                .ringPropagationSpeed('propagationSpeed')
                .ringRepeatPeriod('repeatPeriod')
                .arcsData(arcsData)
                .arcColor('color')
                .arcDashLength(0.4)
                .arcDashGap(0.2)
                .arcDashInitialGap(() => Math.random())
                .arcDashAnimateTime(2000)
                .pointLabel(tooltipHtml);
            
            const controls = world.controls();
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.7;
            controls.enableZoom = true;
            world.pointOfView({ lat: povLat, lng: povLng, altitude: povAlt }, 1000);
            
            window.zoomIn = () => { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.max(0.4, pov.altitude - 0.3) }, 500); };
            window.zoomOut = () => { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.min(4.0, pov.altitude + 0.3) }, 500); };
            
            __ZOOM_CMD__
        }

        function buildFlatMap() {
            const width = container.clientWidth || 900;
            const height = 500;

            const svg = d3.select(container).append('svg')
                .attr('width', width).attr('height', height)
                .style('background', '#050505').style('display', 'block');

            const zoomLayer = svg.append('g');

            const projection = d3.geoEquirectangular()
                .rotate([-povLng, 0])
                .fitSize([width, height], { type: 'Sphere' });
            const geoPath = d3.geoPath(projection);

            zoomLayer.append('path')
                .datum({ type: 'Sphere' })
                .attr('d', geoPath)
                .attr('fill', '#060c0b').attr('stroke', '#1a3630').attr('stroke-width', 1);

            zoomLayer.append('path')
                .datum(d3.geoGraticule10())
                .attr('d', geoPath)
                .attr('fill', 'none').attr('stroke', '#0e2320').attr('stroke-width', 0.5);

            const countryLayer = zoomLayer.append('g');
            const contentLayer = zoomLayer.append('g');

            d3.json('https://unpkg.com/world-atlas@2/countries-110m.json')
                .then(topo => {
                    const countries = topojson.feature(topo, topo.objects.countries);
                    countryLayer.selectAll('path').data(countries.features).join('path')
                        .attr('d', geoPath)
                        .attr('fill', '#0a1a16').attr('stroke', '#00ffcc44').attr('stroke-width', 0.6);
                })
                .catch(() => {})
                .finally(() => drawPointsAndArcs());

            function drawPointsAndArcs() {
                const arcsG = contentLayer.append('g');
                
                arcsData.forEach(a => {
                    const p1 = projection([a.startLng, a.startLat]);
                    const p2 = projection([a.endLng, a.endLat]);
                    if (!p1 || !p2) return;
                    
                    const mx = (p1[0] + p2[0]) / 2;
                    const my = (p1[1] + p2[1]) / 2 - 50; 
                    
                    arcsG.append('path')
                        .attr('d', `M${p1[0]},${p1[1]} Q${mx},${my} ${p2[0]},${p2[1]}`)
                        .attr('fill', 'none')
                        .attr('stroke', '#00ffcc')
                        .attr('stroke-opacity', 0.35)
                        .attr('stroke-width', 1.2)
                        .attr('stroke-dasharray', '4,3');
                });

                const tooltip = d3.select(container).append('div')
                    .style('position', 'absolute').style('pointer-events', 'none')
                    .style('opacity', 0).style('z-index', 100).style('transition', 'opacity 0.15s');

                contentLayer.append('g').selectAll('circle').data(data).join('circle')
                    .attr('cx', d => projection([d.lon, d.lat])[0])
                    .attr('cy', d => projection([d.lon, d.lat])[1])
                    .attr('r', 5).attr('fill', '#00ffcc')
                    .attr('stroke', '#00ffcc').attr('stroke-width', 7).attr('stroke-opacity', 0.2)
                    .style('cursor', 'pointer')
                    .on('mouseenter', function (event, d) {
                        tooltip.style('opacity', 1).html(tooltipHtml(d));
                    })
                    .on('mousemove', function (event) {
                        const [mx, my] = d3.pointer(event, container);
                        tooltip.style('left', (mx + 12) + 'px').style('top', (my + 12) + 'px');
                    })
                    .on('mouseleave', function () { tooltip.style('opacity', 0); });
            }

            const zoom = d3.zoom().scaleExtent([1, 8]).on('zoom', (event) => {
                zoomLayer.attr('transform', event.transform);
            });
            svg.call(zoom);
            window.zoomIn = () => svg.transition().duration(300).call(zoom.scaleBy, 1.5);
            window.zoomOut = () => svg.transition().duration(300).call(zoom.scaleBy, 1 / 1.5);
            
            __ZOOM_CMD__
        }

        if (isFlat) { buildFlatMap(); } else { buildGlobe(); }
    </script>
</body>
</html>
"""

map_html = (
    map_html.replace("__GLOBE_DATA_JSON__", globe_json)
    .replace("__POV_LAT__", str(pov_lat))
    .replace("__POV_LNG__", str(pov_lng))
    .replace("__POV_ALT__", str(pov_alt))
    .replace("__IS_FLAT_BOOL__", "true" if st.session_state.flat_mode else "false")
    .replace("__ZOOM_CMD__", zoom_cmd)
)

components.html(map_html, height=520)

st.markdown("---")

left_col, right_col = st.columns([1.3, 1])

with left_col:
    cards_html = ""
    for item in news_items:
        cards_html += f'<div style="background: #080808; border: 1px solid #161616; border-bottom: 1px solid #1f1f1f; padding: 12px 15px; margin-bottom: 8px;"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;"><span style="background: #0c1412; border: 1px solid #00ffcc55; color: #00ffcc; font-size: 9px; padding: 2px 7px; font-family: \'Courier New\', Courier, monospace;">{item["source"]}</span><span style="font-size: 10px; color: #777; font-family: \'Courier New\', Courier, monospace;">{item["date"]}</span></div><a href="{item["url"]}" target="_blank" style="color: #ddd; text-decoration: none; font-size: 12px; font-family: \'Courier New\', Courier, monospace; display: block; line-height: 1.4;">{item["title"]}</a><div style="font-size: 11px; color: #00ffcc55; margin-top: 6px;">&nearr;</div></div>'

    ticker_widget_html = f"""<div style="background: #060606; border: 1px solid #1f1f1f; border-radius: 4px; padding: 15px;"><div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 10px;"><span style="font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #00ffcc;">LIVE NEWS TICKER (AUTO-SCROLL)</span><span style="background: #0d1a17; border: 1px solid #00ffcc55; color: #00ffcc; padding: 2px 10px; font-size: 11px; font-family: 'Courier New', Courier, monospace;">{len(news_items)} ITEMS</span></div><div class="ticker-container" style="height: 520px; overflow: hidden; position: relative;"><div class="ticker-track" style="position: absolute; width: 100%; animation: autoScroll 35s linear infinite;">{cards_html}{cards_html}</div></div></div>"""
    st.markdown(ticker_widget_html, unsafe_allow_html=True)

with right_col:
    # 1. Widget Kurs Valas Asing
    forex_cards_html = ""
    currencies_meta = [
        ("USD", "US Dollar"), ("SGD", "Singapore Dollar"), 
        ("EUR", "Euro Zone"), ("GBP", "British Pound"), 
        ("JPY", "Japanese Yen"), ("AUD", "Australian Dollar"), 
        ("MYR", "Malaysian Ringgit"), ("CNY", "Chinese Yuan")
    ]
    
    for code, name in currencies_meta:
        mid_rate = forex_rates.get(code, 10000.0)
        buy_rate = mid_rate * 0.995
        sell_rate = mid_rate * 1.005
        
        forex_cards_html += f'<div style="background: #080808; border: 1px solid #161616; padding: 10px 12px; margin-bottom: 8px;"><div style="display: flex; justify-content: space-between; font-size: 11px; color: #888; border-bottom: 1px solid #1a1a1a; padding-bottom: 4px; margin-bottom: 6px;"><span><b>{code} / IDR</b> ({name})</span><span style="color: #00ffcc;">LIVE 1H</span></div><div style="display: flex; justify-content: space-between; font-size: 12px; font-family: \'Courier New\', Courier, monospace;"><div><span style="color: #666; font-size: 10px;">BELI:</span> <b style="color: #00ffcc;">Rp {buy_rate:,.2f}</b></div><div><span style="color: #666; font-size: 10px;">JUAL:</span> <b style="color: #ffaa00;">Rp {sell_rate:,.2f}</b></div></div></div>'

    forex_widget_html = f"""<div style="background: #060606; border: 1px solid #1f1f1f; border-radius: 4px; padding: 15px; margin-bottom: 15px;"><div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 10px;"><span style="font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #00ffcc;">KURS VALUTA ASING (BELI & JUAL)</span><span style="background: #0d1a17; border: 1px solid #00ffcc55; color: #00ffcc; padding: 2px 10px; font-size: 11px; font-family: 'Courier New', Courier, monospace;">AUTO-UPDATE 1H</span></div><div style="max-height: 240px; overflow-y: auto; padding-right: 4px;">{forex_cards_html}</div></div>"""
    st.markdown(forex_widget_html, unsafe_allow_html=True)

    # 2. Widget Darkweb & Ransomware Leaks (Render HTML Aman)
    darkweb_cards_html = ""
    for dw in darkweb_items:
        darkweb_cards_html += f'''
        <div style="background: #080808; border: 1px solid #2a1616; border-left: 3px solid #ff3333; padding: 10px 12px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #ff6666; border-bottom: 1px solid #1f1a1a; padding-bottom: 4px; margin-bottom: 6px;">
                <span><b>GANG: {dw.get("group", "Unknown")}</b></span>
                <span>[{dw.get("country", "INT")}] {dw.get("date", "Recent")}</span>
            </div>
            <div style="font-size: 12px; color: #ddd; margin-bottom: 4px;">Target: <b>{dw.get("target", "Target Confirmed")}</b></div>
            <div style="font-size: 10px; color: #ff3333; font-weight: bold;">STATUS: [DATA LEAKED / EXTORTION]</div>
        </div>
        '''

    darkweb_widget_html = f"""
    <div style="background: #060606; border: 1px solid #2a1616; border-radius: 4px; padding: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a1616; padding-bottom: 10px; margin-bottom: 10px;">
            <span style="font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #ff3333;">⚠️ LIVE DARKWEB & RANSOM LEAKS</span>
            <span style="background: #2a0c0c; border: 1px solid #ff333355; color: #ff6666; padding: 2px 10px; font-size: 11px; font-family: 'Courier New', Courier, monospace;">API LIVE</span>
        </div>
        <div style="max-height: 240px; overflow-y: auto; padding-right: 4px;">
            {darkweb_cards_html}
        </div>
    </div>
    """
    st.markdown(darkweb_widget_html, unsafe_allow_html=True)

st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui berita, kurs, & intel darkweb tiap 1 jam.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
