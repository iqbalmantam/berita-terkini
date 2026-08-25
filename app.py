import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import json
import streamlit.components.v1 as components

# Konfigurasi Halaman & Responsivitas Mobile (Full Width Tanpa Sidebar)
st.set_page_config(
    page_title="CRUCIX // Global & Regional OSINT Terminal",
    page_icon="🛡️",
    layout="wide"
)

# Auto-Refresh setiap 1 Jam (3600 detik = 3.600.000 milidetik)
st_autorefresh(interval=3600 * 1000, key="osint_refresher")

# Inisialisasi Translator dengan Cache Resource agar stabil
@st.cache_resource
def get_translator():
    return GoogleTranslator(source='auto', target='id')

translator = get_translator()

# Fallback / Baseline Data OSINT Berdasarkan Kategori Wilayah ala Crucix
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

# Fungsi Ambil Data Live GDELT API dengan Fallback Aman
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

                # Distribusikan kategori wilayah secara dinamis
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

# Styling Tema Cyberpunk Dark ala Crucix
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
    h1, h2, h3 { color: #00ffcc; font-family: 'Courier New', Courier, monospace; text-shadow: 0 0 10px rgba(0,255,204,0.4); }
</style>
""", unsafe_allow_html=True)

st.markdown("### ⚡ CRUCIX // GLOBAL & REGIONAL OSINT TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING 3D GLOBE ENGINE · LIVE INTEL FEED · AUTO-TRANSLATE ACTIVE</span>", unsafe_allow_html=True)

with st.spinner("Memuat satelit dan jaringan OSINT global..."):
    news_items = fetch_live_news()

globe_json = json.dumps(news_items)

# HTML Globe 3D Lengkap dengan Navigasi Wilayah, Animasi, dan Filter Berita di Bawahnya
globe_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow-x: hidden; }
        #header-nav { display: flex; gap: 6px; padding: 10px 0; background: #050505; overflow-x: auto; border-bottom: 1px solid #1a1a1a; }
        .nav-btn { background: transparent; border: 1px solid #00ffcc55; color: #00ffcc; padding: 6px 14px; font-family: 'Courier New', Courier, monospace; font-size: 11px; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; transition: all 0.2s; white-space: nowrap; }
        .nav-btn:hover, .nav-btn.active { background: #00ffcc; color: #050505; box-shadow: 0 0 12px #00ffccaa; font-weight: bold; border-color: #00ffcc; }
        #globe-container { width: 100%; height: 500px; position: relative; }
        .ui-controls { position: absolute; top: 15px; left: 15px; z-index: 10; display: flex; gap: 6px; }
        .ctrl-btn { background: rgba(5,5,5,0.85); border: 1px solid #00ffcc66; color: #00ffcc; padding: 6px 12px; font-family: 'Courier New', Courier, monospace; font-size: 11px; cursor: pointer; border-radius: 2px; }
        .ctrl-btn:hover { border-color: #00ffcc; background: #00ffcc22; }
        
        /* Ticker Feed Style ala Crucix di Bawah Peta */
        #news-section { padding: 15px; background: #070707; border-top: 1px solid #1a1a1a; }
        .ticker-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #00ffcc44; padding-bottom: 8px; margin-bottom: 15px; }
        .ticker-title { font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #00ffcc; }
        .ticker-badge { background: #00ffcc22; border: 1px solid #00ffcc; color: #00ffcc; padding: 2px 8px; font-size: 10px; }
        
        .news-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        .news-card { background: rgba(12, 12, 12, 0.9); border: 1px solid #1f1f1f; border-left: 2px solid #00ffcc; padding: 12px; transition: all 0.2s; }
        .news-card:hover { border-color: #00ffcc; box-shadow: 0 0 10px rgba(0,255,204,0.15); }
        .news-meta { font-size: 10px; color: #888; margin-bottom: 6px; display: flex; justify-content: space-between; }
        .news-link { color: #fff; text-decoration: none; font-size: 12px; line-height: 1.4; display: block; }
        .news-link:hover { color: #00ffcc; text-decoration: underline; }

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
    <!-- Menu Kategori Wilayah di Atas Peta -->
    <div id="header-nav">
        <button class="nav-btn active" onclick="filterRegion('world', this)">World</button>
        <button class="nav-btn" onclick="filterRegion('americas', this)">Americas</button>
        <button class="nav-btn" onclick="filterRegion('europe', this)">Europe</button>
        <button class="nav-btn" onclick="filterRegion('middle_east', this)">Middle East</button>
        <button class="nav-btn" onclick="filterRegion('asia_pacific', this)">Asia Pacific</button>
        <button class="nav-btn" onclick="filterRegion('africa', this)">Africa</button>
    </div>

    <!-- Peta 3D -->
    <div id="globe-container">
        <div class="ui-controls">
            <button class="ctrl-btn" onclick="zoomIn()">+</button>
            <button class="ctrl-btn" onclick="zoomOut()">-</button>
            <button class="ctrl-btn" onclick="toggleFlatMode()" id="flat-btn">FLAT MODE: OFF</button>
        </div>
    </div>

    <!-- Live News Ticker & Feed di Bawah Peta -->
    <div id="news-section">
        <div class="ticker-header">
            <span class="ticker-title">LIVE NEWS TICKER & INTEL FEED</span>
            <span class="ticker-badge" id="item-count">ITEMS</span>
        </div>
        <div class="news-grid" id="news-grid-container">
            <!-- Berita akan dimuat dinamis lewat JavaScript -->
        </div>
    </div>

    <script>
        const allData = __GLOBE_DATA_JSON__;

        const ringsData = allData.map(d => ({
            lat: d.lat,
            lng: d.lon,
            maxRadius: 4.0,
            propagationSpeed: 2.5,
            repeatPeriod: 1400
        }));

        const arcsData = allData.map((d, i) => {
            const target = allData[(i + 2) % allData.length];
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
            .pointsData(allData)
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

        // Fungsi Render Berita ke dalam Grid di Bawah Peta
        function renderNews(filteredData) {
            const container = document.getElementById('news-grid-container');
            document.getElementById('item-count').innerText = filteredData.length + " ITEMS";
            container.innerHTML = '';

            filteredData.forEach(item => {
                const card = document.createElement('div');
                card.className = 'news-card';
                card.innerHTML = `
                    <div class="news-meta">
                        <span><b>\${item.source}</b></span>
                        <span>\${item.date}</span>
                    </div>
                    <a href="\${item.url}" target="_blank" class="news-link">\${item.title}</a>
                `;
                container.appendChild(card);
            });
        }

        // Filter berdasarkan Wilayah (World, Americas, Europe, dll.)
        function filterRegion(region, btn) {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            controls.autoRotate = false;

            let filtered = allData;
            if (region !== 'world') {
                filtered = allData.filter(d => d.region === region);
            }

            world.pointsData(filtered);

            const viewpoints = {
                world: { lat: 0, lng: 0, altitude: 2.5 },
                americas: { lat: 20, lng: -90, altitude: 1.6 },
                europe: { lat: 50, lng: 10, altitude: 1.4 },
                middle_east: { lat: 25, lng: 45, altitude: 1.4 },
                asia_pacific: { lat: 10, lng: 115, altitude: 1.6 },
                africa: { lat: 0, lng: 20, altitude: 1.6 }
            };
            if (viewpoints[region]) {
                world.pointOfView(viewpoints[region], 1500);
            }

            renderNews(filtered);
        }

        function zoomIn() {
            const pov = world.pointOfView();
            world.pointOfView({ ...pov, altitude: Math.max(0.4, pov.altitude - 0.3) }, 500);
        }

        function zoomOut() {
            const pov = world.pointOfView();
            world.pointOfView({ ...pov, altitude: Math.min(4.0, pov.altitude + 0.3) }, 500);
        }

        let flatMode = false;
        function toggleFlatMode() {
            flatMode = !flatMode;
            const btn = document.getElementById('flat-btn');
            if (flatMode) {
                btn.innerText = "FLAT MODE: ON";
                btn.style.background = "#00ffcc22";
                world.pointOfView({ lat: 0, lng: 110, altitude: 3.2 }, 1000);
            } else {
                btn.innerText = "FLAT MODE: OFF";
                btn.style.background = "rgba(5,5,5,0.85)";
                world.pointOfView({ lat: 0, lng: 0, altitude: 2.5 }, 1000);
            }
        }

        // Render awal saat halaman dimuat
        renderNews(allData);
    </script>
</body>
</html>
""".replace("__GLOBE_DATA_JSON__", globe_json)

# Render Komponen Utama ke Streamlit
components.html(globe_html, height=1150)

# Footer & Watermark
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui data tiap 1 jam via GDELT & Live Feed.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
