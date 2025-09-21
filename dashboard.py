import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

# ======================
# Bersihkan cache lama
# ======================
st.cache_data.clear()

# ======================
# Konfigurasi file
# ======================
file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
sheet_name = 'Query'

@st.cache_data
def load_data():
    df_local = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
    df_local.columns = df_local.columns.str.strip()
    return df_local

df = load_data()

# ======================
# Sidebar (dihilangkan, langsung default Topology)
# ======================
menu_option = st.radio("Pilih Tampilan:", ["Topology", "Dashboard"], horizontal=True)
search_node = st.text_input("🔍 Cari New Site ID / Destination:")

# Lock tinggi kanvas
canvas_height = 350

# helper: ambil kolom jika ada, fallback ke nama alternatif
def get_col(df, name, alt=None):
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

col_site = get_col(df, "New Site ID")
col_dest = get_col(df, "New Destenation", alt="New Destination")
col_fiber = get_col(df, "Fiber Type")
col_site_name = get_col(df, "Site Name")
col_host = get_col(df, "Host Name", alt="Hostname")
col_flp = get_col(df, "FLP Vendor")
col_flp_len = get_col(df, "FLP LENGTH")
col_syskey = get_col(df, "System Key")
col_dest_name = get_col(df, "Destination Name")

# ======================
# Main Area
# ======================
if menu_option == "Topology":
    # Judul sticky
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px; 
                   z-index:999; border-bottom:1px solid #ddd;">
            🌐 Topology Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )

    if not search_node:
        st.info("ℹ️ Masukkan **Site ID / Destination** untuk menampilkan topology.")
    else:
        mask = (
            df[col_site].astype(str).str.contains(search_node, case=False, na=False) |
            df[col_dest].astype(str).str.contains(search_node, case=False, na=False)
        )
        df_filtered = df[mask]

        if df_filtered.empty:
            st.warning("⚠️ Node tidak ditemukan di data.")
        else:
            ring_ids = df_filtered["Ring ID"].dropna().unique()

            for ring in ring_ids:
                st.subheader(f"🔗 Ring ID: {ring}")

                ring_df = df[df["Ring ID"] == ring].copy()
                ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip()
                ring_df = ring_df[ring_df[col_dest].notna() & (ring_df[col_dest].str.strip() != "")]

                # ======================
                # Topology dengan tinggi fix 350px
                # ======================
                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [
                    str(n).strip()
                    for n in nodes_order
                    if pd.notna(n) and str(n).strip().lower() not in ["", "nan", "none"]
                ]
                valid_dest_nodes = set(ring_df[col_dest].dropna().astype(str).str.strip().unique())
                valid_site_nodes = set(ring_df[col_site].dropna().astype(str).str.strip().unique())
                nodes_order = [n for n in nodes_order if n in valid_dest_nodes or n in valid_site_nodes]

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
                net.toggle_physics(False)

                # Degree nodes
                node_degree = {}
                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s:
                        node_degree[s] = node_degree.get(s, 0) + 1
                    if t:
                        node_degree[t] = node_degree.get(t, 0) + 1

                # Grid position
                max_per_row = 8
                x_spacing = 150
                y_spacing = 150
                positions = {}
                for i, nid in enumerate(nodes_order):
                    row_num = i // max_per_row
                    col_num = i % max_per_row
                    positions[nid] = (col_num * x_spacing, row_num * y_spacing)

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

                # Tambahkan node
                for nid in nodes_order:
                    nid = str(nid).strip()
                    if not nid or nid.lower() in ["nan", "none"]:
                        continue
                    if nid not in valid_dest_nodes and nid not in valid_site_nodes:
                        continue

                    info = get_node_info(nid)
                    fiber = info["Fiber Type"].strip() if info["Fiber Type"] else ""
                    if node_degree.get(nid, 0) == 1 and str(fiber).strip().lower() not in ["p0_1"]:
                        fiber = "P0"
                    f_low = fiber.lower()
                    if f_low == "dark fiber":
                        node_image = "https://img.icons8.com/ios-filled/50/007FFF/router.png"
                    elif f_low in ["p0", "p0_1"]:
                        node_image = "https://img.icons8.com/ios-filled/50/21793A/router.png"
                    else:
                        node_image = "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"

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
                        color={"border": "007FFF" if f_low=="dark fiber" else ("21793A" if f_low in ["p0","p0_1"] else "A2A2C2"),
                               "background": "white"},
                        title=title
                    )
                    added_nodes.add(nid)

                # Tambahkan edges
                edges_to_add = []
                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if not s or not t:
                        continue
                    if s.lower() in ["nan", "none"] or t.lower() in ["nan", "none"]:
                        continue
                    flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                    if s not in added_nodes:
                        net.add_node(s, label=s)
                        added_nodes.add(s)
                    if t not in added_nodes:
                        net.add_node(t, label=t)
                        added_nodes.add(t)
                    edges_to_add.append({
                        "from": s, "to": t,
                        "label": str(flp_len) if flp_len != "" else "",
                        "title": f"FLP LENGTH: {flp_len}",
                        "width": 3, "color": "black",
                        "font": {"color": "red"}, "smooth": False
                    })

                for e in edges_to_add:
                    net.edges.append(e)

                html_str = net.generate_html()
                html_str = html_str.replace(
                    '<body>',
                    '<body><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
                )
                components.html(html_str, height=canvas_height, scrolling=True)

                # ======================
                # Tabel di bawah kanvas (tidak sticky)
                # ======================
                st.markdown("## 📋 Data Ring")
                table_cols = [c for c in [
                    col_syskey, col_flp, col_site, col_site_name,
                    col_dest, col_dest_name, col_fiber, col_host
                ] if c is not None]

                st.dataframe(
                    ring_df[table_cols].reset_index(drop=True),
                    use_container_width=True,
                    height=300
                )

elif menu_option == "Dashboard":
    # Judul sticky
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px; 
                   z-index:999; border-bottom:1px solid #ddd;">
            📊 Dashboard Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"**Jumlah Ring:** {df['Ring ID'].nunique()}")
    st.markdown(f"**Jumlah Site:** {df['New Site ID'].nunique()}")
    st.markdown(f"**Jumlah Destination:** {df['New Destenation'].nunique()}")
    st.dataframe(df.head(20))
