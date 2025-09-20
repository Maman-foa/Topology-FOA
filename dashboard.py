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
    # baca semua kolom sebagai string sedapat mungkin untuk konsistensi
    df_local = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
    # strip header whitespace
    df_local.columns = df_local.columns.str.strip()
    return df_local

df = load_data()

# ======================
# Sidebar
# ======================
st.sidebar.header("⚙️ Menu")
menu_option = st.sidebar.radio("Pilih Tampilan:", ["Topology", "Dashboard"])
search_node = st.sidebar.text_input("🔍 Cari New Site ID / Destination:")

# helper: ambil kolom jika ada, fallback ke nama alternatif
def get_col(df, name, alt=None):
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

col_site = get_col(df, "New Site ID")
col_dest = get_col(df, "New Destenation", alt="New Destination")  # menjaga ejaan user
col_fiber = get_col(df, "Fiber Type")
col_site_name = get_col(df, "Site Name")
col_host = get_col(df, "Host Name", alt="Hostname")
col_flp = get_col(df, "FLP Vendor")
col_flp_len = get_col(df, "FLP LENGTH")

# ======================
# Main Area
# ======================
if menu_option == "Topology":
    st.markdown("<h2 style='color:white;'>🧬 Topology Fiber Optic Active</h2>", unsafe_allow_html=True)

    # Filter source data berdasarkan search (jika ada)
    if search_node:
        mask = (
            df[col_site].astype(str).str.contains(search_node, case=False, na=False) |
            df[col_dest].astype(str).str.contains(search_node, case=False, na=False)
        )
        df_filtered = df[mask]
    else:
        df_filtered = df

    if df_filtered.empty:
        st.warning("⚠️ Node tidak ditemukan di data.")
    else:
        ring_ids = df_filtered["Ring ID"].dropna().unique()

        for ring in ring_ids:
            st.subheader(f"🔗 Ring ID: {ring}")

            ring_df = df[df["Ring ID"] == ring].copy()
            # pastikan ID konsisten string + strip
            ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
            ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip()

            # ambil semua node unik (pakai set of strings)
            nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
            nodes_order = [n for n in nodes_order if str(n).strip() != "nan" and str(n).strip() != ""]  # hapus kosong

            # Network init
            net = Network(height="85vh", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
            net.toggle_physics(False)  # matikan physics global supaya kaku

            # prepare maps & degree
            node_degree = {}
            for _, r in ring_df.iterrows():
                s = str(r[col_site]).strip()
                t = str(r[col_dest]).strip()
                if s:
                    node_degree[s] = node_degree.get(s, 0) + 1
                if t:
                    node_degree[t] = node_degree.get(t, 0) + 1

            # buat posisi grid
            max_per_row = 8
            x_spacing = 150
            y_spacing = 150
            positions = {}
            for i, nid in enumerate(nodes_order):
                row_num = i // max_per_row
                col_num = i % max_per_row
                x = col_num * x_spacing
                y = row_num * y_spacing
                positions[nid] = (x, y)

            # track nodes added
            added_nodes = set()

            # fungsi untuk ambil info node (baris pertama yang match)
            def get_node_info(nid):
                # cari di site kolom dulu, jika tidak ada cari di dest kolom
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

            # tambahkan semua node dulu (pasti)
            for nid in nodes_order:
                nid = str(nid).strip()
                if not nid or nid.lower() == "nan":
                    continue
                info = get_node_info(nid)
                fiber = info["Fiber Type"].strip() if info["Fiber Type"] else ""
                # jika degree 1 dan bukan P0_1 -> tandai P0
                if node_degree.get(nid, 0) == 1 and str(fiber).strip().lower() not in ["p0_1"]:
                    fiber = "P0"
                # pilih icon
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
                # tambahkan node
                net.add_node(nid,
                             label="\n".join(label_parts),
                             x=x, y=y,
                             physics=False,
                             size=50,
                             shape="image",
                             image=node_image,
                             color={"border": "007FFF" if f_low=="dark fiber" else ("21793A" if f_low in ["p0","p0_1"] else "A2A2C2"),
                                    "background": "white"},
                             title=title)
                added_nodes.add(nid)

            # ======================
            # Tambahkan edges — dibuat aman:
            # - pastikan site/dest di-strip
            # - jika node belum ada, tambahkan fallback minimal node
            # - tambahkan edge (bypass assert dengan menambahkan to net.edges)
            # ======================
            # Prepare edges list (so we can append)
            edges_to_add = []
            for _, r in ring_df.iterrows():
                s = str(r[col_site]).strip()
                t = str(r[col_dest]).strip()
                if s == "" or t == "":
                    continue
                flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                # ensure nodes present in net (and added_nodes)
                if s not in added_nodes:
                    net.add_node(s, label=s)
                    added_nodes.add(s)
                if t not in added_nodes:
                    net.add_node(t, label=t)
                    added_nodes.add(t)
                # append edge dict (use 'from'/'to' keys expected by vis)
                edge = {
                    "from": s,
                    "to": t,
                    "label": str(flp_len) if flp_len != "" else "",
                    "title": f"FLP LENGTH: {flp_len}",
                    "width": 3,
                    "color": "black",
                    "font": {"color": "red"},
                    "smooth": False
                }
                edges_to_add.append(edge)

            # Bypass add_edge assertion by appending to net.edges if present,
            # otherwise fallback to net.add_edge (nodes guaranteed to exist)
            if hasattr(net, "edges"):
                # net.edges is list of dicts in pyvis
                for e in edges_to_add:
                    try:
                        net.edges.append(e)
                    except Exception:
                        # fallback safe add_edge
                        net.add_edge(e["from"], e["to"], label=e.get("label",""), title=e.get("title",""),
                                     width=e.get("width",3), color=e.get("color","black"))
            else:
                for e in edges_to_add:
                    net.add_edge(e["from"], e["to"], label=e.get("label",""), title=e.get("title",""),
                                 width=e.get("width",3), color=e.get("color","black"))

            # Render HTML (tambahkan CSS grid)
            html_str = net.generate_html()
            html_str = html_str.replace(
                '<body>',
                '<body><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
            )
            components.html(html_str, height=850, scrolling=True)

elif menu_option == "Dashboard":
    st.markdown("<h2 style='color:white;'>📶 Dashboard Fiber Optic Active</h2>", unsafe_allow_html=True)
    st.markdown(f"**Jumlah Ring:** {df['Ring ID'].nunique()}")
    st.markdown(f"**Jumlah Site:** {df['New Site ID'].nunique()}")
    st.markdown(f"**Jumlah Destination:** {df['New Destenation'].nunique()}")
    st.dataframe(df.head(20))
