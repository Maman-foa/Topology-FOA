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

# Kolom penting
col_site = "New Site ID"
col_dest = "Destination"
col_site_name = "New Site Name"
col_host = "Hostname"
col_fiber = "Fiber Type"
col_flp = "FLP Vendor"
col_flp_len = "FLP Length"

# ======================
# Sidebar menu
# ======================
menu_option = st.sidebar.selectbox("Pilih Menu", ["Topology", "FLP Vendor"])

# ======================
# Fungsi buat Topology
# ======================
def draw_topology(data, height=900):
    net = Network(height=f"{height}px", width="100%", bgcolor="#f8f8f8",
                  font_color="black", directed=False)
    net.toggle_physics(False)

    nodes_order = list(pd.unique(pd.concat([data[col_site], data[col_dest]], ignore_index=True)))
    nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]

    max_per_row = 8
    x_spacing = 200
    y_spacing = 200
    positions = {}
    for i, nid in enumerate(nodes_order):
        row = i // max_per_row
        col_in_row = i % max_per_row
        col = max_per_row - 1 - col_in_row if row % 2 == 1 else col_in_row
        x = col * x_spacing
        y = row * y_spacing
        positions[nid] = (x, y)

    added_nodes = set()
    for _, r in data.iterrows():
        s = str(r[col_site]).strip() if col_site and pd.notna(r[col_site]) else ""
        t = str(r[col_dest]).strip() if col_dest and pd.notna(r[col_dest]) else ""

        for nid in [s, t]:
            if not nid or nid in added_nodes:
                continue

            df_match = data[
                (data[col_site].astype(str).str.strip() == nid) |
                (data[col_dest].astype(str).str.strip() == nid)
            ]
            row0 = df_match.iloc[0] if not df_match.empty else {}
            fiber = str(row0.get(col_fiber, "")).strip().lower() if col_fiber else ""
            site_name = str(row0.get(col_site_name, "")) if col_site_name else ""
            host_name = str(row0.get(col_host, "")) if col_host else ""
            flp_vendor = str(row0.get(col_flp, "")) if col_flp else ""

            degree = (data[col_site].astype(str).str.strip().tolist() +
                      data[col_dest].astype(str).str.strip().tolist()).count(nid)
            if degree == 1 and fiber not in ["p0", "p0_1"]:
                fiber = "p0"

            if fiber == "dark fiber":
                node_image = "https://img.icons8.com/ios-filled/50/007FFF/router.png"
                border_color = "007FFF"
            elif fiber in ["p0", "p0_1"]:
                node_image = "https://img.icons8.com/ios-filled/50/21793A/router.png"
                border_color = "21793A"
            else:
                node_image = "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"
                border_color = "A2A2C2"

            label_parts = [fiber.upper() if fiber else "", nid, site_name, host_name, flp_vendor]
            label = "\n".join([p for p in label_parts if p])
            title = "<br>".join([p for p in label_parts if p])

            x, y = positions.get(nid, (0, 0))
            net.add_node(
                nid,
                label=label,
                x=x, y=y,
                physics=False,
                size=50,
                shape="image",
                image=node_image,
                color={"border": border_color, "background": "white"},
                title=title
            )
            added_nodes.add(nid)

        if s and t:
            flp_len_val = r[col_flp_len] if col_flp_len and col_flp_len in r and pd.notna(r[col_flp_len]) else ""
            net.add_edge(s, t, label=str(flp_len_val) if flp_len_val else "", color="red", width=2)

    html_str = net.generate_html()
    search_js = """
    <input type="text" id="nodeSearch" placeholder="🔍 Cari Site ID..." 
           style="position:absolute; top:10px; left:50px; z-index:999; padding:6px; border:1px solid #ccc; border-radius:4px;">
    <script type="text/javascript">
    var input = document.getElementById('nodeSearch');
    input.addEventListener("keyup", function(event) {
      if (event.key === "Enter") {
        var query = input.value.trim();
        if(query){
            var nodeId = null;
            var allNodes = nodes.get();
            for (var i=0; i<allNodes.length; i++){
                var lab = allNodes[i].label || "";
                if (lab.toLowerCase().includes(query.toLowerCase())){
                    nodeId = allNodes[i].id;
                    break;
                }
            }
            if(nodeId !== null){
                network.selectNodes([nodeId]);
                network.focus(nodeId, {scale:1.6, animation:{duration:400}});
            } else {
                alert("Site ID tidak ditemukan di canvas.");
            }
        }
      }
    });
    </script>
    """
    html_str = html_str.replace("</body>", search_js + "</body>")
    components.html(html_str, height=height, scrolling=True)

# ======================
# Menu Topology
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
    draw_topology(df)

# ======================
# Menu FLP Vendor
# ======================
elif menu_option == "FLP Vendor":
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px;
                   z-index:999; border-bottom:1px solid #ddd; margin:0;">
            🏢 Topology by FLP Vendor
        </h2>
        """,
        unsafe_allow_html=True
    )

    vendor_list = sorted([v for v in df[col_flp].dropna().unique() if str(v).strip()])
    vendor_choice = st.selectbox("Pilih Vendor", ["-- Pilih Vendor --"] + vendor_list)

    if vendor_choice == "-- Pilih Vendor --":
        st.info("👆 Silakan pilih vendor untuk menampilkan topology.")
    else:
        df_filtered = df[df[col_flp].astype(str).str.strip() == vendor_choice]
        if df_filtered.empty:
            st.warning("⚠️ Data untuk vendor ini tidak ditemukan.")
        else:
            draw_topology(df_filtered)
