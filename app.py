import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# Konfigurasi Halaman & Responsivitas Mobile
st.set_page_config(
    page_title="Global & Indonesia OSINT Terminal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="auto"
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
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query_term}&mode=artlist&maxrecords=10&format=json"
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

# Judul Utama Dashboard
st.title("🌐 Live OSINT & Konflik Global-Indonesia")
st.markdown("<i>Sistem pemantauan intelijen berita militer, politik, dan ekonomi dunia serta Indonesia yang diperbarui secara otomatis setiap 1 jam.</i>", unsafe_allow_html=True)

with st.spinner("Memuat data intelijen terbaru..."):
    global_news = fetch_live_news("geopolitics%20OR%20war%20OR%20economy", 25.0, 15.0, "Global/Internasional")
    indo_news = fetch_live_news("Indonesia%20politik%20OR%20ekonomi%20OR%20militer", -0.7893, 113.9213, "Indonesia")
    combined_news = indo_news + global_news

df_news = pd.DataFrame(combined_news)

# Layout Tabs untuk Kenyamanan Akses di HP / Smartphone
tab1, tab2, tab3 = st.tabs(["🗺️ Peta Interaktif", "🇮🇳 Berita Indonesia", "🌍 Berita Global"])

with tab1:
    st.subheader("Titik Pantau Geopolitik & Konflik")
    
    # Koordinat Pusat Peta Dinamis
    center_lat = -0.7893 if indo_news else 20.0
    center_lon = 113.9213 if indo_news else 0.0
    
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=3, 
        tiles="CartoDB dark_matter"
    )

    if not df_news.empty:
        for _, row in df_news.iterrows():
            popup_html = f"""
            <div style="width: 220px; font-size: 11px;">
                <b>[{row['negara']}]</b><br>
                <a href="{row['url']}" target="_blank"><b>{row['title']}</b></a><br>
                <hr style="margin: 5px 0;">
                <span style="color: gray;">Sumber: {row['source']} | {row['date']}</span>
            </div>
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="red" if row['negara'] == "Indonesia" else "blue", icon="info-sign")
            ).add_to(m)

    # Render Peta aman untuk layar HP (width 100%)
    st_folium(m, width="100%", height=450)

with tab2:
    st.subheader("🇮🇳 Berita Terkini Indonesia (Politik, Ekonomi, Militer)")
    if indo_news:
        for item in indo_news:
            st.markdown(f"""
            - **[{item['source']}]** [{item['title']}]({item['url']})  
              <span style="font-size: 0.8em; color: gray;">Waktu: {item['date']}</span>
            """, unsafe_allow_html=True)
    else:
        st.info("Memuat pembaruan berita Indonesia...")

with tab3:
    st.subheader("🌍 Berita Global & Konflik Dunia")
    if global_news:
        for item in global_news:
            st.markdown(f"""
            - **[{item['source']}]** [{item['title']}]({item['url']})  
              <span style="font-size: 0.8em; color: gray;">Waktu: {item['date']}</span>
            """, unsafe_allow_html=True)
    else:
        st.info("Memuat pembaruan berita global...")

# Panel Kontrol & Watermark Sidebar
st.sidebar.markdown("### ⚙️ Panel Kontrol OSINT")
st.sidebar.info("Data diperbarui otomatis setiap 1 jam via GDELT Live API.")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-host; text-align: center; color: gray; font-size: 0.9em;'>"
    "<b>Developed by iqbalmantam</b>"
    "</div>", 
    unsafe_allow_html=True
)
