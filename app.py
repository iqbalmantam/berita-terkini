import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import json
import streamlit.components.v1 as components

# Konfigurasi Halaman & Responsivitas Mobile (Full Width Tanpa Sidebar)
st.set_page_config(
    page_title="CRUCIX // Indonesia OSINT Terminal",
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

# Fungsi Ambil Data Live GDELT API dengan Error Handling Aman
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_news(query_term, default_lat, default_lon, default_country):
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query_term}&mode=artlist&maxrecords=12&format=json"
    articles_list = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            if articles:
                for art in articles:
                    title_en = art.get("title", "")
                    if not title_en:
                        continue
                    
                    # Terjemahan otomatis ke Bahasa Indonesia
                    try:
                        title_id = translator.translate(title_en) if query_term != "Indonesia" else title_en
                        if not title_id:
                            title_id = title_en
                    except Exception:
                        title_id = title_en

                    articles_list.append({
                        "title": title_id,
                        "url": art.get("url", "#"),
                        "source": art.get("source", "Unknown"),
                        "date": art.get("seendate", "Terbaru"),
                        "lat": default_lat,
                        "lon": default_lon,
                        "negara": default_country
                    })
    except Exception:
        pass  # Mencegah aplikasi crash jika koneksi API gagal
    return articles_list

# Styling Tema Gelap ala Terminal Cyberpunk (Crucix Style)
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
    h1, h2, h3 { color: #00ffcc; font-family: 'Courier New', Courier, monospace; text-shadow: 0 0 8px rgba(0,255,204,0.3); }
</style>
""", unsafe_allow_html=True)

# Judul Utama Terminal
st.markdown("### ⚡ CRUCIX // GLOBAL & INDONESIA OSINT TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING 3D GLOBE ENGINE · LIVE OSINT FEED · AUTO-TRANSLATE ACTIVE</span>", unsafe_allow_html=True)

with st.spinner("Menghubungkan ke satelit & sumber OSINT global..."):
    global_news = fetch_live_news("geopolitics%20OR%20war%20OR%20economy", 25.0, 15.0, "Global")
    indo_news = fetch_live_news("Indonesia%20politik%20OR%20ekonomi%20OR%20militer", -0.7893, 113.9213, "Indonesia")
    combined_news = indo_news + global_news

# Konversi data ke format JSON yang aman dibaca oleh JavaScript Globe 3D
globe_data_json = json.dumps(combined_news)

# Render Bola Dunia 3D interaktif menggunakan Globe.gl (Persis seperti Crucix)
globe_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow: hidden; }}
        #globe-viz {{ width: 100%; height: 480px; }}
        .tooltip {{ background: rgba(10,10,10,0.92); border: 1px solid #00ffcc; padding: 10px; font-size: 11px; color: #fff; max-width: 260px; box-shadow: 0 0 15px rgba(0,255,204,0.3); }}
        .tooltip a {{ color: #00ffcc; text-decoration: none; }}
        .tooltip a:hover {{ text-decoration: underline; }}
    </style>
    <script src="https://unpkg.com/three"></script>
    <script src="https://unpkg.com/globe.gl"></script>
</head>
<body>
    <div id="globe-viz"></div>
    <script>
        const newsData = {globe_data_json};

        const world = Globe()
            (document.getElementById('globe-viz'))
            .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
            .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
            .backgroundColor('#050505')
            .pointsData(newsData)
            .pointLat(d => d.lat)
            .pointLng(d => d.lng)
            .pointColor(d => d.negara === 'Indonesia' ? '#ff0055' : '#00ffcc')
            .pointAltitude(0.08)
            .pointRadius(0.55)
            .pointLabel(d => `
                <div class="tooltip">
                    <b>[${{d.negara}}]</b><br>
                    <a href="${{d.url}}" target="_blank">${{d.title}}</a><br>
                    <hr style="border-color: #333; margin: 6px 0;">
                    <span style="color: #888;">SRC: ${{d.source}} | ${{d.date}}</span>
                </div>
            `);

        // Rotasi otomatis globe agar hidup
        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.6;
    </script>
</body>
</html>
"""

# Tampilkan widget 3D Globe di Streamlit
components.html(globe_html, height=500)

# Feed Berita di Bawah Globe (Tabs yang sangat rapi untuk HP)
st.markdown("---")
tab1, tab2 = st.tabs(["🇮🇳 Berita Terkini Indonesia", "🌍 Berita Global & Konflik"])

with tab1:
    st.markdown("#### Intelijen Domestik (Politik, Ekonomi, Pertahanan)")
    if indo_news:
        for item in indo_news:
            st.markdown(f"""
            - **[{item['source']}]** [{item['title']}]({item['url']})  
              <span style="font-size: 0.8em; color: gray;">Waktu: {item['date']}</span>
            """, unsafe_allow_html=True)
    else:
        st.info("Memuat pembaruan berita Indonesia...")

with tab2:
    st.markdown("#### Intelijen Global & Konflik Dunia")
    if global_news:
        for item in global_news:
            st.markdown(f"""
            - **[{item['source']}]** [{item['title']}]({item['url']})  
              <span style="font-size: 0.8em; color: gray;">Waktu: {item['date']}</span>
            """, unsafe_allow_html=True)
    else:
        st.info("Memuat pembaruan berita global...")

# Footer & Watermark di Bagian Bawah (Tanpa Frame Kiri / Sidebar)
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui data tiap 1 jam via GDELT.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
