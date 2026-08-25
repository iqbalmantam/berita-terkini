import time
import streamlit as st
import requests
from deep_translator import GoogleTranslator
from streamlit_autorefresh import st_autorefresh
import json

# TTL cache: 1 jam kalau fetch terakhir SUKSES, 5 menit kalau terakhir GAGAL
# (biar cepat retry, tidak nyangkut di fallback statis selama 1 jam penuh)
LIVE_TTL = 3600
RETRY_TTL = 300


@st.cache_resource
def _get_cache_store(name: str):
    """Wadah state persisten lintas rerun & lintas user (mirip st.cache_data,
    tapi TTL-nya kita kontrol manual sesuai sukses/gagalnya fetch terakhir)."""
    return {"data": None, "timestamp": 0.0, "is_live": False}

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
    
    @keyframes autoScroll {
        0% { transform: translateY(0); }
        100% { transform: translateY(-50%); }
    }
    .ticker-container:hover .ticker-track {
        animation-play-state: paused;
    }
</style>
""", unsafe_allow_html=True)

# Auto-Refresh setiap 1 Jam (3600 detik)
st_autorefresh(interval=3600 * 1000, key="osint_refresher")

# Translator
@st.cache_resource
def get_translator():
    return GoogleTranslator(source='auto', target='id')

translator = get_translator()


def translate_title(text: str, max_retries: int = 2) -> str:
    """Terjemahkan judul ke Indonesia dengan retry + backoff singkat.
    Kalau semua percobaan gagal (rate-limit/blokir/timeout), balik ke teks asli
    supaya berita tetap tampil (tidak kosong), cuma tidak terjemahan."""
    for attempt in range(max_retries):
        try:
            result = translator.translate(text)
            if result:
                return result
        except Exception:
            pass
        time.sleep(0.4 * (attempt + 1))  # backoff singkat sebelum coba lagi
    return text

# Fungsi Ambil Data Kurs Valas Live & Update Otomatis per 1 Jam
def fetch_forex_rates():
    store = _get_cache_store("forex")
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

    # Fetch gagal -> pakai data live terakhir yang masih ada (kalau ada),
    # kalau belum pernah sukses sama sekali baru pakai default_rates.
    fallback = store["data"] if store["data"] is not None else default_rates
    store["data"] = fallback
    store["timestamp"] = now
    store["is_live"] = False
    return fallback

forex_rates = fetch_forex_rates()

# Fallback Data OSINT Berita
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

def fetch_live_news():
    store = _get_cache_store("news")
    now = time.time()
    ttl = LIVE_TTL if store["is_live"] else RETRY_TTL
    if store["data"] is not None and (now - store["timestamp"]) < ttl:
        return store["data"]

    articles_list = []
    error_reason = None
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc?query=geopolitics%20OR%20war%20OR%20economy%20OR%20defense&mode=artlist&maxrecords=25&format=json"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            error_reason = f"GDELT balas HTTP {response.status_code}"
        else:
            try:
                data = response.json()
            except ValueError:
                data = {}
                error_reason = f"Respons GDELT bukan JSON valid (potongan: {response.text[:120]!r})"

            articles = data.get("articles", [])
            if not articles and not error_reason:
                error_reason = "GDELT mengembalikan 0 artikel untuk query ini"

            regions_pool = ["world", "americas", "europe", "middle_east", "asia_pacific", "africa"]
            for idx, art in enumerate(articles):
                title_en = art.get("title", "")
                if not title_en:
                    continue
                title_id = translate_title(title_en)
                time.sleep(0.15)  # jeda kecil antar-artikel, hindari burst request
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
    except requests.exceptions.Timeout:
        error_reason = "Timeout menghubungi GDELT (>10 detik)"
    except requests.exceptions.ConnectionError as e:
        error_reason = f"Gagal konek ke GDELT: {e}"
    except Exception as e:
        error_reason = f"Error tak terduga: {type(e).__name__}: {e}"

    if len(articles_list) >= 8:
        # Fetch sukses dengan hasil cukup banyak -> simpan sebagai data live, TTL 1 jam
        store["data"] = articles_list
        store["timestamp"] = now
        store["is_live"] = True
        store["last_error"] = None
        return articles_list

    # Fetch gagal / hasil terlalu sedikit -> pakai data live terakhir yang masih
    # ada (kalau ada), baru jatuh ke DEFAULT_OSINT_DATA kalau belum pernah sukses.
    # TTL dipersingkat jadi 5 menit supaya cepat dicoba ulang.
    store["last_error"] = error_reason or f"Cuma {len(articles_list)} artikel valid (minimal butuh 8)"
    fallback = store["data"] if store["data"] is not None else (articles_list + DEFAULT_OSINT_DATA)
    store["data"] = fallback
    store["timestamp"] = now
    store["is_live"] = False
    return fallback

st.markdown("### ⚡ CRUCIX // GLOBAL & REGIONAL OSINT TERMINAL")
st.markdown("<span style='color: #888; font-size: 0.85em;'>INITIALIZING INTEL ENGINE · LIVE FEED · AUTO-TRANSLATE ACTIVE (UPDATES EVERY 1H)</span>", unsafe_allow_html=True)

news_items = fetch_live_news()
_news_status = _get_cache_store("news")
if _news_status.get("is_live"):
    st.markdown("<span style='color:#00ffcc; font-size:0.78em;'>● LIVE — data GDELT berhasil diambil</span>", unsafe_allow_html=True)
else:
    _reason = _news_status.get("last_error", "alasan tidak diketahui")
    st.markdown(f"<span style='color:#ffaa00; font-size:0.78em;'>● FALLBACK — {_reason}</span>", unsafe_allow_html=True)

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
    <script src="https://unpkg.com/d3@7"></script>
    <script src="https://unpkg.com/topojson-client@3"></script>
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
        const povLat = __POV_LAT__, povLng = __POV_LNG__, povAlt = __POV_ALT__;
        const container = document.getElementById('map-container');
        const arcsData = data.map((d, i) => {
            const target = data[(i + 2) % data.length];
            return { startLat: d.lat, startLng: d.lon, endLat: target.lat, endLng: target.lon, color: ['#00ffcc', '#0044ff'] };
        });
        const tooltipHtml = d => `<div class="globe-tooltip"><b>[${d.region.toUpperCase()}]</b><br><a href="${d.url}" target="_blank">${d.title}</a><br><hr style="border-color: #333; margin: 6px 0;"><span style="color: #888;">SRC: ${d.source} | ${d.date}</span></div>`;

        // ---------- MODE 1: GLOBE 3D ----------
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
        }

        // ---------- MODE 2: PETA DATAR 2D (proyeksi equirectangular asli) ----------
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
                .catch(() => { /* peta negara opsional; titik & garis tetap tampil tanpa itu */ })
                .finally(() => drawPointsAndArcs());

            function drawPointsAndArcs() {
                const arcsG = contentLayer.append('g');
                arcsData.forEach(a => {
                    const p1 = projection([a.startLng, a.startLat]);
                    const p2 = projection([a.endLng, a.endLat]);
                    if (!p1 || !p2) return;
                    const mx = (p1[0] + p2[0]) / 2, my = (p1[1] + p2[1]) / 2 - 45;
                    arcsG.append('path')
                        .attr('d', `M${p1[0]},${p1[1]} Q${mx},${my} ${p2[0]},${p2[1]}`)
                        .attr('fill', 'none').attr('stroke', '#00ffcc55').attr('stroke-width', 1);
                });

                const tooltip = d3.select(container).append('div')
                    .style('position', 'absolute').style('pointer-events', 'none')
                    .style('opacity', 0).style('z-index', 100).style('transition', 'opacity 0.15s');

                contentLayer.append('g').selectAll('circle').data(data).join('circle')
                    .attr('cx', d => projection([d.lon, d.lat])[0])
                    .attr('cy', d => projection([d.lon, d.lat])[1])
                    .attr('r', 4.5).attr('fill', '#00ffcc')
                    .attr('stroke', '#00ffcc').attr('stroke-width', 6).attr('stroke-opacity', 0.15)
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
    .replace("__FLAT_MODE__", "true" if st.session_state.flat_mode else "false")
)

st.iframe(map_html, height=520)

st.markdown("---")

# Layout 2 Kolom: Kiri = Live News Ticker (Auto-Scroll), Kanan = Kurs Beli & Jual Valas terhadap IDR
left_col, right_col = st.columns([1.3, 1])

with left_col:
    cards_html = ""
    for item in news_items:
        cards_html += f'<div style="background: #080808; border: 1px solid #161616; border-bottom: 1px solid #1f1f1f; padding: 12px 15px; margin-bottom: 8px;"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;"><span style="background: #0c1412; border: 1px solid #00ffcc55; color: #00ffcc; font-size: 9px; padding: 2px 7px; font-family: \'Courier New\', Courier, monospace;">{item["source"]}</span><span style="font-size: 10px; color: #777; font-family: \'Courier New\', Courier, monospace;">{item["date"]}</span></div><a href="{item["url"]}" target="_blank" style="color: #ddd; text-decoration: none; font-size: 12px; font-family: \'Courier New\', Courier, monospace; display: block; line-height: 1.4;">{item["title"]}</a><div style="font-size: 11px; color: #00ffcc55; margin-top: 6px;">&nearr;</div></div>'

    ticker_widget_html = f"""<div style="background: #060606; border: 1px solid #1f1f1f; border-radius: 4px; padding: 15px;"><div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 10px;"><span style="font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #00ffcc;">LIVE NEWS TICKER (AUTO-SCROLL)</span><span style="background: #0d1a17; border: 1px solid #00ffcc55; color: #00ffcc; padding: 2px 10px; font-size: 11px; font-family: 'Courier New', Courier, monospace;">{len(news_items)} ITEMS</span></div><div class="ticker-container" style="height: 520px; overflow: hidden; position: relative;"><div class="ticker-track" style="position: absolute; width: 100%; animation: autoScroll 35s linear infinite;">{cards_html}{cards_html}</div></div></div>"""
    st.markdown(ticker_widget_html, unsafe_allow_html=True)

with right_col:
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

    forex_widget_html = f"""<div style="background: #060606; border: 1px solid #1f1f1f; border-radius: 4px; padding: 15px;"><div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 10px;"><span style="font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; color: #00ffcc;">KURS VALUTA ASING (BELI & JUAL)</span><span style="background: #0d1a17; border: 1px solid #00ffcc55; color: #00ffcc; padding: 2px 10px; font-size: 11px; font-family: 'Courier New', Courier, monospace;">AUTO-UPDATE 1H</span></div><div style="max-height: 520px; overflow-y: auto; padding-right: 4px;">{forex_cards_html}</div></div>"""
    st.markdown(forex_widget_html, unsafe_allow_html=True)

# Footer & Watermark
st.markdown("---")
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("<span style='color: gray; font-size: 0.82em;'>⚙️ Sistem OSINT otomatis memperbarui berita & kurs tiap 1 jam.</span>", unsafe_allow_html=True)
with footer_col2:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'><b>Developed by iqbalmantam</b></div>", unsafe_allow_html=True)
