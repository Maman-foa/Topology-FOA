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
file_path = '/home/user/foa-analys/src/Files/FOA ALL FLP AUGUST_2025.xlsb'
sheet_name = 'Query'

@st.cache_data
def load_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")

df = load_data(file_path, sheet_name)

# ======================
# Input kolom (langsung di halaman utama, bukan sidebar)
# ======================
st.markdown("## ⚙️ Konfigurasi Kolom")

col_syskey = st.text_input("Kolom Syskey", "SYSKEY")
col_flp = st.text_input("Kolom FLP Vendor", "FLP")
col_site = st.text_input("Kolom New Site ID", "NEW_SITE_ID")
col_site_name = st.text_input("Kolom New Site Name", "NEW_SITE_NAME")
col_dest = st.text_input("Kolom Destination Site ID", "DEST_SITE_ID")
col_dest_name = st.text_input("Kolom Destination Site Name", "DEST_SITE_NAME")
col_fiber = st.text_input("Kolom Fiber", "FIBER")
col_host = st.text_input("Kolom Hostname", "HOSTNAME")

# ======================
# Validasi input
# ======================
required_cols = [col_syskey, col_flp, col_site, col_dest]
if not all(c in df.columns for c in required_cols):
    st.error("❌ Kolom wajib tidak ditemukan di file Excel!")
else:
    # ======================
    # Filter ring (hapus yang dest kosong)
    # ======================
    ring_df = df.dropna(subset=[col_dest]).copy()

    if ring_df.empty:
        st.warning("⚠️ Tidak ada data ring ditemukan.")
    else:
        # ======================
        # Topology (kanvas fix 350px)
        # ======================
        net = Network(height="350px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
        net.toggle_physics(False)

        # Tambah node & edge
        for _, row in ring_df.iterrows():
            site_id = str(row[col_site])
            site_name = str(row[col_site_name]) if col_site_name in row else ""
            flp_vendor = str(row[col_flp]) if col_flp in row else ""
            host_name = str(row[col_host]) if col_host in row else ""

            dest_id = str(row[col_dest])
            dest_name = str(row[col_dest_name]) if col_dest_name in row else ""

            # Label node
            node_label = f"{site_id}\n{site_name}\n{flp_vendor}\n{host_name}".strip()
            dest_label = f"{dest_id}\n{dest_name}".strip()

            # Tambah node jika belum ada
            if site_id not in net.get_nodes():
                net.add_node(site_id, label=node_label, shape="dot", size=18, color="#4a90e2")
            if dest_id not in net.get_nodes():
                net.add_node(dest_id, label=dest_label, shape="dot", size=18, color="#50e3c2")

            # Tambah edge
            fiber_label = str(row[col_fiber]) if col_fiber in row else ""
            net.add_edge(site_id, dest_id, label=fiber_label, color="#888", width=2)

        # Export ke HTML
        html_str = net.generate_html()
        html_str = html_str.replace(
            '<body>',
            '<body><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), '
            'linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
        )

        st.markdown("## 🌐 Topology Ring")
        components.html(html_str, height=350, scrolling=True)

        # ======================
        # Tabel di bawah kanvas
        # ======================
        st.markdown("## 📋 Data Ring")
        table_cols = [c for c in [
            col_syskey, col_flp, col_site, col_site_name,
            col_dest, col_dest_name, col_fiber, col_host
        ] if c in ring_df.columns]

        st.dataframe(
            ring_df[table_cols].reset_index(drop=True),
            use_container_width=True,
            height=300
        )
