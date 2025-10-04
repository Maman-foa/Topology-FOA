import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import re

# ======================
# Page config & style
# ======================
st.set_page_config(layout="wide", page_title="Fiber Optic Analyzer", page_icon="🧬")

st.markdown("""
<style>
body {
    background-color: #1e1f21;
    color: #f0f0f0;
}
.flex-container {
    display: flex;
    flex-wrap: wrap;
    gap: 2%;
    align-content: start;
    height: 100vh;
    padding: 8px;
    box-sizing: border-box;
}
.header, .footer {
    width: 100%;
    height: 5%;
    background: #2b2c2f;
    border-radius: 12px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 5px #000;
}
.sidebar {
    width: 25%;
    height: 75%;
    background: #2b2c2f;
    border-radius: 12px;
    padding: 12px;
    overflow-y: auto;
    box-shadow: inset 0 0 5px #000;
}
.content {
    flex-grow: 1;
    height: 75%;
    background: #2b2c2f;
    border-radius: 12px;
    padding: 12px;
    overflow-y: auto;
    box-shadow: inset 0 0 5px #000;
}
.block-container {padding-top: 0rem; padding-bottom: 0rem;}
header [data-testid="stToolbar"] {visibility: hidden; height: 0;}
[data-testid="stStatusWidget"], [data-testid="stSidebarNav"] {visibility: hidden; height: 0;}
</style>

<div class="flex-container">
  <div class="header">🧬 Topology Fiber Optic Active</div>
  <div class="sidebar" id="sidebar"></div>
  <div class="content" id="content"></div>
  <div class="footer" id="footer"></div>
</div>
""", unsafe_allow_html=True)


# ======================
# Fungsi Highlight
# ======================
def highlight_text(text, keywords):
    if not keywords:
        return text
    result = str(text)
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        result = pattern.sub(
            lambda m: f"<mark style='background-color:yellow;color:black;'>{m.group(0)}</mark>", 
            result
        )
    return result


# ======================
# Session state
# ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "do_search" not in st.session_state:
    st.session_state.do_search = False
if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""


# ======================
# Login
# ======================
def login():
    st.title("🔐 Login")
    password = st.text_input("Masukkan Password:", type="password")
    if st.button("Login"):
        if password == "Jakarta@24":
            st.session_state.authenticated = True
            st.success("Login berhasil! 🎉")
        else:
            st.error("Password salah.")

if not st.session_state.authenticated:
    login()
    st.stop()


# ======================
# Fungsi pencarian
# ======================
def trigger_search():
    st.session_state.do_search = True


# ======================
# Sidebar (Topology)
# ======================
st.markdown("<div class='sidebar'>", unsafe_allow_html=True)
st.markdown("### ⚙️ Topology")
menu_option = st.radio("Pilih Tampilan:", ["Topology"])
st.markdown("</div>", unsafe_allow_html=True)

# ======================
# Content (Kanvas)
# ======================
st.markdown("<div class='content'>", unsafe_allow_html=True)

canvas_height = 400
file_path = 'SEPTEMBER_FOA - Update_2025.xlsb'
sheet_name = 'Query CW39_2025'

if st.session_state.do_search and st.session_state.search_keyword:
    search_nodes = [s.strip() for s in st.session_state.search_keyword.split(",") if s.strip()]
    search_by = st.session_state.get("search_by", "New Site ID")
    with st.spinner("⏳ Sedang memuat data..."):
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

        def get_col(df, name, alt=None):
            if name in df.columns: return name
            if alt and alt in df.columns: return alt
            return None

        col_site = get_col(df, "New Site ID")
        col_dest = get_col(df, "New Destenation", alt="New Destination")
        col_fiber = get_col(df, "Fiber Type")
        col_ring = get_col(df, "Ring ID")

        pattern = "|".join(map(re.escape, search_nodes))
        df_filtered = df[df[col_site].astype(str).str.contains(pattern, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Node tidak ditemukan di data.")
        else:
            net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#222", directed=False)
            net.toggle_physics(False)
            for _, r in df_filtered.iterrows():
                s, t = str(r[col_site]).strip(), str(r[col_dest]).strip()
                if s and t:
                    net.add_node(s, label=s, color="#00ffff")
                    net.add_node(t, label=t, color="#ff00ff")
                    net.add_edge(s, t, color="#ff4d4d")
            html_str = net.generate_html()
            components.html(html_str, height=canvas_height, scrolling=False)
else:
    st.info("ℹ️ Masukkan keyword di bawah (bagian Footer) untuk menampilkan Topology.")

st.markdown("</div>", unsafe_allow_html=True)

# ======================
# Footer (Pencarian)
# ======================
st.markdown("<div class='footer'>", unsafe_allow_html=True)
st.markdown("### 🔍 Pencarian Data Topology")

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"], key="search_by")
with col2:
    search_input = st.text_input(
        "Masukkan keyword (pisahkan dengan koma):",
        key="search_keyword",
        placeholder="Contoh: 16SBY0267, 16SBY0497"
    )
with col3:
    if st.button("Cari Topology"):
        trigger_search()

st.markdown("</div>", unsafe_allow_html=True)
