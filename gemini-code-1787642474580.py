import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import json
import streamlit.components.v1 as components

# Konfigurasi Halaman & Responsivitas Mobile (Full Width Tanpa Sidebar)
st.set_page_config(
    page_title="CRUCIX // Indonesia & Global OSINT Terminal",
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

# Fallback / Baseline Data OSINT yang kaya agar aplikasi tidak pernah kosong
DEFAULT_OSINT_DATA = [
    {
        "title": "Eskalasi Ketegangan Geopolitik di Selat Malaka & Laut China Selatan",
        "url": "https://www.gdeltproject.org",
        "source": "OSINT Global Feed",
        "date": "2026-08-25",
        "lat": 3.1390,
        "lon": 101.6869,
        "negara": "Indonesia/Regional"
    },
    {
        "title": "Bank Indonesia Perkuat Kebijakan Stabilitas Nilai Tukar di Tengah Tekanan Global",
        "url": "https://www.bi.go.id",
        "source": "Ekonomi Nasional",
        "date": "2026-08-25",
        "lat": -6.2088,
        "lon": 106.8456,
        "negara": "Indonesia"
    },
    {
        "title": "Konsolidasi Pertahanan Nasional & Modernisasi Alutsista TNI",
        "url": "https://www.kemhan.go.id",
        "source": "Hankam RI",
        "date": "2026-08-25",
        "lat": -0.7893,
        "lon": 113.9213,
        "negara": "Indonesia"
    },
    {
        "title": "Konflik Ukraina-Rusia: Intensitas Drone & Artileri di Garis Depan",
        "url": "https://www.reuters.com",
        "source": "Reuters",
        "date": "2026-08-25",
        "lat": 48.3794,
        "lon": 31.1656,
        "negara": "Global"
    },
    {
        "title": "Timur Tengah: Pemantauan Ketat Jalur Logistik Energi & Minyak Global",
        "url": "https://www.aljazeera.com",
        "source": "Al Jazeera",
        "date": "2026-08-25",
        "lat": 25.276987,
        "lon": 55.296249,
        "negara": "Global"
    },
    {
        "title": "Krisis Ekonomi & Rantai Pasok Global: Lonjakan Indeks Logistik",
        "url": "https://www.bloomberg.com",
        "source": "Bloomberg",
        "date": "2026-08-25",
        "lat": 40.7128,
        "lon": -74.0060,
        "negara": "Global"
    }
]

# Fungsi Ambil Data Live GDELT API dengan Fallback Aman
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_news():
    articles_list = []
    
    # Ambil dari GDELT Global
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc?query=geopolitics%20OR%20war%20OR%20economy&mode=artlist&maxrecords=12&format=json"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            for art in articles:
                title_en = art.get("title", "")
                if not title_en:
                    continue
                try:
                    title_id = translator.translate(title_en)
                except Exception:
                    title_id = title_en

                articles_list.append({
                    "title": title_id,
                    "url": art.get("url", "#"),
                    "source": art.get("source", "GDELT OSINT"),
                    "date": art.get("seendate", "Terbaru"),
                    "lat": 20.0 + (hash(title_en) % 30) - 15,
                    "lon": 0.0 + (hash(title_en) % 180) - 90,
                    "negara": "Global"
                })
    except Exception:
        pass

    # Ambil Berita Indonesia dari GDELT
    try:
        url_indo = "https://api.gdeltproject.org/api/v2/doc/doc?query=Indonesia%20politics%20OR%20economy&mode=artlist&maxrecords=8&format=json"
        resp_indo = requests.get(url_indo, timeout=8)
        if resp_indo.status_code == 200:
            data_indo = resp_indo.json()
            for art in data_indo.get("articles", []):
                title_en = art.get("title", "")
                if not title_en:
                    continue
                try:
                    title_id = translator.translate(title_en)
                except Exception:
                    title_id = title_en

                articles_list.append({
                    "title": title_id,
                    "url": art.get("url", "#"),
                    "source": art.get("source", "ID News"),
                    "date": art.get("seendate", "Terbaru"),
                    "lat": -0.7893 + ((hash(title_en) % 10) - 5) * 0.4,
                    "lon": 113.9213 + ((hash(title_en) % 10) - 5) * 0.4,
                    "negara": "Indonesia"
                })
    except Exception:
        pass

    # Gabungkan dengan Default Data agar tidak pernah kosong
    if not articles_list:
        return DEFAULT_OSINT_DATA
    return articles_list + DEFAULT_OSINT_DATA

# Styling Tema Cyberpunk Dark ala Crucix
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
    h1, h2, h3 { color: #00ffcc; font-family: 'Courier New', Courier, monospace; text-shadow: 0 0 10px rgba(0,255,204,0.4); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #0a0a0a; }
    .stTabs [data-baseweb="tab"] { background-color: #111; color: #00ffcc; border: 1px solid #00ffcc33; border-radius: 4px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #00ffcc22 !important; border-color: #00ffcc !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("### ⚡ CRUCIX // GLOBAL & INDONESIA OSINT TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING 3D GLOBE ENGINE · LIVE INTEL FEED · AUTO-TRANSLATE ACTIVE</span>", unsafe_allow_html=True)

with st.spinner("Memuat satelit dan jaringan OSINT global..."):
    news_items = fetch_live_news()

indo_list = [item for item in news_items if item["negara"] == "Indonesia" or "Indonesia" in item["negara"]]
global_list = [item for item in news_items if item["negara"] != "Indonesia" and "Indonesia" not in item["negara"]]

globe_json = json.dumps(news_items)

# HTML Globe 3D Interaktif (Globe.gl)
globe_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background-color: #050505; overflow: hidden; }}
        #globe-container {{ width: 100vw; height: 520px; }}
        .globe-tooltip {{
            background: rgba(10, 10, 10, 0.95);
            border: 1px solid #00ffcc;
            color: #fff;
            padding: 10px 14px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 11px;
            max-width: 280px;
            box-shadow: 0 0 20px rgba(0,255,204,0.4);
            border-radius: 3px;
        }}
        .globe-tooltip a {{ color: #00ffcc; text-decoration: none; font-weight: bold; }}
        .globe-tooltip a:hover {{ text-decoration: underline; }}
    </style>
    <script src="https://unpkg.com/three"></script>
    <script src="https://unpkg.com/globe.gl"></script>
</head>
<body>
    <div id="globe-container"></div>
    <script>
        const data = {globe_json};

        const world = Globe()
            (document.getElementById('globe-container'))
            .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
            .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
            .backgroundColor('#050505')
            .pointsData(data)
            .pointLat(d => d.lat)
            .pointLng(d => d.lon)
            .pointColor(d => (d.negara.includes('Indonesia')) ? '#ff0055' : '#00ffcc')
            .pointAltitude(0.1)
            .pointRadius(0.6)
            .pointLabel(d => `
                <div class="globe-tooltip">
                    <b>[${{d.negara.toUpperCase()}}]</b><br>
                    <a href="${{d.url}}" target="_blank">${{d.title}}</a><br>
                    <hr style="border-color: #333; margin: 6px 0;">
                    <span style="color: #888;">SRC: ${{d.source}} | ${{d.date}}</span>
                </div>
            `);

        // Kontrol interaktif & rotasi otomatis
        const controls = world.controls();
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.8;
        controls.enableZoom = true;
    </script>
</body>
</html>
"""

components.html(globe_html, height=530)

st.markdown("---")
tab1, tab2 = st.tabs(["🇮🇳 Berita Terkini Indonesia", "🌍 Berita Global & Konflik"])

with tab1:
    st.markdown("#### 🇮🇳 Intelijen Domestik & Nasional")
    if indo_list:
        for item in indo_list:
            st.markdown(f"""
            - **[{item['source']}]** [{item['title']}]({item['url']})  
              <span style="font-size: 0.8em; color: gray;">Waktu: {item['date']}</span>
            """, unsafe_allow_html=True)
    else:
        st.info("Memuat intelijen Indonesia...")

with tab2:
    st.markdown("#### 🌍 Intelijen Global, Perang & Ekonomi")
    if global_list:
        for item in global_list:
            st.markdown(f"""
            - **[{item['source']}]** [{item['title']}]({item['url']})  
              <span style="font-size: 0.8em; color: gray;">Waktu: {item['date']}</span>
            """, unsafe_allow_html=True)
    else:
        st.info("Memuat intelijen global...")

# Footer & Watermark
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui data tiap 1 jam via GDELT & Live Feed.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)