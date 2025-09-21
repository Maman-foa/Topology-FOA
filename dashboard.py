import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    .canvas-border { border: 3px solid #333333; border-radius: 5px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# Session state
# ======================
if 'do_search' not in st.session_state:
    st.session_state.do_search = False
if 'search_keyword' not in st.session_state:
    st.session_state.search_keyword = ""

def trigger_search():
    st.session_state.do_search = True

# ======================
# Menu + Search
# ======================
col1, col2, col3 = st.columns([1,2,2])
with col1:
    menu_option = st.radio("Pilih Tampilan:", ["Topology", "FLP Vendor"])

if menu_option == "Topology":
    with col2:
        search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
    with col3:
        search_node = st.text_input(
            "🔍 Masukkan keyword:",
            key="search_keyword",
            placeholder="Ketik lalu tekan Enter",
            on_change=trigger_search
        )
else:  # FLP Vendor
    search_by = "FLP Vendor"
    with col2:
        st.markdown("**Cari berdasarkan:** FLP Vendor")
    with col3:
        search_node = st.text_input(
            "🏭 Masukkan nama vendor:",
            key="search_keyword",
            placeholder="Ketik nama vendor lalu tekan Enter",
            on_change=trigger_search
        )

canvas_height = 900

# ======================
# Helper function
# ======================
def get_col(df, name, alt=None):
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

# ======================
# Judul Utama
# ======================
if menu_option == "Topology":
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px;
                   z-index:999; border-bottom:1px solid #ddd; margin:0;">
            🧬 Topology Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px;
                   z-index:999; border-bottom:1px solid #ddd; margin:0;">
            🏭 FLP Vendor Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )

# ======================
# Konten (gabungan semua ring, node dikelompokkan per ring)
# ======================
if not st.session_state.do_search or search_node.strip() == "":
    st.info("ℹ️ Pilih kategori di atas, masukkan keyword, lalu tekan Enter untuk menampilkan data.")
else:
    file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
    sheet_name = 'Query'
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
    df.columns = df.columns.str.strip()

    # Kolom helper
    col_site = get_col(df, "New Site ID")
    col_dest = get_col(df, "New Destenation", alt="New Destination")
    col_fiber = get_col(df, "Fiber Type")
    col_site_name = get_col(df, "Site Name")
    col_host = get_col(df, "Host Name", alt="Hostname")
    col_flp = get_col(df, "FLP Vendor")
    col_flp_len = get_col(df, "FLP LENGTH")
    col_ring = get_col(df, "Ring ID")

    # Filter data sesuai pencarian
    if menu_option == "Topology":
        if search_by == "New Site ID":
            df_filtered = df[df[col_site].astype(str).str.contains(search_node, case=False, na=False)]
        elif search_by == "Ring ID":
            df_filtered = df[df[col_ring].astype(str).str.contains(search_node, case=False, na=False)]
        else:  # Host Name
            df_filtered = df[df[col_host].astype(str).str.contains(search_node, case=False, na=False)]
    else:  # FLP Vendor
        df_filtered = df[df[col_flp].astype(str).str.contains(search_node, case=False, na=False)]

    if df_filtered.empty:
        st.warning("⚠️ Data tidak ditemukan.")
    else:
        # Buat 1 Network untuk semua ring
        net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
        net.force_atlas_2based()

        added_nodes = set()
        for _, r in df_filtered.iterrows():
            s = str(r[col_site]).strip() if pd.notna(r[col_site]) else ""
            t = str(r[col_dest]).strip() if pd.notna(r[col_dest]) else ""
            ring = str(r[col_ring]) if pd.notna(r[col_ring]) else "Unknown"
            vendor = str(r[col_flp]) if col_flp in r and pd.notna(r[col_flp]) else ""
            host = str(r[col_host]) if col_host in r and pd.notna(r[col_host]) else ""

            if s and s not in added_nodes:
                net.add_node(
                    s,
                    label=f"{s}\n{host}\n({vendor})",
                    size=25,
                    group=ring,   # group berdasarkan Ring ID
                    title=f"Ring: {ring}"
                )
                added_nodes.add(s)
            if t and t not in added_nodes:
                net.add_node(
                    t,
                    label=f"{t}\n({vendor})",
                    size=25,
                    group=ring,
                    title=f"Ring: {ring}"
                )
                added_nodes.add(t)

            if s and t:
                flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                net.add_edge(s, t, label=str(flp_len) if flp_len else "", color="red", width=2)

        # Tampilkan
        html_str = net.generate_html()
        html_str = html_str.replace(
            '<body>',
            '<body><div class="canvas-border"><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
        )
        components.html(html_str, height=canvas_height, scrolling=True)
