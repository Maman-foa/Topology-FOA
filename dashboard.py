import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# ======================
# Page config & CSS (Hacker Style)
# ======================
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: black;
        color: #00FF00;
        font-family: 'Courier New', Courier, monospace;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        background-color: black;
        color: #00FF00;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 60px;
        background-color: #111;
        color: #00FF00;
    }
    header, [data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stSidebarNav"] {
        visibility: hidden;
        height: 0;
    }
    h2 {
        color: #00FF00 !important;
        font-family: 'Courier New', monospace;
    }
    .stButton>button {
        background-color: #111;
        color: #00FF00;
        border: 1px solid #00FF00;
    }
    .stTextInput>div>input {
        background-color: black;
        color: #00FF00;
        border: 1px solid #00FF00;
    }
    .canvas-border {
        border: 3px solid #00FF00;
        border-radius: 5px;
    }
    .vis-network {
        background-color: black !important;
        color: #00FF00 !important;
        font-family: 'Courier New', monospace;
        background-image: linear-gradient(to right, #00FF00 1px, transparent 1px), linear-gradient(to bottom, #00FF00 1px, transparent 1px);
        background-size: 30px 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
# Password Login
# ======================
def login():
    st.markdown("<h1 style='color:#00FF00; font-family:Courier;'>🔐 Hacker Terminal Login</h1>", unsafe_allow_html=True)
    password = st.text_input("Masukkan Password:", type="password", key="pass_input")
    if st.button("Login"):
        if password == "Jakarta@24":
            st.session_state.authenticated = True
            st.success("✅ Login berhasil!")
            st.rerun()
        else:
            st.error("❌ Password salah.")

if not st.session_state.authenticated:
    login()
    st.stop()

# ======================
# Fungsi pencarian
# ======================
def trigger_search():
    st.session_state.do_search = True

# ======================
# Menu + Search
# ======================
col1, col2, col3 = st.columns([1,2,2])
with col1:
    menu_option = st.radio("Pilih Tampilan:", ["Topology"])
with col2:
    search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
with col3:
    search_node = st.text_input(
        "🔍 Masukkan keyword:",
        key="search_keyword",
        placeholder="Ketik lalu tekan Enter",
        on_change=trigger_search
    )

canvas_height = 350

# ======================
# Judul hacker style sticky
# ======================
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <h2 style="
        position:sticky; 
        top:0;  
        background-color:black; 
        padding:12px;
        z-index:999; 
        border-bottom:1px solid #00FF00; 
        margin:0;
        font-family: 'Courier New', monospace;
        color:#00FF00;
    ">
        🧬 Hacker Topology Terminal
    </h2>
    """,
    unsafe_allow_html=True
)

# ======================
# Konten utama tanpa mengubah logika asli
# ======================
if not st.session_state.do_search or search_node.strip() == "":
    st.info("ℹ️ Pilih kategori di atas, masukkan keyword, lalu tekan Enter untuk menampilkan topology.", icon="💡")
else:
    with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
        file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
        sheet_name = 'Query'
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

        # Kolom helper sama seperti skrip asli
        col_site = "New Site ID"
        col_dest = "New Destenation"
        col_fiber = "Fiber Type"
        col_site_name = "Site Name"
        col_host = "Host Name"
        col_flp = "FLP Vendor"
        col_flp_len = "FLP LENGTH"
        col_syskey = "System Key"
        col_dest_name = "Destination Name"
        col_ring = "Ring ID"
        col_member_ring = "Member Ring"

        if search_by == "New Site ID":
            df_filtered = df[df[col_site].astype(str).str.contains(search_node, case=False, na=False)]
        elif search_by == "Ring ID":
            df_filtered = df[df[col_ring].astype(str).str.contains(search_node, case=False, na=False)]
        else:
            df_filtered = df[df[col_host].astype(str).str.contains(search_node, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Node tidak ditemukan di data.")
        else:
            ring_ids = df_filtered["Ring ID"].dropna().unique()
            for ring in ring_ids:
                st.subheader(f"🔗 Ring ID: {ring}")

                ring_df = df[df["Ring ID"] == ring].copy()

                if col_member_ring and not ring_df.empty:
                    non_na_members = ring_df[col_member_ring].dropna()
                    members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                    st.markdown(
                        f'<p style="font-size:14px; color:#00FF00; margin-top:-10px;">💡 Member Ring: {members_str}</p>',
                        unsafe_allow_html=True
                    )

                # Logika original tanpa perubahan
                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]
                valid_dest_nodes = set(ring_df[col_dest].dropna().astype(str).str.strip().unique())
                valid_site_nodes = set(ring_df[col_site].dropna().astype(str).str.strip().unique())
                nodes_order = [n for n in nodes_order if n in valid_dest_nodes or n in valid_site_nodes]

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="black", font_color="#00FF00", directed=False)
                net.toggle_physics(False)

                node_degree = {}
                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s:
                        node_degree[s] = node_degree.get(s, 0) + 1
                    if t:
                        node_degree[t] = node_degree.get(t, 0) + 1

                max_per_row = 8
                x_spacing = 200
                y_spacing = 200
                positions = {}
                for i, nid in enumerate(nodes_order):
                    row = i // max_per_row
                    col_in_row = i % max_per_row
                    if row % 2 == 1:
                        col = max_per_row - 1 - col_in_row
                    else:
                        col = col_in_row
                    x = col * x_spacing
                    y = row * y_spacing
                    positions[nid] = (x, y)

                added_nodes = set()
                for nid in nodes_order:
                    x, y = positions.get(nid, (0,0))
                    net.add_node(nid, label=nid, x=x, y=y, physics=False, size=50, color={"border": "#00FF00", "background": "black"}, font={"color": "#00FF00"})

                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s and t and s.lower() not in ["nan","none"] and t.lower() not in ["nan","none"]:
                        flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                        if s not in added_nodes:
                            net.add_node(s, label=s, color="#00FF00")
                            added_nodes.add(s)
                        if t not in added_nodes:
                            net.add_node(t, label=t, color="#00FF00")
                            added_nodes.add(t)
                        net.add_edge(s, t, label=str(flp_len), width=3, color="#00FF00", smooth=False)

                html_str = net.generate_html()
                html_str = html_str.replace('<body>', '<body><div class="canvas-border"></div>')
                components.html(html_str, height=canvas_height, scrolling=False)

                st.markdown("### 📋 Member Ring", unsafe_allow_html=True)
                table_cols = [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host]
                display_df = ring_df[table_cols].fillna("").reset_index(drop=True)
                st.dataframe(display_df, use_container_width=True, height=300)
