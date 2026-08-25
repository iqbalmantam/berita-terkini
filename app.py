import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import json
import streamlit.components.v1 as components

# Konfigurasi Halaman (Full Width)
st.set_page_config(
    page_title="CRUCIX // Global & Regional OSINT Terminal",
    page_icon="🛡️",
    layout="wide"
)

# Sembunyikan Header Streamlit / Logo GitHub / Menu secara Total via CSS
st.markdown("""
<style>
    header {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp { background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
</style>
""", unsafe_allow_html=True)

# Auto-Refresh setiap 1 Jam
st_autorefresh(interval=3600 * 1000, key="osint_refresher")

# Translator
@st.cache_resource
def get_translator():
    return GoogleTranslator(source='auto', target='id')

translator = get_translator()

# Fallback Data OSINT
DEFAULT_OSINT_DATA = [
    {"title": "Canada walked away from Trump. Could the EU ever do the same?", "url": "https://www.euronews.com", "source": "EURONEWS", "date": "2h ago", "lat": 50.8503, "lon": 4.3517, "region": "europe"},
    {"title": "Indonesians brave choking smoke to pray for rain as country battles wildfires", "url": "https://www.npr.org", "source": "NPR", "date": "2h ago", "lat": -0.7893, "lon": 113.9213, "region": "asia_pacific"},
    {"title": "Two US carrier groups in Middle East strain navy resources", "url": "https://www.aljazeera.com", "source": "AL JAZEERA", "date": "2h ago", "lat": 25.276987, "lon": 55.296249, "region": "middle_east"},
    {"title": "The UK will help Ukraine make long-range missiles by sharing classified tech information", "url": "https://www.reuters.com", "source": "REUTERS", "date": "3h ago", "lat": 48.3794, "lon": 31.1656, "region": "europe"},
    {"title": "New economic measures and tariffs impact trade across the Americas", "url": "https://www.bloomberg.com", "source": "BLOOMBERG", "date": "4h ago", "lat": 25.0343, "lon": -77.3963, "region": "americas"},
    {"title": "Ceasefire verification mission deploys to eastern DR Congo", "url": "https://www.france24.com", "source": "FRANCE 24", "date": "5h ago", "lat": -4.0383, "lon": 21.7587, "region": "africa"},
    {"title": "Global supply chain pressures rise amid new maritime trade route restrictions", "url": "https://www.reuters.com", "source": "REUTERS", "date": "1h ago", "lat": 12.35, "lon": 43.23, "region": "middle_east"},
    {"title": "Central banks evaluate digital currency frameworks amid inflation shifts", "url": "https://www.bloomberg.com", "source": "BLOOMBERG", "date": "2h ago", "lat": 51.5074, "lon": -0.1278, "region": "europe"},
    {"title": "South China Sea naval exercises prompt diplomatic responses across ASEAN", "url": "https://www.channelnewsasia.com", "source": "CNA", "date": "3h ago", "lat": 12.0, "lon": 114.0, "region": "asia_pacific"},
    {"title": "Latin American lithium corridor projects attract new multinational investments", "url": "https://www.mercopress.com", "source": "MERCOPRESS", "date": "4h ago", "lat": -22.9068, "lon": -43.1729, "region": "americas"}
]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_news():
    articles_list = []
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc?query=geopolitics%20OR%20war%20OR%20economy%20OR%20defense&mode=artlist&maxrecords=25&format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            regions_pool = ["world", "americas", "europe", "middle_east", "asia_pacific", "africa"]
            for idx, art in enumerate(articles):
                title_en = art.get("title", "")
                if not title_en:
                    continue
                try:
                    title_id = translator.translate(title_en)
                except Exception:
                    title_id = title_en
                assigned_region = regions_pool[idx % len(regions_pool)]
                articles_list.append({
                    "title": title_id,
                    "url": art.get("url", "#"),
                    "source": art.get("source", "OSINT FEED").upper(),
                    "date": "1h ago",
                    "lat": 20.0 + (hash(title_en) % 30) - 15,
                    "lon": 0.0 + (hash(title_en) % 180) - 90,
                    "region": assigned_region
                })
    except Exception:
        pass
    if len(articles_list) < 8:
        return articles_list + DEFAULT_OSINT_DATA
    return articles_list

st.markdown("### ⚡ CRUCIX // GLOBAL & REGIONAL OSINT TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING INTEL ENGINE · LIVE FEED · AUTO-TRANSLATE ACTIVE</span>", unsafe_allow_html=True)

news_items = fetch_live_news()

# Inisialisasi Session State
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "world"
if "flat_mode" not in st.session_state:
    st.session_state.flat_mode = False

st.markdown("<br>", unsafe_allow_html=True)

# Menu Navigasi Wilayah & Flat Mode (7 Kolom)
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    if st.button("WORLD", use_container_width=True):
        st.session_state.selected_region = "world"
with col2:
    if st.button("AMERICAS", use_container_width=True):
        st.session_state.selected_region = "americas"
with col3:
    if st.button("EUROPE", use_container_width=True):
        st.session_state.selected_region = "europe"
with col4:
    if st.button("MIDDLE EAST", use_container_width=True):
        st.session_state.selected_region = "middle_east"
with col5:
    if st.button("ASIA PACIFIC", use_container_width=True):
        st.session_state.selected_region = "asia_pacific"
with col6:
    if st.button("AFRICA", use_container_width=True):
        st.session_state.selected_region = "africa"
with col7:
    flat_label = "FLAT: ON" if st.session_state.flat_mode else "FLAT: OFF"
    if st.button(flat_label, use_container_width=True):
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

map_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow: hidden; }
        #map-container { width: 100%; height: 500px; position: relative; }
        .crucix-controls { position: absolute; top: 15px; left: 15px; z-index: 99; display: flex; flex-direction: column; gap: 4px; }
        .ctrl-row { display: flex; gap: 4px; align-items: center; }
        .crucix-btn { background: #050505; border: 1px solid #00ffcc55; color: #00ffcc; font-family: 'Courier New', Courier, monospace; font-size: 14px; cursor: pointer; text-align: center; display: flex; align-items: center; justify-content: center; width: 38px; height: 38px; font-weight: bold; }
        .crucix-btn:hover { border-color: #00ffcc; background: #00ffcc22; box-shadow: 0 0 8px #00ffccaa; }
        .globe-tooltip { background: rgba(10, 10, 10, 0.95); border: 1px solid #00ffcc; color: #fff; padding: 10px 14px; font-family: 'Courier New', Courier, monospace; font-size: 11px; max-width: 280px; box-shadow: 0 0 20px rgba(0,255,204,0.4); border-radius: 3px; }
        .globe-tooltip a { color: #00ffcc; text-decoration: none; font-weight: bold; }
        .globe-tooltip a:hover { text-decoration: underline; }
    </style>
    <script src="https://unpkg.com/three"></script>
    <script src="https://unpkg.com/globe.gl"></script>
</head>
<body>
    <div id="map-container">
        <div class="crucix-controls">
            <div class="ctrl-row"><button class="crucix-btn" onclick="zoomIn()">+</button></div>
            <div class="ctrl-row"><button class="crucix-btn" onclick="zoomOut()">-</button></div>
        </div>
    </div>
    <script>
        const data = __GLOBE_DATA_JSON__;
        const isFlat = __FLAT_MODE__;
        const ringsData = data.map(d => ({ lat: d.lat, lng: d.lon, maxRadius: 4.0, propagationSpeed: 2.5, repeatPeriod: 1400 }));
        const arcsData = data.map((d, i) => {
            const target = data[(i + 2) % data.length];
            return { startLat: d.lat, startLng: d.lon, endLat: target.lat, endLng: target.lon, color: ['#00ffcc', '#0044ff'] };
        });
        const world = Globe()
            (document.getElementById('map-container'))
            .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
            .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
            .backgroundColor('#050505')
            .showGlobe(!isFlat)
            .showAtmosphere(!isFlat)
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
            .pointLabel(d => `<div class="globe-tooltip"><b>[\${d.region.toUpperCase()}]</b><br><a href="\${d.url}" target="_blank">\${d.title}</b><br><hr style="border-color: #333; margin: 6px 0;"><span style="color: #888;">SRC: \${d.source} | \${d.date}</span></div>`);
        const controls = world.controls();
        controls.autoRotate = !isFlat;
        controls.autoRotateSpeed = 0.7;
        controls.enableZoom = true;
        world.pointOfView({ lat: __POV_LAT__, lng: __POV_LNG__, altitude: __POV_ALT__ }, 1000);
        function zoomIn() { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.max(0.4, pov.altitude - 0.3) }, 500); }
        function zoomOut() { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.min(4.0, pov.altitude + 0.3) }, 500); }
    </script>
</body>
</html>
"""

map_html = (
    map_html.replace("__GLOBE_DATA_JSON__", globe_json)
    .replace("__POV_LAT__", str(pov_lat))
    .replace("__POV_LNG__", str(pov_lng))
    .replace("__POV_ALT__", str(pov_alt))
    .replace("__FLAT_MODE__", "true" if st.session_state.flat_mode else "false")
)

components.html(map_html, height=520)

st.markdown("---")

# Layout 2 Kolom: Kiri = Live News Ticker (Auto-Scroll), Kanan = Kurs Mata Uang terhadap Rupiah (IDR)
left_col, right_col = st.columns([1.3, 1])

with left_col:
    cards_html = ""
    for item in news_items:
        cards_html += f"""
        <div style="background: #080808; border: 1px solid #161616; border-bottom: 1px solid #1f1f1f; padding: 12px 15px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="background: #0c1412; border: 1px solid #00ffcc55; color: #00ffcc; font-size: 9px; padding: 2px 7px; font-family: 'Courier New', Courier, monospace;">{item['source']}</span>
                <span style="font-size: 10px; color: #777; font-family: 'Courier New', Courier, monospace;">{item['date']}</span>
            </div>
            <a href="{item['url']}" target="_blank" style="color: #ddd; text-decoration: none; font-size: 12px; font-family: 'Courier New', Courier, monospace; display: block; line-height: 1.4;">{item['title']}</a>
            <div style="font-size: 11px; color: #00ffcc55; margin-top: 6px;">↗</div>
        </div>
        """

    st.markdown(f"""
    <div style="background: #060606; border: 1px solid #1f1f1f; border-radius: 4px; padding: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 10px;">
            <span style="font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #00ffcc;">LIVE NEWS TICKER (AUTO-SCROLL)</span>
            <span style="background: #0d1a17; border: 1px solid #00ffcc55; color: #00ffcc; padding: 2px 10px; font-size: 11px; font-family: 'Courier New', Courier, monospace;">{len(news_items)} ITEMS</span>
        </div>
        <div class="ticker-container" style="height: 480px; overflow: hidden; position: relative;">
            <div class="ticker-track" style="position: absolute; width: 100%; animation: autoScroll 35s linear infinite;">
                {cards_html}
                {cards_html}
            </div>
        </div>
    </div>
    <style>
    @keyframes autoScroll {{
        0% {{ transform: translateY(0); }}
        100% {{ transform: translateY(-50%); }}
    }}
    .ticker-container:hover .ticker-track {{
        animation-play-state: paused;
    }}
    </style>
    """, unsafe_allow_html=True)

with right_col:
    st.markdown("#### 💱 KURS RUPIAH (IDR) TERHADAP VALUTA ASING")
    st.markdown("""
    <div style="background: #060606; border: 1px solid #1f1f1f; border-radius: 4px; padding: 15px;">
        <div style="border-bottom: 1px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 15px; font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #00ffcc;">
            NILAI TUKAR MATA ASING / IDR
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-family: 'Courier New', Courier, monospace;">
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">USD / IDR</div>
                <div style="font-size: 15px; color: #00ffcc; font-weight: bold; margin-top: 4px;">Rp 16,250.00</div>
                <div style="font-size: 10px; color: #00ffcc88; margin-top: 2px;">▲ +0.15%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">SGD / IDR</div>
                <div style="font-size: 15px; color: #00ffcc; font-weight: bold; margin-top: 4px;">Rp 12,100.50</div>
                <div style="font-size: 10px; color: #00ffcc88; margin-top: 2px;">▲ +0.08%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">EUR / IDR</div>
                <div style="font-size: 15px; color: #ffaa00; font-weight: bold; margin-top: 4px;">Rp 17,620.00</div>
                <div style="font-size: 10px; color: #ffaa0088; margin-top: 2px;">▼ -0.05%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">GBP / IDR</div>
                <div style="font-size: 15px; color: #00ffcc; font-weight: bold; margin-top: 4px;">Rp 20,615.30</div>
                <div style="font-size: 10px; color: #00ffcc88; margin-top: 2px;">▲ +0.21%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">JPY / IDR</div>
                <div style="font-size: 15px; color: #ffaa00; font-weight: bold; margin-top: 4px;">Rp 104.50</div>
                <div style="font-size: 10px; color: #ffaa0088; margin-top: 2px;">▼ -0.18%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">AUD / IDR</div>
                <div style="font-size: 15px; color: #00ffcc; font-weight: bold; margin-top: 4px;">Rp 10,750.25</div>
                <div style="font-size: 10px; color: #00ffcc88; margin-top: 2px;">▲ +0.12%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">MYR / IDR</div>
                <div style="font-size: 15px; color: #00ffcc; font-weight: bold; margin-top: 4px;">Rp 3,650.00</div>
                <div style="font-size: 10px; color: #00ffcc88; margin-top: 2px;">▲ +0.05%</div>
            </div>
            <div style="background: #080808; border: 1px solid #161616; padding: 12px;">
                <div style="font-size: 11px; color: #888;">CNY / IDR</div>
                <div style="font-size: 15px; color: #ffaa00; font-weight: bold; margin-top: 4px;">Rp 2,280.10</div>
                <div style="font-size: 10px; color: #ffaa0088; margin-top: 2px;">▼ -0.03%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer & Watermark
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui data tiap 1 jam via GDELT & Live Feed.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
