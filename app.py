"""
Logistics News & Financial Terminal
- Left Column: Live News Ticker (Vertical Auto-Scroll, Clean White Titles)
- Right Column: Currency Exchange Rates (Beli & Jual vs IDR)
- Bottom: Stable Interactive Map (D3.js Flat & Globe.gl)
- Developed by iqbalmantam
"""

import time
import streamlit as st
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus
import json
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# Konfigurasi Halaman (Full Width Layout)
st.set_page_config(
    page_title="Logistics & Currency Terminal",
    page_icon="🚛",
    layout="wide"
)

# Custom Styling Terminal Gelap Elegan
st.markdown("""
<style>
    header {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp { background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
    
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
    
    /* Animasi Auto-Scroll untuk Ticker Berita */
    @keyframes autoScroll {
        0% { transform: translateY(0); }
        100% { transform: translateY(-50%); }
    }
    .ticker-container:hover .ticker-track {
        animation-play-state: paused;
    }
</style>
""", unsafe_allow_html=True)

# Auto-Refresh otomatis setiap 1 Jam
st_autorefresh(interval=3600 * 1000, key="logistics_refresher")

# ─── Kamus Koordinat Geografis Presisi ────────────────────────
GEOGRAPHIC_MAPPING = {
    "jakarta": {"lat": -6.2088, "lon": 106.8456},
    "indonesia": {"lat": -0.7893, "lon": 113.9213},
    "singapore": {"lat": 1.3521, "lon": 103.8198},
    "singapura": {"lat": 1.3521, "lon": 103.8198},
    "china": {"lat": 35.8617, "lon": 104.1954},
    "tiongkok": {"lat": 35.8617, "lon": 104.1954},
    "shanghai": {"lat": 31.2304, "lon": 121.4737},
    "japan": {"lat": 36.2048, "lon": 138.2529},
    "jepang": {"lat": 36.2048, "lon": 138.2529},
    "tokyo": {"lat": 35.6762, "lon": 139.6503},
    "usa": {"lat": 37.0902, "lon": -95.7129},
    "america": {"lat": 37.0902, "lon": -95.7129},
    "amerika": {"lat": 37.0902, "lon": -95.7129},
    "europe": {"lat": 54.5260, "lon": 15.2551},
    "eropa": {"lat": 54.5260, "lon": 15.2551},
    "uk": {"lat": 55.3781, "lon": -3.4360},
    "london": {"lat": 51.5074, "lon": -0.1278},
    "germany": {"lat": 51.1657, "lon": 10.4515},
    "jerman": {"lat": 51.1657, "lon": 10.4515},
    "rotterdam": {"lat": 51.9244, "lon": 4.4777}
}

def get_precise_coordinates(text: str):
    text_lower = text.lower()
    for keyword, loc in GEOGRAPHIC_MAPPING.items():
        if keyword in text_lower:
            return loc["lat"], loc["lon"]
    return -6.2088, 106.8456

# ─── Data Fetching Functions ──────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_news(category="all"):
    queries = {
        "id_log": ["industri logistik Indonesia", "jasa pengiriman barang Indonesia"],
        "supply": ["supply chain logistics"],
        "warehouse": ["warehouse logistics"],
        "freight": ["freight forwarding", "shipping cargo"]
    }
    
    active_queries = queries.get(category, ["logistik Indonesia", "supply chain logistics", "shipping cargo", "freight forwarding"])

    all_articles = []
    seen = set()
    for q in active_queries:
        try:
            url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=id&gl=ID&ceid=ID:id"
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                if " - " in title:
                    title_clean, source = title.rsplit(" - ", 1)
                else:
                    title_clean = title
                    source = "WEB"
                
                link = entry.get("link", "#")
                published = entry.get("published", datetime.now().strftime("%d %b %Y, %H:%M"))
                summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)[:250]
                lat, lon = get_precise_coordinates(title_clean + " " + summary)
                
                if title_clean.lower() not in seen:
                    seen.add(title_clean.lower())
                    all_articles.append({
                        "title": title_clean,
                        "source": source.upper(),
                        "link": link,
                        "published": published,
                        "lat": lat,
                        "lon": lon
                    })
        except Exception:
            pass
    return all_articles[:15]

@st.cache_data(ttl=3600)
def fetch_currency_rates():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rates = data.get("rates", {})
            idr_per_usd = rates.get("IDR", 15500.0)
            
            targets = {
                "USD": 1.0, "SGD": rates.get("SGD", 1.35), 
                "EUR": rates.get("EUR", 0.92), "GBP": rates.get("GBP", 0.79),
                "JPY": rates.get("JPY", 150.0), "CNY": rates.get("CNY", 7.2)
            }
            
            result = {}
            for curr, rate_usd in targets.items():
                mid = idr_per_usd if curr == "USD" else (idr_per_usd / rate_usd)
                buy = mid * 0.992
                sell = mid * 1.008
                result[curr] = {
                    "buy": f"Rp {buy:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "sell": f"Rp {sell:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                }
            return result
    except Exception:
        pass
        
    return {
        "USD": {"buy": "Rp 15.450,00", "sell": "Rp 15.650,00"},
        "SGD": {"buy": "Rp 11.450,00", "sell": "Rp 11.650,00"},
        "EUR": {"buy": "Rp 16.750,00", "sell": "Rp 16.950,00"},
        "GBP": {"buy": "Rp 24.044,37", "sell": "Rp 24.286,03"},
        "JPY": {"buy": "Rp 102,50", "sell": "Rp 104,50"},
        "CNY": {"buy": "Rp 2.150,00", "sell": "Rp 2.190,00"}
    }


# State Management
if "selected_cat" not in st.session_state:
    st.session_state.selected_cat = "all"
if "flat_mode" not in st.session_state:
    st.session_state.flat_mode = False

with st.spinner("MENGINISIALISASI FEED SISTEM & MENYINKRONKAN DATA..."):
    news_items = fetch_news(st.session_state.selected_cat)
    rates_dict = fetch_currency_rates()


# ─── Main Header ──────────────────────────────────────────────
st.markdown("### 🚛 LOGISTICS NEWS & FINANCIAL TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>COMMAND CENTER · LIVE TICKER & MAPPING SYSTEM</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ─── TATA LETAK SEIMBANG 2 KOLOM (KIRI & KANAN) ───────────────
left_col, right_col = st.columns(2)

with left_col:
    # 1. Live News Ticker (Kiri) - Dibuat SATU BARIS TANPA SPASI agar tidak error kode HTML mentah
    cards_html = ""
    for item in news_items:
        cards_html += f'<div style="background: #0a1412; border: 1px solid #163028; border-radius: 4px; padding: 12px; margin-bottom: 12px;"><div style="font-size: 0.75em; color: #00ffcc; margin-bottom: 4px;">[{item["source"]}] &bull; {item["published"]}</div><div style="font-size: 0.95em; font-weight: bold; margin-top: 4px; line-height: 1.3;"><a href="{item["link"]}" target="_blank" style="color: #ffffff; text-decoration: none;">{item["title"]}</a></div></div>'
    
    ticker_widget_html = f'<div style="background: #080808; border: 1px solid #1a3630; border-radius: 6px; padding: 15px; margin-bottom: 15px;"><div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a3630; padding-bottom: 10px; margin-bottom: 10px;"><span style="font-family: \'Courier New\', Courier, monospace; font-size: 14px; font-weight: bold; color: #00ffcc;">🟢 LIVE NEWS TICKER (AUTO-SCROLL)</span><span style="border: 1px solid #1a3630; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #00ffcc;">{len(news_items)} ITEMS</span></div><div class="ticker-container" style="height: 480px; overflow: hidden; position: relative;"><div class="ticker-track" style="position: absolute; width: 100%; animation: autoScroll 35s linear infinite;">{cards_html}{cards_html}</div></div></div>'
    
    st.markdown(ticker_widget_html, unsafe_allow_html=True)


with right_col:
    # 2. Kurs Valas Asing (Kanan) - Dibuat SATU BARIS TANPA SPASI
    forex_cards_html = ""
    currencies_meta = [
        ("USD", "US Dollar"), ("SGD", "Singapore Dollar"), 
        ("EUR", "Euro Zone"), ("GBP", "British Pound"), 
        ("JPY", "Japanese Yen"), ("CNY", "Chinese Yuan")
    ]
    
    for code, name in currencies_meta:
        vals = rates_dict.get(code, {"buy": "-", "sell": "-"})
        forex_cards_html += f'<div style="background: #080808; border: 1px solid #1a3630; border-radius: 6px; padding: 11px 16px; margin-bottom: 10px;"><div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.95em; font-weight: bold; color: #00ffcc; border-bottom: 1px solid #142822; padding-bottom: 4px; margin-bottom: 6px;"><span>{code}</span><span style="font-size: 0.75em; color: #888;">IDR / {code} ({name})</span></div><div style="display: flex; justify-content: space-between; font-size: 0.9em;"><div><span style="color: #666; font-size: 10px;">BELI:</span> <span style="color: #00ffcc; font-weight: bold;">{vals["buy"]}</span></div><div><span style="color: #666; font-size: 10px;">JUAL:</span> <span style="color: #ffaa00; font-weight: bold;">{vals["sell"]}</span></div></div></div>'

    forex_widget_html = f'<div style="background: #080808; border: 1px solid #1a3630; border-radius: 6px; padding: 15px; margin-bottom: 15px;"><div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a3630; padding-bottom: 10px; margin-bottom: 10px;"><span style="font-family: \'Courier New\', Courier, monospace; font-size: 14px; font-weight: bold; color: #00ffcc;">💱 KURS VALUTA ASING (BELI & JUAL)</span><span style="border: 1px solid #1a3630; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #00ffcc;">LIVE 1H</span></div><div style="max-height: 480px; overflow-y: auto;">{forex_cards_html}</div></div>'
    
    st.markdown(forex_widget_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── PETA INTERAKTIF (Menggunakan Script Stabil dari Referensi Anda) ──
st.markdown("""
<div style="background: #080808; border: 1px solid #1a3630; padding: 12px 16px; border-radius: 6px; margin-bottom: 15px; font-weight: bold; color: #00ffcc;">
    <span>🗺️ GLOBAL LOGISTICS MAPPING</span>
</div>
""", unsafe_allow_html=True)

cat_menu = [
    ("all", "SEMUA"),
    ("id_log", "LOGISTIK ID"),
    ("supply", "SUPPLY CHAIN"),
    ("warehouse", "WAREHOUSE"),
    ("freight", "FREIGHT & E-COM")
]

menu_cols = st.columns(5)
for i, (cat_key, cat_name) in enumerate(cat_menu):
    with menu_cols[i]:
        is_active = (st.session_state.selected_cat == cat_key)
        btn_label = f"🟢 {cat_name}" if is_active else cat_name
        if st.button(btn_label, key=f"cat_{cat_key}"):
            st.session_state.selected_cat = cat_key
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

# Konversi Data ke JSON
globe_data_clean = []
for n in news_items:
    globe_data_clean.append({
        "title": n["title"],
        "url": n["link"],
        "published": n["published"],
        "source": n["source"],
        "lat": n["lat"],
        "lon": n["lon"]
    })

globe_json = json.dumps(globe_data_clean)

zoom_cmd = ""
if "zoom_action" in st.session_state:
    action = st.session_state.pop("zoom_action")
    if action == "in":
        zoom_cmd = "window.zoomIn && window.zoomIn();"
    elif action == "out":
        zoom_cmd = "window.zoomOut && window.zoomOut();"

# Script Peta Sama Persis Seperti Project Referensi Anda (Bebas Bug)
map_html_template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow: hidden; }
        #map-container { width: 100%; height: 500px; position: relative; border: 1px solid #1a3630; background: #050505; }
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
        const container = document.getElementById('map-container');
        
        const tooltipHtml = d => `<div class="globe-tooltip"><b>[${d.source}]</b><br><a href="${d.url}" target="_blank">${d.title}</a><br><hr style="border-color: #333; margin: 6px 0;"><span style="color: #888;">DATE: ${d.published}</span></div>`;

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
                .pointAltitude(() => 0.09)
                .pointRadius(() => 0.55)
                .ringsData(ringsData)
                .ringColor(() => '#00ffcc')
                .ringMaxRadius('maxRadius')
                .ringPropagationSpeed('propagationSpeed')
                .ringRepeatPeriod('repeatPeriod')
                .pointLabel(tooltipHtml);
            
            const controls = world.controls();
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.7;
            controls.enableZoom = true;
            world.pointOfView({ lat: 0, lng: 0, altitude: 2.5 }, 1000);
            
            window.zoomIn = () => { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.max(0.4, pov.altitude - 0.3) }, 500); };
            window.zoomOut = () => { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.min(4.0, pov.altitude + 0.3) }, 500); };
            
            __ZOOM_CMD__
        }

        function buildFlatMap() {
            const width = container.clientWidth || window.innerWidth || 900;
            const height = 500;

            const svg = d3.select(container).append('svg')
                .attr('width', width).attr('height', height)
                .style('background', '#050505').style('display', 'block');

            const zoomLayer = svg.append('g');

            const projection = d3.geoEquirectangular()
                .scale(width / 6.28)
                .translate([width / 2, height / 2]);

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
                .finally(() => drawPointsAndTooltips());

            function drawPointsAndTooltips() {
                const tooltip = d3.select(container).append('div')
                    .style('position', 'absolute').style('pointer-events', 'none')
                    .style('opacity', 0).style('z-index', 100).style('transition', 'opacity 0.15s');

                contentLayer.append('g').selectAll('circle').data(data).join('circle')
                    .attr('cx', d => { const coords = projection([d.lon, d.lat]); return coords ? coords[0] : -9999; })
                    .attr('cy', d => { const coords = projection([d.lon, d.lat]); return coords ? coords[1] : -9999; })
                    .attr('r', 5)
                    .attr('fill', '#00ffcc')
                    .attr('stroke', '#00ffcc')
                    .attr('stroke-width', 7).attr('stroke-opacity', 0.2)
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

# Injeksi variabel menggunakan Replace (Tanpa Crash)
final_map_html = (
    map_html_template
    .replace("__GLOBE_DATA_JSON__", globe_json)
    .replace("__IS_FLAT_BOOL__", "true" if st.session_state.flat_mode else "false")
    .replace("__ZOOM_CMD__", zoom_cmd)
)

components.html(final_map_html, height=520)


# ─── Footer ───────────────────────────────────────────────────
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem otomatis memperbarui berita logistik & kurs setiap 1 jam.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
