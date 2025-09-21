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
    menu_option = st.radio("Pilih Tampilan:", ["Topology", "Dashboard"])
with col2:
    search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID"])
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
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

# ======================
# Main Area
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

    if not st.session_state.do_search or search_node.strip() == "":
        st.info("ℹ️ Pilih kategori di atas, masukkan keyword, lalu tekan Enter untuk menampilkan topology.")
    else:
        # ======================
        # Load Excel hanya saat Enter ditekan
        # ======================
        file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
        sheet_name = 'Query'
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

        # ======================
        # Kolom helper
        # ======================
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
        col_member_ring = get_col(df, "Member Ring")  # <- Tambahan

        # ======================
        # Filter data sesuai keyword
        # ======================
        if search_by == "New Site ID":
            df_filtered = df[df[col_site].astype(str).str.contains(search_node, case=False, na=False)]
        else:
            df_filtered = df[df[col_ring].astype(str).str.contains(search_node, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Node tidak ditemukan di data.")
        else:
            ring_ids = df_filtered["Ring ID"].dropna().unique()
            for ring in ring_ids:
                # Subheader Ring ID
                st.subheader(f"🔗 Ring ID: {ring}")

                ring_df = df[df["Ring ID"] == ring].copy()

                # ======================
                # Member Ring (warna abu-abu, font 14px)
                # ======================
                if col_member_ring and not ring_df.empty:
                    non_na_members = ring_df[col_member_ring].dropna()
                    members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                    st.markdown(
                        f'<p style="font-size:14px; color:gray; margin-top:-10px;">💡 Member Ring: {members_str}</p>',
                        unsafe_allow_html=True
                    )

                ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip()
                ring_df = ring_df[ring_df[col_dest].notna() & (ring_df[col_dest].str.strip() != "")]

                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "nan", "none"]]
                valid_dest_nodes = set(ring_df[col_dest].dropna().astype(str).str.strip().unique())
                valid_site_nodes = set(ring_df[col_site].dropna().astype(str).str.strip().unique())
                nodes_order = [n for n in nodes_order if n in valid_dest_nodes or n in valid_site_nodes]

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
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
                # ======================
                # Zig-zag positions
                # ======================
                positions = {}
                for i, nid in enumerate(nodes_order):
                    row = i // max_per_row
                    col_in_row = i % max_per_row
                    if row % 2 == 1:  # baris genap → kanan ke kiri
                        col = max_per_row - 1 - col_in_row
                    else:  # baris ganjil → kiri ke kanan
                        col = col_in_row
                    x = col * x_spacing
                    y = row * y_spacing
                    positions[nid] = (x, y)

                added_nodes = set()
                def get_node_info(nid):
                    df_match = ring_df[ring_df[col_site].astype(str).str.strip() == nid]
                    if df_match.empty:
                        df_match = ring_df[ring_df[col_dest].astype(str).str.strip() == nid]
                    if df_match.empty:
                        return {"Fiber Type": "", "Site Name": "", "Host Name": "", "FLP Vendor": ""}
                    row0 = df_match.iloc[0]
                    return {
                        "Fiber Type": str(row0[col_fiber]) if col_fiber in row0 and pd.notna(row0[col_fiber]) else "",
                        "Site Name": str(row0[col_site_name]) if col_site_name in row0 and pd.notna(row0[col_site_name]) else "",
                        "Host Name": str(row0[col_host]) if col_host in row0 and pd.notna(row0[col_host]) else "",
                        "FLP Vendor": str(row0[col_flp]) if col_flp in row0 and pd.notna(row0[col_flp]) else ""
                    }

                for nid in nodes_order:
                    info = get_node_info(nid)
                    fiber = info["Fiber Type"].strip() if info["Fiber Type"] else ""
                    if node_degree.get(nid, 0) == 1 and fiber.lower() not in ["p0_1"]:
                        fiber = "P0"
                    f_low = fiber.lower()
                    node_image = (
                        "https://img.icons8.com/ios-filled/50/007FFF/router.png" if f_low=="dark fiber" else
                        "https://img.icons8.com/ios-filled/50/21793A/router.png" if f_low in ["p0","p0_1"] else
                        "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"
                    )

                    label_parts = [fiber, nid]
                    if info["Site Name"]:
                        label_parts.append(info["Site Name"])
                    if info["Host Name"]:
                        label_parts.append(info["Host Name"])
                    if info["FLP Vendor"]:
                        label_parts.append(info["FLP Vendor"])
                    title = "<br>".join([p for p in label_parts if p])

                    x, y = positions.get(nid, (0,0))
                    net.add_node(
                        nid,
                        label="\n".join(label_parts),
                        x=x, y=y,
                        physics=False,
                        size=50,
                        shape="image",
                        image=node_image,
                        color={"border": "007FFF" if f_low=="dark fiber" else ("21793A" if f_low in ["p0","p0_1"] else "A2A2C2"), "background": "white"},
                        title=title
                    )
                    added_nodes.add(nid)

                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s and t and s.lower() not in ["nan","none"] and t.lower() not in ["nan","none"]:
                        flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                        if s not in added_nodes:
                            net.add_node(s, label=s)
                            added_nodes.add(s)
                        if t not in added_nodes:
                            net.add_node(t, label=t)
                            added_nodes.add(t)
                        net.add_edge(
                            s,
                            t,
                            label=str(flp_len) if flp_len else "",
                            title=f"FLP LENGTH: {flp_len}",
                            width=3,
                            color="red",
                            smooth=False
                        )

                html_str = net.generate_html()
                html_str = html_str.replace(
                    '<body>',
                    '<body><div class="canvas-border"><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
                )
                components.html(html_str, height=canvas_height, scrolling=False)

                # ======================
                # Tambahkan tabel Excel di bawah canvas masing-masing Ring
                # ======================
                table_cols = [
                    col_syskey, col_flp, col_site, col_site_name, col_dest,
                    col_dest_name, col_fiber, col_ring, col_host
                ]
                table_cols = [c for c in table_cols if c in ring_df.columns]
                st.markdown("### 📋 Data Ring")
                st.dataframe(ring_df[table_cols].reset_index(drop=True), use_container_width=True, height=300)

elif menu_option == "Dashboard":
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px;
                   z-index:999; border-bottom:1px solid #ddd; margin:0;">
            📊 Dashboard Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )
    # Load Excel untuk dashboard
    file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
    sheet_name = 'Query'
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
    df.columns = df.columns.str.strip()
    st.markdown(f"**Jumlah Ring:** {df['Ring ID'].nunique()}")
    st.markdown(f"**Jumlah Site:** {df['New Site ID'].nunique()}")
    st.markdown(f"**Jumlah Destination:** {df['New Destenation'].nunique()}")
    st.dataframe(df.head(20))
