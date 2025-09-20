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
    return pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")

df = load_data()

# ======================
# Sidebar
# ======================
st.sidebar.header("⚙️ Menu")
menu_option = st.sidebar.radio("Pilih Tampilan:", ["Topology", "Dashboard"])
search_node = st.sidebar.text_input("🔍 Cari New Site ID / Destination:")

# ======================
# Main Area
# ======================
if menu_option == "Topology":
    st.markdown("<h2 style='color:white;'>🧬 Topology Fiber Optic Active</h2>", unsafe_allow_html=True)

    if search_node:
        df_filtered = df[
            df["New Site ID"].astype(str).str.contains(search_node, case=False, na=False) |
            df["New Destenation"].astype(str).str.contains(search_node, case=False, na=False)
        ]

        if not df_filtered.empty:
            ring_ids = df_filtered["Ring ID"].dropna().unique()

            for ring in ring_ids:
                st.subheader(f"🔗 Ring ID: {ring}")

                # FLP Vendor unik
                vendors = df[df["Ring ID"]==ring]["FLP Vendor"].dropna().unique()
                if len(vendors) > 0:
                    st.markdown(f"**FLP Vendor:** {', '.join(vendors)}")

                # Span ID unik
                if "Span ID" in df.columns:
                    spans = df[df["Ring ID"]==ring]["Span ID"].dropna().unique()
                    if len(spans) > 0:
                        st.markdown(f"**Span ID:** {', '.join(spans)}")

                ring_data = df[df["Ring ID"] == ring].dropna(subset=["New Site ID", "New Destenation"])
                net = Network(height="85vh", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)

                # ======================
                # Mapping info
                # ======================
                site_names_map = pd.Series(df["Site Name"].values, index=df["New Site ID"].astype(str)).to_dict() if "Site Name" in df.columns else {}
                site_hostname_map = pd.Series(df["Host Name"].values, index=df["New Site ID"].astype(str)).to_dict() if "Host Name" in df.columns else {}
                dest_names_map = pd.Series(df["Destination Name"].values, index=df["New Destenation"].astype(str)).to_dict() if "Destination Name" in df.columns else pd.Series(df["New Destenation"].values, index=df["New Destenation"].astype(str)).to_dict()
                dest_hostname_map = pd.Series(df["Destination Host Name"].values, index=df["New Destenation"].astype(str)).to_dict() if "Destination Host Name" in df.columns else {}

                all_nodes = set(ring_data["New Site ID"].astype(str)).union(set(ring_data["New Destenation"].astype(str)))
                node_labels = {}
                border_colors = {}

                # Hitung degree setiap node
                node_degree = {}
                for _, row in ring_data.iterrows():
                    site_id = str(row["New Site ID"])
                    dest_id = str(row["New Destenation"])
                    node_degree[site_id] = node_degree.get(site_id, 0) + 1
                    node_degree[dest_id] = node_degree.get(dest_id, 0) + 1

                for node_id in all_nodes:
                    if node_id in ring_data["New Site ID"].astype(str).values:
                        name = site_names_map.get(node_id, "")
                        hostname = site_hostname_map.get(node_id, "")
                        fiber_type = ring_data[ring_data["New Site ID"].astype(str)==node_id].iloc[0].get("Fiber Type","")
                        flp_vendor = ring_data[ring_data["New Site ID"].astype(str)==node_id].iloc[0].get("FLP Vendor","")
                    else:
                        name = dest_names_map.get(node_id, "")
                        hostname = dest_hostname_map.get(node_id, "")
                        fiber_type = ring_data[ring_data["New Destenation"].astype(str)==node_id].iloc[0].get("Fiber Type","")
                        flp_vendor = ring_data[ring_data["New Destenation"].astype(str)==node_id].iloc[0].get("FLP Vendor","")

                    fiber_type = str(fiber_type).strip()
                    flp_vendor = str(flp_vendor).strip()

                    # Ubah fiber type node ujung jadi P0 kecuali jika sudah P0_1
                    if node_degree.get(node_id, 0) == 1 and fiber_type.lower() not in ["p0_1"]:
                        fiber_type = "P0"

                    # Buat label dengan aman, abaikan NaN
                    label_parts = [fiber_type, str(node_id)]
                    if pd.notna(name) and str(name).strip() != "":
                        label_parts.append(str(name))
                    if pd.notna(hostname) and str(hostname).strip() != "":
                        label_parts.append(str(hostname))
                    if pd.notna(flp_vendor) and str(flp_vendor).strip() != "":
                        label_parts.append(str(flp_vendor))  # Tambahkan FLP Vendor
                    node_labels[node_id] = "\n".join(label_parts)

                    # Border color
                    if fiber_type.lower() == "dark fiber":
                        border_colors[node_id] = "007FFF"
                    elif fiber_type.lower() in ["p0", "p0_1"]:
                        border_colors[node_id] = "21793A"
                    elif fiber_type.lower() == "mmp":
                        border_colors[node_id] = "A2A2C2"
                    else:
                        border_colors[node_id] = "000000"

                # ======================
                # Posisi node grid
                # ======================
                max_per_row = 8
                x_spacing = 150
                y_spacing = 150

                for i, node_id in enumerate(all_nodes):
                    row_num = i // max_per_row
                    col_num = i % max_per_row
                    x = col_num * x_spacing
                    y = row_num * y_spacing

                    # Pilih icon berdasarkan fiber_type
                    fiber_type_lower = node_labels[node_id].split("\n")[0].lower()
                    if fiber_type_lower == "dark fiber":
                        node_image = "https://img.icons8.com/ios-filled/50/007FFF/router.png"
                    elif fiber_type_lower in ["p0", "p0_1"]:
                        node_image = "https://img.icons8.com/ios-filled/50/21793A/router.png"
                    else:
                        node_image = "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"

                    net.add_node(
                        node_id,
                        label=node_labels[node_id],
                        x=x,
                        y=y,
                        physics=False,
                        size=50,
                        shape="image",
                        image=node_image,
                        color={"border": border_colors[node_id], "background": "white"},
                        title=node_labels[node_id]
                    )

                # ======================
                # Tambahkan edge dengan FLP LENGTH merah
                # ======================
                for _, row in ring_data.iterrows():
                    site_id = str(row["New Site ID"])
                    dest_id = str(row["New Destenation"])
                    flp_length = row.get("FLP LENGTH", "")

                    if site_id and dest_id:
                        net.add_edge(
                            site_id,
                            dest_id,
                            label=str(flp_length) if pd.notna(flp_length) else "",
                            title=f"FLP LENGTH: {flp_length}",
                            font={"color": "red"},
                            width=3,
                            color="black",
                            arrows="",
                            smooth=False
                        )

                # ======================
                # Grid CSS langsung di background network
                # ======================
                html_str = net.generate_html()
                html_str = html_str.replace(
                    '<body>',
                    '<body><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
                )

                components.html(html_str, height=850, scrolling=True)

        else:
            st.warning("⚠️ Node tidak ditemukan di data.")

elif menu_option == "Dashboard":
    st.markdown("<h2 style='color:white;'>📶 Dashboard Fiber Optic Active</h2>", unsafe_allow_html=True)
    st.markdown(f"**Jumlah Ring:** {df['Ring ID'].nunique()}")
    st.markdown(f"**Jumlah Site:** {df['New Site ID'].nunique()}")
    st.markdown(f"**Jumlah Destination:** {df['New Destenation'].nunique()}")
    st.dataframe(df.head(20))


