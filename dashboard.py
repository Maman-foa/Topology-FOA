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
    return pd.read_excel(file_path, sheet_name=sheet_name)

df = load_data()

# ======================
# Judul freeze
# ======================
st.markdown(
    """
    <h2 style="position:sticky; top:0; background-color:white; padding:8px;
               z-index:999; border-bottom:1px solid #ddd; margin:0;">
        🧬 Topology Fiber Optic Active
    </h2>
    """,
    unsafe_allow_html=True
)

# ======================
# Buat grafik topology
# ======================
net = Network(height="850px", width="100%", bgcolor="#ffffff", font_color="black")
net.force_atlas_2based()

# Tambahkan node & edge
for _, row in df.iterrows():
    src = row["Hostname"]
    dst = row["Destination"]

    # Nama node dengan vendor di bawah hostname
    vendor = str(row.get("FLP Vendor", "Unknown"))
    src_label = f"{src}\n({vendor})"
    dst_label = f"{dst}\n({vendor})" if pd.notna(dst) else None

    net.add_node(src, label=src_label, shape="dot", size=15, color="#3182bd")
    if dst_label:
        net.add_node(dst, label=dst_label, shape="dot", size=15, color="#31a354")
        net.add_edge(src, dst)

# Simpan hasil ke HTML
net.save_graph("topology.html")

# ======================
# Render di Streamlit
# ======================
with open("topology.html", "r", encoding="utf-8") as f:
    html_code = f.read()

components.html(html_code, height=850, width=1600, scrolling=True)
