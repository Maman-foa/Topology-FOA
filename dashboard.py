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
file_path = "FOA NEW ALL FLP AUGUST_2025.xlsb"  # path relatif di repo
sheet_name = "Query"

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
    st.markdown("""
        <div style="position: fixed; top: 40px; left: 0; right: 0;
                    background-color: #0e1117; padding: 12px;
                    border-bottom: 2px solid #444; z-index: 9999;
                    text-align: center;">
            <h2 style="color:white; margin:0;">🧬 Topology Fiber Optic Active</h2>
        </div>
        <div style="margin-top:120px;"></div>
    """, unsafe_allow_html=True)

    # Filter berdasarkan search_node
    if search_node:
        df_filtered = df[
            df["New Site ID"].astype(str).str.contains(search_node, case=False, na=False) |
            df["New Destenation"].astype(str).str.contains(search_node, case=False, na=False)
        ]
    else:
        df_filtered = df

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

            # ======================
            # Network visualization per ring
            # ======================
            net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="white", directed=True)
            net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=150, spring_strength=0.001, damping=0.09)

            # Buat dictionary node dan informasi
            edges_ring = df[df["Ring ID"]==ring][["New Site ID","New Destenation","Fiber Type","Site Name","Hostname","FLP Vendor"]].dropna()
            node_info = {}
            for _, row in edges_ring.iterrows():
                for col in ["New Site ID","New Destenation"]:
                    node_info[col] = {
                        "Fiber Type": row["Fiber Type"],
                        "Site Name": row["Site Name"],
                        "Hostname": row["Hostname"],
                        "FLP Vendor": row["FLP Vendor"]
                    }

            # Tambahkan node dengan icon dan tooltip
            for node_id, info in node_info.items():
                fiber_type_lower = str(info["Fiber Type"]).lower()
                if fiber_type_lower == "dark fiber":
                    node_image = "https://img.icons8.com/ios-filled/50/007FFF/router.png"
                elif fiber_type_lower == "p0":
                    node_image = "https://img.icons8.com/ios-filled/50/007FFF/router.png"
                elif fiber_type_lower == "p0_1":
                    node_image = "https://img.icons8.com/ios-filled/50/21793A/router.png"
                else:
                    node_image = "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"

                title_text = f"""
                Fiber Type: {info['Fiber Type']}<br>
                Site Name: {info['Site Name']}<br>
                Hostname: {info['Hostname']}<br>
                FLP Vendor: {info['FLP Vendor']}
                """
                net.add_node(node_id, label=node_id, shape='image', image=node_image, physics=False, title=title_text)

            # Tambahkan edge
            for _, row in edges_ring.iterrows():
                net.add_edge(row["New Site ID"], row["New Destenation"])

            # Tampilkan network di Streamlit
            path = f"network_{ring}.html"
            net.save_graph(path)
            HtmlFile = open(path, 'r', encoding='utf-8')
            components.html(HtmlFile.read(), height=600)
    else:
        st.warning("⚠️ Node tidak ditemukan di data.")

# ======================
# Dashboard view
# ======================
elif menu_option == "Dashboard":
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

    # Tabel interaktif
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, groupable=True, filter=True, sortable=True, resizable=True)
    gb.configure_grid_options(domLayout='normal')
    gridOptions = gb.build()

    AgGrid(
        df,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=600,
        reload_data=True
    )
