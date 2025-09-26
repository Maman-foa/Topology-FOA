import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide", page_title="Topology Fiber Optic", page_icon="🧬")

st.markdown(
    """
    <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f9f9f9;
        color: #222;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3 {
        color: #003366;
    }
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 4px;
    }
    .stTextInput>div>input {
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 4px;
    }
    .canvas-border {
        border: 2px solid #003366;
        border-radius: 8px;
        padding: 5px;
        background: white;
    }
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: white;
        padding: 10px;
        border-bottom: 2px solid #003366;
        z-index: 999;
    }
    .search-section {
        background-color: #f1f1f1;
        padding: 10px;
        border-radius: 6px;
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
# Login Section
# ======================
def login():
    st.markdown("<h1 style='color:#003366;'>🔐 Login Fiber Optic Topology</h1>", unsafe_allow_html=True)
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
# Search Section
# ======================
def trigger_search():
    st.session_state.do_search = True

with st.container():
    with st.expander("🔍 Cari Topology", expanded=True):
        col1, col2, col3 = st.columns([1, 2, 2], gap="large")
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

canvas_height = 400

# ======================
# Sticky Title Header
# ======================
st.markdown(
    """
    <div class="sticky-header">
        <h2>🧬 Topology Fiber Optic Active</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# ======================
# Main Content
# ======================
if not st.session_state.do_search or search_node.strip() == "":
    st.info("ℹ️ Pilih kategori di atas, masukkan keyword, lalu tekan Enter untuk menampilkan topology.", icon="💡")
else:
    with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
        file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
        sheet_name = 'Query'
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

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
                        f'<p style="font-size:14px; color:#555;">💡 Member Ring: {members_str}</p>',
                        unsafe_allow_html=True
                    )

                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]
                valid_dest_nodes = set(ring_df[col_dest].dropna().astype(str).str.strip().unique())
                valid_site_nodes = set(ring_df[col_site].dropna().astype(str).str.strip().unique())
                nodes_order = [n for n in nodes_order if n in valid_dest_nodes or n in valid_site_nodes]

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#ffffff", font_color="#003366", directed=False)
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
                    net.add_node(nid, label=nid, x=x, y=y, physics=False, size=50, color={"border": "#003366", "background": "#f0f0f0"}, font={"color": "#003366"})

                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s and t and s.lower() not in ["nan","none"] and t.lower() not in ["nan","none"]:
                        flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                        if s not in added_nodes:
                            net.add_node(s, label=s, color="#003366")
                            added_nodes.add(s)
                        if t not in added_nodes:
                            net.add_node(t, label=t, color="#003366")
                            added_nodes.add(t)
                        net.add_edge(s, t, label=str(flp_len), width=3, color="#003366", smooth=False)

                html_str = net.generate_html()
                html_str = html_str.replace('<body>', '<body><div class="canvas-border"></div>')
                components.html(html_str, height=canvas_height, scrolling=False)

                st.markdown("### 📋 Member Ring", unsafe_allow_html=True)
                table_cols = [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host]
                display_df = ring_df[table_cols].fillna("").reset_index(drop=True)
                st.dataframe(display_df, use_container_width=True, height=300)
