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
# Helpers & load data
# ======================
@st.cache_data
def load_data(file_path='FOA NEW ALL FLP AUGUST_2025.xlsb', sheet_name='Query'):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
    except Exception:
        # fallback (in case engine not available) — user environment harus sesuaikan
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()
    return df

def get_col(df, name, alt=None):
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

# load data early to populate vendor list for dropdown
file_path = 'FOA NEW ALL FLP AUGUST_2025.xlsb'
sheet_name = 'Query'
df = load_data(file_path=file_path, sheet_name=sheet_name)

# ======================
# Session state
# ======================
if 'do_search' not in st.session_state:
    st.session_state.do_search = False

def trigger_search():
    st.session_state.do_search = True

# ======================
# Sidebar/Menu area (top row)
# ======================
col1, col2, col3 = st.columns([1,2,2])
with col1:
    menu_option = st.radio("Pilih Tampilan:", ["Topology", "FLP Vendor"])

# --- Topology inputs ---
if menu_option == "Topology":
    with col2:
        search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"], key="search_by_topo")
    with col3:
        search_node_topo = st.text_input(
            "🔍 Masukkan keyword:",
            key="search_keyword_topo",
            placeholder="Ketik lalu tekan Enter",
            on_change=trigger_search
        )

# --- FLP Vendor inputs (dropdown) ---
else:
    # determine FLP column name
    col_flp_name = get_col(df, "FLP Vendor")
    if not col_flp_name:
        st.error("Kolom 'FLP Vendor' tidak ditemukan di file Excel.")
        st.stop()

    vendors = sorted(df[col_flp_name].dropna().astype(str).unique().tolist())
    vendor_options = ["-- Semua Vendor --"] + vendors
    with col2:
        st.markdown("**Cari berdasarkan:** FLP Vendor")
    with col3:
        vendor_choice = st.selectbox(
            "🏭 Pilih Vendor (atau pilih Semua):",
            options=vendor_options,
            index=0,
            key="vendor_select",
            on_change=trigger_search
        )

# ======================
# Judul (freeze)
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
else:
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
# Main content
# ======================
if not st.session_state.do_search:
    st.info("ℹ️ Pilih tampilan di kiri, lakukan pilihan/ketik, lalu tekan Enter atau pilih vendor untuk melihat hasil.")
else:
    # common helper columns
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

    # ----------------------
    # TOPOLOGY (as semula: per-ring, sub-canvas + member table)
    # ----------------------
    if menu_option == "Topology":
        # validate required columns for chosen search_by
        if search_by == "New Site ID" and not col_site:
            st.error("Kolom 'New Site ID' tidak ditemukan di Excel.")
        elif search_by == "Ring ID" and not col_ring:
            st.error("Kolom 'Ring ID' tidak ditemukan di Excel.")
        elif search_by == "Host Name" and not col_host:
            st.error("Kolom 'Host Name' tidak ditemukan di Excel.")
        else:
            # apply filter
            if search_by == "New Site ID":
                df_filtered = df[df[col_site].astype(str).str.contains(search_node_topo, case=False, na=False)]
            elif search_by == "Ring ID":
                df_filtered = df[df[col_ring].astype(str).str.contains(search_node_topo, case=False, na=False)]
            else:  # Host Name
                df_filtered = df[df[col_host].astype(str).str.contains(search_node_topo, case=False, na=False)]

            if df_filtered.empty:
                st.warning("⚠️ Node tidak ditemukan di data.")
            else:
                # iterate per ring (like original)
                ring_ids = df_filtered[col_ring].dropna().unique()
                canvas_height = 350
                for ring in ring_ids:
                    st.subheader(f"🔗 Ring ID: {ring}")
                    ring_df = df[df[col_ring] == ring].copy()

                    # Member Ring (below subtitle)
                    if col_member_ring and not ring_df.empty:
                        non_na_members = ring_df[col_member_ring].dropna()
                        members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                        st.markdown(
                            f'<p style="font-size:14px; color:gray; margin-top:-10px;">💡 Member Ring: {members_str}</p>',
                            unsafe_allow_html=True
                        )

                    # clean site/dest
                    if col_site:
                        ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                    if col_dest:
                        ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip().replace({"nan": ""})

                    # build node order (zig-zag)
                    nodes_order = []
                    if col_site and col_dest:
                        nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                        nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]
                        valid_dest_nodes = set(ring_df[col_dest].dropna().astype(str).str.strip().unique())
                        valid_site_nodes = set(ring_df[col_site].dropna().astype(str).str.strip().unique())
                        nodes_order = [n for n in nodes_order if n in valid_dest_nodes or n in valid_site_nodes]

                    net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
                    net.toggle_physics(False)

                    # compute degrees
                    node_degree = {}
                    if col_site and col_dest:
                        for _, r in ring_df.iterrows():
                            s = str(r[col_site]).strip()
                            t = str(r[col_dest]).strip()
                            if s:
                                node_degree[s] = node_degree.get(s, 0) + 1
                            if t:
                                node_degree[t] = node_degree.get(t, 0) + 1

                    # positions zig-zag
                    max_per_row = 8
                    x_spacing = 200
                    y_spacing = 200
                    positions = {}
                    for i, nid in enumerate(nodes_order):
                        row = i // max_per_row
                        col_in_row = i % max_per_row
                        if row % 2 == 1:
                            col = max_per_row - 1 - col_in_row
                        else:
                            col = col_in_row
                        x = col * x_spacing
                        y = row * y_spacing
                        positions[nid] = (x, y)

                    added_nodes = set()

                    def get_node_info(nid):
                        # search both as site and as dest
                        df_match = ring_df[ring_df[col_site].astype(str).str.strip() == nid] if col_site else pd.DataFrame()
                        if df_match.empty and col_dest:
                            df_match = ring_df[ring_df[col_dest].astype(str).str.strip() == nid]
                        if df_match.empty:
                            return {"Fiber Type": "", "Site Name": "", "Host Name": "", "FLP Vendor": ""}
                        row0 = df_match.iloc[0]
                        return {
                            "Fiber Type": str(row0[col_fiber]) if col_fiber and col_fiber in row0 and pd.notna(row0[col_fiber]) else "",
                            "Site Name": str(row0[col_site_name]) if col_site_name and col_site_name in row0 and pd.notna(row0[col_site_name]) else "",
                            "Host Name": str(row0[col_host]) if col_host and col_host in row0 and pd.notna(row0[col_host]) else "",
                            "FLP Vendor": str(row0[col_flp]) if col_flp and col_flp in row0 and pd.notna(row0[col_flp]) else ""
                        }

                    # add nodes
                    for nid in nodes_order:
                        info = get_node_info(nid)
                        fiber = info["Fiber Type"].strip() if info["Fiber Type"] else ""
                        if node_degree.get(nid, 0) == 1 and fiber.lower() not in ["p0_1"]:
                            fiber = "P0"
                        f_low = fiber.lower()
                        node_image = (
                            "https://img.icons8.com/ios-filled/50/007FFF/router.png" if f_low == "dark fiber" else
                            "https://img.icons8.com/ios-filled/50/21793A/router.png" if f_low in ["p0", "p0_1"] else
                            "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"
                        )

                        label_parts = [fiber, nid]
                        if info["Site Name"]:
                            label_parts.append(info["Site Name"])
                        if info["Host Name"]:
                            label_parts.append(info["Host Name"])
                        if info["FLP Vendor"]:
                            label_parts.append(info["FLP Vendor"])
                        title = "<br>".join([p for p in label_parts if p])

                        x, y = positions.get(nid, (0, 0))
                        net.add_node(
                            nid,
                            label="\n".join([p for p in label_parts if p]),
                            x=x, y=y,
                            physics=False,
                            size=50,
                            shape="image",
                            image=node_image,
                            color={"border": "007FFF" if f_low == "dark fiber" else ("21793A" if f_low in ["p0", "p0_1"] else "A2A2C2"), "background": "white"},
                            title=title
                        )
                        added_nodes.add(nid)

                    # add edges
                    if col_site and col_dest:
                        for _, r in ring_df.iterrows():
                            s = str(r[col_site]).strip()
                            t = str(r[col_dest]).strip()
                            if s and t and s.lower() not in ["nan", "none"] and t.lower() not in ["nan", "none"]:
                                flp_len = r[col_flp_len] if col_flp_len and col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                                if s not in added_nodes:
                                    net.add_node(s, label=s)
                                    added_nodes.add(s)
                                if t not in added_nodes:
                                    net.add_node(t, label=t)
                                    added_nodes.add(t)
                                net.add_edge(
                                    s,
                                    t,
                                    label=str(flp_len) if flp_len else "",
                                    title=f"FLP LENGTH: {flp_len}",
                                    width=3,
                                    color="red",
                                    smooth=False
                                )

                    html_str = net.generate_html()
                    html_str = html_str.replace(
                        '<body>',
                        '<body><div class="canvas-border"><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
                    )
                    components.html(html_str, height=canvas_height, scrolling=False)

                    # Member Ring table under the canvas
                    table_cols = [c for c in [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host] if c]
                    st.markdown("### 📋 Member Ring")
                    display_df = ring_df[table_cols].fillna("").reset_index(drop=True)
                    st.dataframe(display_df, use_container_width=True, height=300)

    # ----------------------
    # FLP VENDOR (single big canvas, grouped by Ring, no table, search inside canvas)
    # ----------------------
    else:
        # vendor_choice from selectbox above; if "-- Semua Vendor --" selected show all
        if 'vendor_choice' not in locals():
            # fallback (shouldn't happen since selectbox defined earlier)
            vendor_choice = "-- Semua Vendor --"

        if vendor_choice == "-- Semua Vendor --":
            df_filtered = df[df[col_flp].astype(str).str.strip() != ""]
        else:
            df_filtered = df[df[col_flp].astype(str).str.strip() == vendor_choice]

        if df_filtered.empty:
            st.warning("⚠️ Data untuk vendor ini tidak ditemukan.")
        else:
            canvas_height = 900
            net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
            net.toggle_physics(True)
            added_nodes = set()

            for _, r in df_filtered.iterrows():
                s = str(r[col_site]).strip() if col_site and pd.notna(r[col_site]) else ""
                t = str(r[col_dest]).strip() if col_dest and pd.notna(r[col_dest]) else ""
                ring = str(r[col_ring]).strip() if col_ring and pd.notna(r[col_ring]) else "Unknown"
                vendor = str(r[col_flp]).strip() if col_flp and pd.notna(r[col_flp]) else ""
                host = str(r[col_host]).strip() if col_host and pd.notna(r[col_host]) else ""
                site_name = str(r[col_site_name]).strip() if col_site_name and pd.notna(r[col_site_name]) else ""

                if not s and not t:
                    continue

                # helper to get node label & title (use first matching row in df_filtered)
                def node_label_and_title(nid):
                    df_match = df_filtered[df_filtered[col_site].astype(str).str.strip() == nid] if col_site else pd.DataFrame()
                    if df_match.empty and col_dest:
                        df_match = df_filtered[df_filtered[col_dest].astype(str).str.strip() == nid]
                    if df_match.empty:
                        return nid, nid
                    row0 = df_match.iloc[0]
                    label_parts = [nid]
                    if col_site_name and col_site_name in row0 and pd.notna(row0[col_site_name]):
                        label_parts.append(str(row0[col_site_name]))
                    if col_host and col_host in row0 and pd.notna(row0[col_host]):
                        label_parts.append(str(row0[col_host]))
                    if col_flp and col_flp in row0 and pd.notna(row0[col_flp]):
                        label_parts.append(str(row0[col_flp]))
                    label = "\n".join(label_parts)
                    title = "<br>".join(label_parts)
                    return label, title

                for nid in [s, t]:
                    if not nid:
                        continue
                    if nid not in added_nodes:
                        label, title = node_label_and_title(nid)
                        net.add_node(
                            nid,
                            label=label,
                            size=30,
                            group=ring,        # group by Ring ID so pyvis gives same color per ring
                            title=title
                        )
                        added_nodes.add(nid)

                if s and t:
                    flp_len_val = r[col_flp_len] if col_flp_len and col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                    net.add_edge(s, t, label=str(flp_len_val) if flp_len_val else "", color="red", width=2)

            # generate html and inject search box (search by Site ID inside canvas)
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
                    try {
                        var allNodes = nodes.get(); // nodes DataSet
                        for (var i=0; i<allNodes.length; i++){
                            var lab = allNodes[i].label || "";
                            if (lab.toString().toLowerCase().includes(query.toLowerCase())){
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
                    } catch(err){
                        alert("Terjadi error saat mencari node: " + err);
                    }
                }
              }
            });
            </script>
            """
            html_str = html_str.replace("</body>", search_js + "</body>")
            components.html(html_str, height=canvas_height, scrolling=True)
