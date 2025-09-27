import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import re
import os

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide")

# === Header dengan logo & judul sejajar tengah ===
st.markdown(
    """
    <div style="
        position:sticky; 
        top:0;  
        background-color:white; 
        padding:12px;
        z-index:999; 
        border-bottom:1px solid #ddd; 
        margin:0;
        display:flex;
        align-items:center;
        justify-content:center;
        gap:12px;
    ">
        <img src="https://www.google.com/imgres?q=logo%20huawei%20terbaru&imgurl=https%3A%2F%2Fimages.seeklogo.com%2Flogo-png%2F6%2F1%2Fhuawei-logo-png_seeklogo-68529.png&imgrefurl=https%3A%2F%2Fseeklogo.com%2Fvector-logo%2F68529%2Fhuawei&docid=kHndFtsfvSsqWM&tbnid=alXFxK5NdQp11M&vet=12ahUKEwif-8bHxPmPAxXLxjgGHZpREz8QM3oECBgQAA..i&w=600&h=600&hcb=2&ved=2ahUKEwif-8bHxPmPAxXLxjgGHZpREz8QM3oECBgQAA" 
             alt="Huawei Logo" height="40">
        <h2 style="margin:0;">🧬 Topology Fiber Optic Active</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# ======================
# Load data
# ======================
file_path = "Fiber Optic Active.xlsx"   # <-- pastikan nama & lokasi file sesuai
if not os.path.exists(file_path):
    st.error(f"❌ File tidak ditemukan: {file_path}")
    st.stop()

df = pd.read_excel(file_path)

# ======================
# Input pencarian
# ======================
search_input = st.text_input("🔍 Cari Node ID (pisahkan dengan koma)", "")
keywords = [s.strip() for s in search_input.split(",") if s.strip()]

if keywords:
    # Cari semua Ring ID yang match dengan keyword
    df_filtered = df[
        df["New Site ID"].astype(str).str.contains("|".join(keywords), flags=re.IGNORECASE, na=False) |
        df["New Destenation"].astype(str).str.contains("|".join(keywords), flags=re.IGNORECASE, na=False)
    ]

    ring_ids = df_filtered["Ring ID"].dropna().unique()

    if len(ring_ids) == 0:
        st.warning("⚠️ Tidak ditemukan Ring ID yang sesuai dengan keyword.")
    else:
        # Gabungkan semua ring yang ditemukan
        ring_df_all = df[df["Ring ID"].isin(ring_ids)].copy()

        # ======================
        # Build PyVis network
        # ======================
        net = Network(height="600px", width="100%", bgcolor="white", font_color="black", notebook=False)
        net.barnes_hut()

        # Tambahkan node & edge
        for _, row in ring_df_all.iterrows():
            src = str(row["New Site ID"])
            dst = str(row["New Destenation"])
            link = str(row["Fiber Type"]) if "Fiber Type" in row else "Unknown"

            # Tentukan warna node
            for node in [src, dst]:
                if node not in net.get_nodes():
                    color = "red" if node in keywords else "lightblue"
                    net.add_node(node, label=node, color=color)

            # Tambahkan edge
            net.add_edge(src, dst, label=link)

        # Simpan dan tampilkan network
        net.save_graph("network.html")
        with open("network.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=650)

        # ======================
        # Tampilkan Ring Info
        # ======================
        st.subheader("📋 Ring Information")
        st.info(", ".join(ring_ids))  # Ring ID dipisah koma

        # ======================
        # Tabel gabungan
        # ======================
        st.subheader("📊 Data Gabungan")
        st.dataframe(ring_df_all)

else:
    st.info("⬆️ Masukkan Node ID di atas untuk melihat topology.")
