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
    menu_option = st.radio("Pilih Tampilan:", ["Topology", "FLP Vendor"])

if menu_option == "Topology":
    with col2:
        search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
    with col3:
        search_node = st.text_input(
            "🔍 Masukkan keyword:",
            key="search_keyword",
            placeholder="Ketik lalu tekan Enter",
            on_change=trigger_search
        )
else:  # FLP Vendor
    search_by = "FLP Vendor"
    with col2:
        st.markdown("**Cari berdasarkan:** FLP Vendor")
    with col3:
        search_node = st.text_input(
            "🏭 Masukkan nama vendor:",
            key="search_keyword",
            placeholder="Ketik nama vendor lalu tekan Enter",
            on_change=trigger_search
        )

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
# Judul Utama
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

elif menu_option == "FLP Vendor":
    st.markdown(
        """
        <h2 style="position:sticky; top:0; background-color:white; padding:8px;
                   z-index:999; border-bottom:1px solid #ddd; margin:0;">
            🏭 FLP Vendor Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )

# ======================
# Konten (untuk keduanya)
# ======================
if not st.session_state.do_search or search_node.strip() == "":
    st.info("ℹ️ Pilih kategori di atas, masukkan keyword, lalu tekan Enter untuk menampilkan data.")
else:
    file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
    sheet_name = 'Query'
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
    df.columns = df.columns.str.strip()

    # Kolom helper
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
    col_member_ring = get_col(df, "Member Ring")

    # Filter data sesuai pencarian
    if menu_option == "Topology":
        if search_by == "New Site ID":
            df_filtered = df[df[col_site].astype(str).str.contains(search_node, case=False, na=False)]
        elif search_by == "Ring ID":
            df_filtered = df[df[col_ring].astype(str).str.contains(search_node, case=False, na=False)]
        else:  # Host Name
            df_filtered = df[df[col_host].astype(str).str.contains(search_node, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Data tidak ditemukan.")
        else:
            ring_ids = df_filtered["Ring ID"].dropna().unique()
            for ring in ring_ids:
                st.subheader(f"🔗 Ring ID: {ring}")
                ring_df = df[df["Ring ID"] == ring].copy()

                # Bersihkan data
                ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip().replace({"nan": ""})

                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]

                net = Network(height="400px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
                net.toggle_physics(False)

                # Tambah nodes + edges
                added_nodes = set()
                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if not s or not t or s.lower() in ["nan","none"] or t.lower() in ["nan","none"]:
                        continue
                    for nid in [s, t]:
                        if nid not in added_nodes:
                            net.add_node(nid, label=nid, shape="dot", size=20)
                            added_nodes.add(nid)
                    flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                    net.add_edge(s, t, label=str(flp_len) if flp_len else "", color="red")

                html_str = net.generate_html()
                components.html(html_str, height=450, scrolling=False)

    else:  # ================= FLP VENDOR =================
        df_filtered = df[df[col_flp].astype(str).str.contains(search_node, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Data tidak ditemukan.")
        else:
            net = Network(height="800px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
            net.toggle_physics(True)

            added_nodes = set()
            for _, r in df_filtered.iterrows():
                s = str(r[col_site]).strip()
                t = str(r[col_dest]).strip()
                if not s or not t or s.lower() in ["nan","none"] or t.lower() in ["nan","none"]:
                    continue

                def get_node_info(nid):
                    df_match = df_filtered[df_filtered[col_site].astype(str).str.strip() == nid]
                    if df_match.empty:
                        df_match = df_filtered[df_filtered[col_dest].astype(str).str.strip() == nid]
                    if df_match.empty:
                        return {"Site Name":"", "Host Name":"", "FLP Vendor":""}
                    row0 = df_match.iloc[0]
                    return {
                        "Site Name": str(row0[col_site_name]) if col_site_name in row0 and pd.notna(row0[col_site_name]) else "",
                        "Host Name": str(row0[col_host]) if col_host in row0 and pd.notna(row0[col_host]) else "",
                        "FLP Vendor": str(row0[col_flp]) if col_flp in row0 and pd.notna(row0[col_flp]) else ""
                    }

                for nid in [s, t]:
                    if nid not in added_nodes:
                        info = get_node_info(nid)
                        label_parts = [nid]
                        if info["Site Name"]: label_parts.append(info["Site Name"])
                        if info["Host Name"]: label_parts.append(info["Host Name"])
                        if info["FLP Vendor"]: label_parts.append(info["FLP Vendor"])
                        net.add_node(
                            nid,
                            label="\n".join(label_parts),
                            shape="dot",
                            size=25,
                            color={"background": "#007FFF", "border": "#333"},
                            title="<br>".join(label_parts)
                        )
                        added_nodes.add(nid)

                flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                net.add_edge(s, t, label=str(flp_len) if flp_len else "", color="red")

            html_str = net.generate_html()
            # Inject search box
            search_js = """
            <input type="text" id="nodeSearch" placeholder="🔍 Cari Site ID..."
                   style="position:absolute; top:10px; left:50px; z-index:999; padding:5px;
                          border:1px solid #ccc; border-radius:4px;">
            <script type="text/javascript">
            var input = document.getElementById('nodeSearch');
            input.addEventListener("keyup", function(event) {
              if (event.key === "Enter") {
                var query = input.value.trim();
                if(query){
                    var nodeId = null;
                    var allNodes = nodes.get();
                    for (var i=0; i<allNodes.length; i++){
                        if (allNodes[i].label.includes(query)){
                            nodeId = allNodes[i].id;
                            break;
                        }
                    }
                    if(nodeId){
                        network.selectNodes([nodeId]);
                        network.focus(nodeId, {scale:1.5, animation:true});
                    } else {
                        alert("Site ID tidak ditemukan!");
                    }
                }
              }
            });
            </script>
            """
            html_str = html_str.replace("</body>", search_js + "</body>")
            components.html(html_str, height=800, scrolling=True)
