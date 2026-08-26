"""
Logistics News & Financial Terminal
- Left Column: Live News Ticker (Vertical Auto-Scroll, Clean White Titles)
- Right Column: Currency Exchange Rates (Beli & Jual vs IDR)
- Bottom: Stable Interactive Map (100% from user's working script)
- Developed by iqbalmantam
"""

import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus
import time
import hashlib
import json
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Logistics & Currency Terminal",
    page_icon="🚛",
    layout="wide"
)

# ─── Custom CSS (Terminal & Dashboard Tactical Hybrid) ─────────
# Semua CSS diletakkan rata kiri agar tidak terdeteksi sebagai code-block
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
    font-size: 0.85em;
}
div.stButton > button:hover {
    background-color: #132622 !important;
    border-color: #00ffcc !important;
    color: #ffffff !important;
}

/* Custom CSS untuk Modul Ticker dan Valas */
.mod-container {
    background: #080808;
    border: 1px solid #1a3630;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 15px;
}
.mod-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1a3630;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.mod-title {
    font-family: 'Courier New', Courier, monospace;
    font-size: 14px;
    font-weight: bold;
    color: #00ffcc;
}
.mod-badge {
    border: 1px solid #1a3630;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    color: #00ffcc;
}

/* Ticker Auto-Scroll */
@keyframes autoScroll {
    0% { transform: translateY(0); }
    100% { transform: translateY(-50%); }
}
.ticker-viewport {
    height: 480px;
    overflow: hidden;
    position: relative;
}
.ticker-track {
    position: absolute;
    width: 100%;
    animation: autoScroll 35s linear infinite;
}
.ticker-viewport:hover .ticker-track {
    animation-play-state: paused;
}
.ticker-card {
    background: #0a1412;
    border: 1px solid #163028;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 12px;
}
.ticker-meta {
    font-size: 0.75em;
    color: #00ffcc;
    margin-bottom: 4px;
}
.ticker-title a {
    color: #ffffff !important; /* Judul Berita Putih Bersih */
    text-decoration: none;
    font-size: 0.95em;
    font-weight: bold;
    line-height: 1.3;
}
.ticker-title a:hover {
    color: #00ffcc !important;
    text-decoration: underline;
}

/* Currency Card */
.curr-card {
    background: #080808;
    border: 1px solid #1a3630;
    border-radius: 6px;
    padding: 11px 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# Auto-Refresh setiap 1 Jam
st_autorefresh(interval=3600 * 1000, key="logistics_refresher")


# ─── Kamus Koordinat Geografis Nyata & Presisi ───────────────
GEOGRAPHIC_MAPPING = {
    "jakarta": {"lat": -6.2088, "lon": 106.8456, "region": "asia_pacific"},
    "indonesia": {"lat": -0.7893, "lon": 113.9213, "region": "asia_pacific"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "region": "asia_pacific"},
    "singapura": {"lat": 1.3521, "lon": 103.8198, "region": "asia_pacific"},
    "china": {"lat": 35.8617, "lon": 104.1954, "region": "asia_pacific"},
    "tiongkok": {"lat": 35.8617, "lon": 104.1954, "region": "asia_pacific"},
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "region": "asia_pacific"},
    "japan": {"lat": 36.2048, "lon": 138.2529, "region": "asia_pacific"},
    "jepang": {"lat": 36.2048, "lon": 138.2529, "region": "asia_pacific"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "region": "asia_pacific"},
    "usa": {"lat": 37.0902, "lon": -95.7129, "region": "americas"},
    "america": {"lat": 37.0902, "lon": -95.7129, "region": "americas"},
    "amerika": {"lat": 37.0902, "lon": -95.7129, "region": "americas"},
    "europe": {"lat": 54.5260, "lon": 15.2551, "region": "europe"},
    "eropa": {"lat": 54.5260, "lon": 15.2551, "region": "europe"},
    "uk": {"lat": 55.3781, "lon": -3.4360, "region": "europe"},
    "london": {"lat": 51.5074, "lon": -0.1278, "region": "europe"},
    "germany": {"lat": 51.1657, "lon": 10.4515, "region": "europe"},
    "jerman": {"lat": 51.1657, "lon": 10.4515, "region": "europe"},
    "rotterdam": {"lat": 51.9244, "lon": 4.4777, "region": "europe"}
}

def get_precise_coordinates(text: str):
    text_lower = text.lower()
    for keyword, loc in GEOGRAPHIC_MAPPING.items():
        if keyword in text_lower:
            return loc["lat"], loc["lon"], loc["region"]
    return -6.2088, 106.8456, "asia_pacific"


# ─── Data Fetching Functions ──────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_google_news_rss(query: str, lang: str = "en", country: str = "us", max_results: int = 15, category: str = "general") -> list:
    encoded_query = quote_plus(query)
    if lang == "id":
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"
    else:
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=US&ceid=US:en"

    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            published = ""
            published_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_dt = datetime(*entry.published_parsed[:6])
                published = published_dt.strftime("%d %b %Y, %H:%M")

            title = entry.get("title", "")
            source = ""
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source = parts[1] if len(parts) > 1 else ""

            summary = ""
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary = soup.get_text(strip=True)[:300]

            article_id = hashlib.md5(entry.get("link", title).encode()).hexdigest()
            lat, lon, region = get_precise_coordinates(title + " " + summary)

            articles.append({
                "id": article_id, "title": title, "link": entry.get("link", ""),
                "published": published, "published_dt": published_dt,
                "source": source.upper() if source else "WEB",
                "summary": summary, "language": lang,
                "lat": lat, "lon": lon, "region": region,
                "category": category, "type": "logistics_news"
            })
        return articles
    except Exception:
        return []

def fetch_news_with_status(category: str) -> list:
    queries = {
        "id_log": (["industri logistik Indonesia", "jasa pengiriman barang Indonesia"], ["Indonesia logistics industry"]),
        "supply": (["supply chain Indonesia"], ["supply chain logistics"]),
        "warehouse": (["warehouse logistik Indonesia"], ["warehouse logistics"]),
        "freight": (["freight forwarding Indonesia"], ["global freight forwarding"])
    }

    all_articles = []
    seen_titles = set()
    cat_keys = queries.keys() if category == "all" else [category]

    for cat in cat_keys:
        q_id, q_en = queries.get(cat, (["logistik"], ["logistics"]))
        for q in q_id:
            for art in fetch_google_news_rss(q, lang="id", country="ID", max_results=8, category=cat):
                if art["title"].lower() not in seen_titles:
                    seen_titles.add(art["title"].lower())
                    all_articles.append(art)
        for q in q_en:
            for art in fetch_google_news_rss(q, lang="en", country="us", max_results=8, category=cat):
                if art["title"].lower() not in seen_titles:
                    seen_titles.add(art["title"].lower())
                    all_articles.append(art)

    all_articles.sort(key=lambda x: x["published_dt"] if x["published_dt"] else datetime.min, reverse=True)
    return all_articles

@st.cache_data(ttl=3600)
def fetch_currency_rates():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        data = res.json()
        rates = data.get("rates", {})
        idr_per_usd = rates.get("IDR", 15500.0)
        
        targets = {
            "USD (US Dollar)": 1.0,
            "SGD (Singapore Dollar)": rates.get("SGD", 1.35),
            "EUR (Euro Zone)": rates.get("EUR", 0.92),
            "GBP (British Pound)": rates.get("GBP", 0.79),
            "JPY (Japanese Yen)": rates.get("JPY", 150.0),
            "CNY (Chinese Yuan)": rates.get("CNY", 7.2)
        }
        
        result = {}
        for curr, rate_usd in targets.items():
            mid = idr_per_usd if "USD" in curr else (idr_per_usd / rate_usd)
            buy = mid * 0.992
            sell = mid * 1.008
            result[curr] = {
                "buy": f"Rp {buy:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "sell": f"Rp {sell:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            }
        return result
    except Exception:
        return {
            "USD (US Dollar)": {"buy": "Rp 15.450,00", "sell": "Rp 15.650,00"},
            "SGD (Singapore Dollar)": {"buy": "Rp 11.450,00", "sell": "Rp 11.650,00"},
            "EUR (Euro Zone)": {"buy": "Rp 16.750,00", "sell": "Rp 16.950,00"},
            "GBP (British Pound)": {"buy": "Rp 24.044,37", "sell": "Rp 24.286,03"}
        }

# State Management
if "selected_cat" not in st.session_state:
    st.session_state.selected_cat = "all"
if "flat_mode" not in st.session_state:
    st.session_state.flat_mode = False

with st.spinner("MENGINISIALISASI FEED SISTEM & MENYINKRONKAN DATA..."):
    all_news = fetch_news_with_status(st.session_state.selected_cat)
    rates_dict = fetch_currency_rates()


# ─── Main Header ──────────────────────────────────────────────
st.markdown("### 🚛 LOGISTICS NEWS & FINANCIAL TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>COMMAND CENTER · LIVE TICKER & MAPPING SYSTEM</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ─── TATA LETAK SEIMBANG 2 KOLOM (KIRI & KANAN) ───────────────
left_col, right_col = st.columns(2)

with left_col:
    # Build HTML untuk Ticker tanpa indentasi sama sekali
    cards_html = ""
    for item in all_news[:15]:
        cards_html += f"""<div class="ticker-card"><div class="ticker-meta">[{item['source']}] &bull; {item['published']}</div><div class="ticker-title"><a href="{item['link']}" target="_blank">{item['title']}</a></div></div>"""
    
    ticker_widget_html = f"""
<div class="mod-container">
<div class="mod-header">
<span class="mod-title">🟢 LIVE NEWS TICKER (AUTO-SCROLL)</span>
<span class="mod-badge">{len(all_news[:15])} ITEMS</span>
</div>
<div class="ticker-viewport">
<div class="ticker-track">
{cards_html}
{cards_html}
</div>
</div>
</div>
"""
    # Render HTML Ticker
    st.markdown(ticker_widget_html, unsafe_allow_html=True)

with right_col:
    # Build HTML untuk Valas
    forex_cards_html = ""
    for curr_name, vals in rates_dict.items():
        forex_cards_html += f"""<div class="curr-card"><div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.95em; font-weight: bold; color: #00ffcc; border-bottom: 1px solid #142822; padding-bottom: 4px; margin-bottom: 6px;"><span>{curr_name.split()[0]}</span><span style="font-size: 0.75em; color: #888;">IDR / {curr_name.split()[0]}</span></div><div style="display: flex; justify-content: space-between; font-size: 0.9em;"><div><span style="color: #666; font-size: 10px;">BELI:</span> <span style="color: #00ffcc; font-weight: bold;">{vals['buy']}</span></div><div><span style="color: #666; font-size: 10px;">JUAL:</span> <span style="color: #ffaa00; font-weight: bold;">{vals['sell']}</span></div></div></div>"""

    forex_widget_html = f"""
<div class="mod-container">
<div class="mod-header">
<span class="mod-title">💱 KURS VALUTA ASING (BELI & JUAL)</span>
<span class="mod-badge">LIVE 1H</span>
</div>
<div style="max-height: 480px; overflow-y: auto;">
{forex_cards_html}
</div>
</div>
"""
    # Render HTML Valas
    st.markdown(forex_widget_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── PETA INTERAKTIF (Diambil 100% dari referensi pengguna) ──
st.markdown("""
<div class="mod-container" style="padding: 12px 16px; margin-bottom: 15px;">
<span class="mod-title" style="margin:0;">🗺️ GLOBAL LOGISTICS MAPPING</span>
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

# Siapkan data map
globe_data_clean = []
for n in all_news[:12]:
    globe_data_clean.append({
        "id": n.get("id", ""),
        "title": n["title"],
        "url": n["link"],
        "published": n["published"],
        "source": n["source"],
        "summary": n.get("summary", ""),
        "language": n.get("language", ""),
        "lat": n["lat"],
        "lon": n["lon"],
        "category": n.get("category", ""),
        "type": n.get("type", "news")
    })

globe_json = json.dumps(globe_data_clean)

zoom_cmd = ""
if "zoom_action" in st.session_state:
    action = st.session_state.pop("zoom_action")
    if action == "in":
        zoom_cmd = "window.zoomIn && window.zoomIn();"
    elif action == "out":
        zoom_cmd = "window.zoomOut && window.zoomOut();"

# SCRIPT HTML PETA PERSIS DARI REFERENSI
map_html_template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; background-color: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; overflow: hidden; }
        #map-container { width: 100%; height: 500px; position: relative; border: 1px solid #1a3630; background: #050505; display: flex; justify-content: center; align-items: center; }
        .globe-tooltip { background: rgba(10, 10, 10, 0.95); border: 1px solid #00ffcc; color: #fff; padding: 10px 14px; font-family: 'Courier New', Courier, monospace; font-size: 11px; max-width: 280px; box-shadow: 0 0 20px rgba(0,255,204,0.4); border-radius: 3px; z-index: 1000; }
        .globe-tooltip a { color: #00ffcc; text-decoration: none; font-weight: bold; }
        .globe-tooltip a:hover { text-decoration: underline; }
        .error-box { color: #ff3333; padding: 20px; font-family: monospace; font-size: 12px; }
        
        @keyframes pulse {
            0% { r: 4px; opacity: 1; }
            50% { r: 9px; opacity: 0.4; }
            100% { r: 4px; opacity: 1; }
        }
        .pulse-ring { animation: pulse 2s infinite ease-in-out; }
    </style>
    <script src="https://unpkg.com/three@0.152.0/build/three.min.js"></script>
    <script src="https://unpkg.com/globe.gl@2.25.1/dist/globe.gl.min.js"></script>
    <script src="https://unpkg.com/d3@7.8.5/dist/d3.min.js"></script>
    <script src="https://unpkg.com/topojson-client@3.1.0/dist/topojson-client.min.js"></script>
</head>
<body>
    <div id="map-container"></div>
    <script>
        try {
            const data = __GLOBE_DATA_JSON__;
            const isFlat = __IS_FLAT_BOOL__;
            const container = document.getElementById('map-container');
            const width = container.clientWidth || window.innerWidth || 900;
            const height = 500;
            const tooltipHtml = d => `<div class="globe-tooltip"><b>[${d.source}]</b><br><a href="${d.url}" target="_blank">${d.title}</a><br><hr style="border-color: #333; margin: 6px 0;"><span style="color: #888;">DATE: ${d.published}</span></div>`;

            function buildGlobe() {
                if (!window.Globe || !window.THREE) throw new Error("Globe.gl gagal dimuat.");
                const ringsData = data.map(d => ({ lat: d.lat, lng: d.lon, maxRadius: 3.5, propagationSpeed: 2.0, repeatPeriod: 1600 }));
                const world = Globe()(container)
                    .width(width)
                    .height(height)
                    .globeImageUrl('https://unpkg.com/three-globe@2.24.1/example/img/earth-night.jpg')
                    .bumpImageUrl('https://unpkg.com/three-globe@2.24.1/example/img/earth-topology.png')
                    .backgroundColor('#050505')
                    .pointsData(data)
                    .pointLat(d => d.lat)
                    .pointLng(d => d.lon)
                    .pointColor(() => '#00ffcc')
                    .pointAltitude(() => 0.08)
                    .pointRadius(() => 0.5)
                    .ringsData(ringsData)
                    .ringColor(() => '#00ffcc')
                    .ringMaxRadius('maxRadius')
                    .ringPropagationSpeed('propagationSpeed')
                    .ringRepeatPeriod('repeatPeriod')
                    .pointLabel(tooltipHtml);
                
                const controls = world.controls();
                controls.autoRotate = true;
                controls.autoRotateSpeed = 0.4;
                controls.enableZoom = true;
                world.pointOfView({ lat: 0, lng: 0, altitude: 2.5 }, 1000);
                
                window.zoomIn = () => { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.max(0.4, pov.altitude - 0.3) }, 500); };
                window.zoomOut = () => { const pov = world.pointOfView(); world.pointOfView({ ...pov, altitude: Math.min(4.0, pov.altitude + 0.3) }, 500); };
                __ZOOM_CMD__
            }

            function buildFlatMap() {
                const svg = d3.select(container).append('svg').attr('width', width).attr('height', height).style('background', '#050505').style('display', 'block');
                const zoomLayer = svg.append('g');
                const projection = d3.geoEquirectangular().scale(width / 6.28).translate([width / 2, height / 2]);
                const geoPath = d3.geoPath(projection);

                zoomLayer.append('path').datum({ type: 'Sphere' }).attr('d', geoPath).attr('fill', '#070f0e').attr('stroke', '#1a3630').attr('stroke-width', 1);
                zoomLayer.append('path').datum(d3.geoGraticule10()).attr('d', geoPath).attr('fill', 'none').attr('stroke', '#0e2320').attr('stroke-width', 0.5);

                const countryLayer = zoomLayer.append('g');
                const contentLayer = zoomLayer.append('g');
                const tooltip = d3.select(container).append('div').attr('class', 'globe-tooltip').style('position', 'absolute').style('pointer-events', 'none').style('opacity', 0);

                d3.json('https://unpkg.com/world-atlas@2/countries-110m.json').then(topo => {
                    const countries = topojson.feature(topo, topo.objects.countries);
                    countryLayer.selectAll('path').data(countries.features).join('path').attr('d', geoPath).attr('fill', '#0c1c18').attr('stroke', '#00ffcc44').attr('stroke-width', 0.6);
                }).catch(() => {}).finally(() => {
                    contentLayer.selectAll('circle.pulse').data(data).join('circle')
                        .attr('class', 'pulse-ring')
                        .attr('cx', d => { const c = projection([d.lon, d.lat]); return c ? c[0] : -9999; })
                        .attr('cy', d => { const c = projection([d.lon, d.lat]); return c ? c[1] : -9999; })
                        .attr('r', 8).attr('fill', '#00ffcc').attr('opacity', 0.4);

                    contentLayer.selectAll('circle.node').data(data).join('circle')
                        .attr('cx', d => { const c = projection([d.lon, d.lat]); return c ? c[0] : -9999; })
                        .attr('cy', d => { const c = projection([d.lon, d.lat]); return c ? c[1] : -9999; })
                        .attr('r', 4.5).attr('fill', '#050505').attr('stroke', '#00ffcc').attr('stroke-width', 2).style('cursor', 'pointer')
                        .on('mouseenter', function (event, d) {
                            d3.select(this).attr('fill', '#00ffcc');
                            tooltip.style('opacity', 1).html(`<b>[${d.source}]</b><br><a href="${d.url}" target="_blank">${d.title}</a><hr style="border-color:#333;margin:5px 0;"><span style="color:#888;">${d.published}</span>`);
                        })
                        .on('mousemove', function (event) {
                            const [mx, my] = d3.pointer(event, container);
                            tooltip.style('left', (mx + 15) + 'px').style('top', (my + 15) + 'px');
                        })
                        .on('mouseleave', function () {
                            d3.select(this).attr('fill', '#050505');
                            tooltip.style('opacity', 0);
                        });
                });

                const zoom = d3.zoom().scaleExtent([1, 8]).on('zoom', (event) => { zoomLayer.attr('transform', event.transform); });
                svg.call(zoom);
                window.zoomIn = () => svg.transition().duration(300).call(zoom.scaleBy, 1.5);
                window.zoomOut = () => svg.transition().duration(300).call(zoom.scaleBy, 1 / 1.5);
                __ZOOM_CMD__
            }

            if (isFlat) { buildFlatMap(); } else { buildGlobe(); }
        } catch (err) {
            document.getElementById('map-container').innerHTML = `<div class="error-box"><b>ERROR RENDERING MAP:</b><br>${err.message}</div>`;
        }
    </script>
</body>
</html>
"""

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
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem otomatis memperbarui berita logistik & kurs valas setiap 1 jam.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
