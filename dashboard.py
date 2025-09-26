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
    [data-testid="stSidebar"] > div:first-child { padding-top: 60px; }
    header [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    [data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
    [data-testid="stSidebarNav"] {visibility: hidden; height: 0;}
    mark { background-color: yellow; color: black; }
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
    st.title("🔐 Login")
    password = st.text_input("Masukkan Password:", type="password")
    if st.button("Login"):
        if password == "Jakarta@24":
            st.session_state.authenticated = True
            st.success("Login berhasil!")
            st.experimental_rerun()   # gunakan experimental_rerun
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
# Helper function
# ======================
def get_col(df, name, alt=None):
    if name in df.columns: return name
    if alt and alt in df.columns: return alt
    return None

# ======================
# Main Area
# ======================
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <h2 style="position:sticky; top:0; background-color:white;
    padding:12px; z-index:999; border-bottom:1px solid #ddd; margin:0;">
        🧬 Topology Fiber Optic Active
    </h2>
    """, unsafe_allow_html=True
)

if not st.session_state.do_search or search_node.strip() == "":
    st.info("ℹ️ Pilih kategori di atas, masukkan keyword, lalu tekan Enter.")
else:
    with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
        file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
        sheet_name = 'Query'
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

        col_site = get_col(df, "New Site ID")
        col_dest = get_col(df, "New Destenation", alt="New Destination")
        col_fiber = get_col(df, "Fiber Type")
        col_site_name = get_col(df, "Site Name")
        col_host = get_col(df, "Host Name", alt="Hostname")
        col_flp = get_col(df, "FLP Vendor")
        col_flp_len = get_col(df, "FLP LENGTH")
        col_syskey = get_col(df, "System Key")
        col_dest_name = get_col(df, "Destination Name")
        col_ring = get_col(df, "Ring ID")
        col_member_ring = get_col(df, "Member Ring")

        # Filter data sesuai pencarian
        if search_by == "New Site ID":
            df_filtered = df[df[col_site].astype(str).str.contains(search_node, case=False, na=False)]
        elif search_by == "Ring ID":
            df_filtered = df[df[col_ring].astype(str).str.contains(search_node, case=False, na=False)]
        else:
            df_filtered = df[df[col_host].astype(str).str.contains(search_node, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Node tidak ditemukan.")
        else:
            ring_ids = df_filtered[col_ring].dropna().unique()
            for ring in ring_ids:
                # GANTI: gunakan st.markdown agar HTML <mark> boleh dipakai
                st.markdown(f"### 🔗 Ring ID: <mark>{ring}</mark>", unsafe_allow_html=True)

                ring_df = df[df[col_ring] == ring].copy()
                if col_member_ring and not ring_df.empty:
                    non_na_members = ring_df[col_member_ring].dropna()
                    members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                    st.markdown(
                        f'<p style="font-size:14px; color:gray; margin-top:-10px;">💡 Member Ring: <mark>{members_str}</mark></p>',
                        unsafe_allow_html=True
                    )

                ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip().replace({"nan": ""})

                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [n for n in nodes_order if str(n).strip() not in ["", "nan", "none"]]

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
                net.toggle_physics(False)

                # posisi zig-zag
                max_per_row, x_spacing, y_spacing = 8, 200, 200
                positions = {}
                for i, nid in enumerate(nodes_order):
                    row, col_in_row = divmod(i, max_per_row)
                    col = max_per_row - 1 - col_in_row if row % 2 else col_in_row
                    positions[nid] = (col * x_spacing, row * y_spacing)

                added_nodes = set()
                for nid in nodes_order:
                    df_match = ring_df[(ring_df[col_site]==nid) | (ring_df[col_dest]==nid)]
                    row0 = df_match.iloc[0] if not df_match.empty else {}
                    fiber = str(row0.get(col_fiber,"")).strip().lower() if row0 else ""
                    ftype = "P0" if fiber=="" else fiber

                    node_image = (
                        "https://img.icons8.com/ios-filled/50/007FFF/router.png" if fiber=="dark fiber" else
                        "https://img.icons8.com/ios-filled/50/21793A/router.png" if fiber in ["p0","p0_1"] else
                        "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"
                    )

                    # Highlight merah kalau match (search_node mungkin kosong, guard)
                    is_match = False
                    if isinstance(search_node, str) and search_node.strip():
                        try:
                            host_val = str(row0.get(col_host,"")).lower() if row0 else ""
                        except Exception:
                            host_val = ""
                        is_match = (search_node.lower() in nid.lower()) or (search_node.lower() in host_val)

                    border_color = "red" if is_match else (
                        "007FFF" if fiber=="dark fiber" else "21793A" if fiber in ["p0","p0_1"] else "A2A2C2"
                    )

                    x, y = positions.get(nid,(0,0))
                    net.add_node(
                        nid,
                        label=nid,
                        x=x, y=y,
                        physics=False,
                        size=50,
                        shape="image",
                        image=node_image,
                        color={"border": border_color, "background":"white"}
                    )
                    added_nodes.add(nid)

                for _, r in ring_df.iterrows():
                    s, t = str(r[col_site]).strip(), str(r[col_dest]).strip()
                    if s and t and s not in ["nan","none"] and t not in ["nan","none"]:
                        flp_len = r[col_flp_len] if pd.notna(r[col_flp_len]) else ""
                        net.add_edge(s, t, label=str(flp_len) if flp_len else "", width=3, color="red", smooth=False)

                html_str = net.generate_html()
                html_str = html_str.replace('<body>', '<body><div class="canvas-border">')
                components.html(html_str, height=canvas_height, scrolling=False)

                # Tabel member ring
                table_cols = [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host]
                st.markdown("### 📋 Member Ring")
                display_df = ring_df[table_cols].fillna("").reset_index(drop=True)
                st.dataframe(display_df, use_container_width=True, height=300)
