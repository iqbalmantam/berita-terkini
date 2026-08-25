import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import json
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

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
    {
        "title": "Canada walked away from Trump. Could the EU ever do the same?",
        "url": "https://www.euronews.com",
        "source": "EURONEWS",
        "date": "2h ago",
        "lat": 50.8503,
        "lon": 4.3517,
        "region": "europe"
    },
    {
        "title": "Indonesians brave choking smoke to pray for rain as country battles wildfires",
        "url": "https://www.npr.org",
        "source": "NPR",
        "date": "2h ago",
        "lat": -0.7893,
        "lon": 113.9213,
        "region": "asia_pacific"
    },
    {
        "title": "Two US carrier groups in Middle East strain navy resources",
        "url": "https://www.aljazeera.com",
        "source": "AL JAZEERA",
        "date": "2h ago",
        "lat": 25.276987,
        "lon": 55.296249,
        "region": "middle_east"
    },
    {
        "title": "The UK will help Ukraine make long-range missiles by sharing classified tech information",
        "url": "https://www.reuters.com",
        "source": "REUTERS",
        "date": "3h ago",
        "lat": 48.3794,
        "lon": 31.1656,
        "region": "europe"
    },
    {
        "title": "New economic measures and tariffs impact trade across the Americas",
        "url": "https://www.bloomberg.com",
        "source": "BLOOMBERG",
        "date": "4h ago",
        "lat": 25.0343,
        "lon": -77.3963,
        "region": "americas"
    },
    {
        "title": "Ceasefire verification mission deploys to eastern DR Congo",
        "url": "https://www.france24.com",
        "source": "FRANCE 24",
        "date": "5h ago",
        "lat": -4.0383,
        "lon": 21.7587,
        "region": "africa"
    }
]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_news():
    articles_list = []
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc?query=geopolitics%20OR%20war%20OR%20economy&mode=artlist&maxrecords=15&format=json"
        response = requests.get(url, timeout=8)
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
    if not articles_list:
        return DEFAULT_OSINT_DATA
    return articles_list + DEFAULT_OSINT_DATA

st.markdown("### ⚡ CRUCIX // GLOBAL & REGIONAL OSINT TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING INTEL ENGINE · LIVE FEED · AUTO-TRANSLATE ACTIVE</span>", unsafe_allow_html=True)

news_items = fetch_live_news()

# Inisialisasi Session State
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "world"
if "flat_mode" not in st.session_state:
    st.session_state.flat_mode = False

st.markdown("<br>", unsafe_allow_html=True)

# Menu Navigasi Wilayah & Tombol Flat Mode di Atas Peta (7 Kolom)
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

# Filter berita berdasarkan wilayah
if current_region == "world":
    filtered_news = news_items
    pov_lat, pov_lng, pov_alt = 0, 0, 2.5
    map_center = [20.0, 0.0]
    map_zoom = 2
else:
    filtered_news = [item for item in news_items if item["region"] == current_region]
    if not filtered_news:
        filtered_news = news_items
    viewpoints = {
        "americas": (20, -90, 1.6, [20.0, -90.0], 3),
        "europe": (50, 10, 1.4, [50.0, 10.0], 4),
        "middle_east": (25, 45, 1.4, [25.0, 45.0], 4),
        "asia_pacific": (10, 115, 1.6, [10.0, 115.0], 3),
        "africa": (0, 20, 1.6, [0.0, 20.0], 3)
    }
    vp = viewpoints.get(current_region, (0, 0, 2.5, [20.0, 0.0], 2))
    pov_lat, pov_lng, pov_alt, map_center, map_zoom = vp[0], vp[1], vp[2], vp[3], vp[4]

globe_json = json.dumps(filtered_news)

# Render Peta: 3D Globe atau 2D Flat Map (Folium) sesuai pilihan Flat Mode
if st.session_state.flat_mode:
    # Mode Peta Datar (Flat Map) menggunakan Folium tema gelap
    m = folium.Map(location=map_center, zoom_start=map_zoom, tiles="CartoDB dark_matter")
    for item in filtered_news:
        popup_html = f"""
        <div style="width: 220px; font-size: 11px; font-family: monospace;">
            <b>[{item['region'].upper()}]</b><br>
            <a href="{item['url']}" target="_blank"><b>{item['title']}</b></a><br>
            <hr style="margin: 5px 0;">
            <span style="color: gray;">SRC: {item['source']} | {item['date']}</span>
        </div>
        """
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="darkred", icon="info-sign")
        ).add_to(m)
    st_folium(m, width="100%", height=500)
else:
    # Mode Bola Dunia 3D (Globe 3D)
    globe_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow: hidden; }
            #globe-container { width: 100%; height: 500px; position: relative; }
            .globe-tooltip {
                background: rgba(10, 10, 10, 0.95);
                border: 1px solid #00ffcc;
                color: #fff;
                padding: 10px 14px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 11px;
                max-width: 280px;
                box-shadow: 0 0 20px rgba(0,255,204,0.4);
                border-radius: 3px;
            }
            .globe-tooltip a { color: #00ffcc; text-decoration: none; font-weight: bold; }
            .globe-tooltip a:hover { text-decoration: underline; }
        </style>
        <script src="https://unpkg.com/three"></script>
        <script src="https://unpkg.com/globe.gl"></script>
    </head>
    <body>
        <div id="globe-container"></div>
        <script>
            const data = __GLOBE_DATA_JSON__;

            const ringsData = data.map(d => ({
                lat: d.lat,
                lng: d.lon,
                maxRadius: 4.0,
                propagationSpeed: 2.5,
                repeatPeriod: 1400
            }));

            const arcsData = data.map((d, i) => {
                const target = data[(i + 2) % data.length];
                return {
                    startLat: d.lat,
                    startLng: d.lon,
                    endLat: target.lat,
                    endLng: target.lon,
                    color: ['#00ffcc', '#0044ff']
                };
            });

            const world = Globe()
                (document.getElementById('globe-container'))
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
                .pointLabel(d => `
                    <div class="globe-tooltip">
                        <b>[\${d.region.toUpperCase()}]</b><br>
                        <a href="\${d.url}" target="_blank">\${d.title}</a><br>
                        <hr style="border-color: #333; margin: 6px 0;">
                        <span style="color: #888;">SRC: \${d.source} | \${d.date}</span>
                    </div>
                `);

            const controls = world.controls();
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.7;
            controls.enableZoom = true;

            world.pointOfView({ lat: __POV_LAT__, lng: __POV_LNG__, altitude: __POV_ALT__ }, 1000);
        </script>
    </body>
    </html>
    """
    globe_html = (
        globe_html.replace("__GLOBE_DATA_JSON__", globe_json)
        .replace("__POV_LAT__", str(pov_lat))
        .replace("__POV_LNG__", str(pov_lng))
        .replace("__POV_ALT__", str(pov_alt))
    )
    components.html(globe_html, height=520)

# Live News Ticker & Feed di Bawah Peta
st.markdown("---")
st.markdown(f"#### 📡 LIVE NEWS TICKER & INTEL FEED ({current_region.upper()}) — {len(filtered_news)} ITEMS")

cols = st.columns(2)
for idx, item in enumerate(filtered_news):
    col_target = cols[idx % 2]
    with col_target:
        st.markdown(f"""
        <div style="background: rgba(12, 12, 12, 0.9); border: 1px solid #1f1f1f; border-left: 2px solid #00ffcc; padding: 12px; margin-bottom: 12px; border-radius: 3px;">
            <div style="font-size: 10px; color: #888; margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span><b>{item['source']}</b></span>
                <span>{item['date']}</span>
            </div>
            <a href="{item['url']}" target="_blank" style="color: #fff; text-decoration: none; font-size: 12px; line-height: 1.4; display: block;">{item['title']}</a>
        </div>
        """, unsafe_allow_html=True)

# Footer & Watermark
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui data tiap 1 jam via GDELT & Live Feed.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
