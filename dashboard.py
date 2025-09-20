import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridOptionsBuilder

# ======================
# Bersihkan cache lama
# ======================
st.cache_data.clear()

# ======================
# Konfigurasi file
# ======================
file_path = 'FOA ALITA AUGUST_2025.xlsb'
sheet_name = 'FOA Active'

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
    # ======================
    # Header Topology freeze & center
    # ======================
    st.markdown("""
        <div style="position: fixed; top: 40px; left: 0; right: 0;
                    background-color: #0e1117; padding: 12px;
                    border-bottom: 2px solid #444; z-index: 9999;
                    text-align: center;">
            <h2 style="color:white; margin:0;">🧬 Topology Fiber Optic Active</h2>
        </div>
        <div style="margin-top:120px;"></div>
    """, unsafe_allow_html=True)

    if search_node:
        df_filtered = df[
            df["New Site ID"].astype(str).str.contains(search_node, case=False, na=False) |
            df["New Destenation"].astype(str).str.contains(search_node, case=False, na=False)
        ]

        if not df_filtered.empty:
            ring_ids = df_filtered["Ring ID"].dropna().unique()
            for ring in ring_ids:
                st.subheader(f"🔗 Ring ID: {ring}")
                vendors = df[df["Ring ID"]==ring]["FLP Vendor"].dropna().unique()
                if len(vendors) > 0:
                    st.markdown(f"**FLP Vendor:** {', '.join(vendors)}")
                if "Span ID" in df.columns:
                    spans = df[df["Ring ID"]==ring]["Span ID"].dropna().unique()
                    if len(spans) > 0:
                        st.markdown(f"**Span ID:** {', '.join(spans)}")

                # ... Network visualization code tetap sama ...

        else:
            st.warning("⚠️ Node tidak ditemukan di data.")

elif menu_option == "Dashboard":
    # ======================
    # Header Dashboard freeze & center
    # ======================
    st.markdown("""
        <div style="position: fixed; top: 40px; left: 0; right: 0;
                    background-color: #0e1117; padding: 12px;
                    border-bottom: 2px solid #444; z-index: 9999;
                    text-align: center;">
            <h2 style="color:white; margin:0;">📶 Dashboard Fiber Optic Active</h2>
        </div>
        <div style="margin-top:120px;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Jumlah Ring:** {df['Ring ID'].nunique()}")
    st.markdown(f"**Jumlah Site:** {df['New Site ID'].nunique()}")
    st.markdown(f"**Jumlah Destination:** {df['New Destenation'].nunique()}")

    # ======================
    # Tampilkan tabel mirip Excel
    # ======================
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, groupable=True, filter=True, sortable=True, resizable=True)
    gb.configure_grid_options(domLayout='normal')  # agar bisa scroll, header tetap
    gridOptions = gb.build()

    AgGrid(
        df,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=600,
        reload_data=True
    )
