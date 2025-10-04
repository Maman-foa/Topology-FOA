import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import re

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide", page_title="Fiber Optic Analyzer", page_icon="🧬")

st.markdown("""
    <style>
    /* Layout grid dasar */
    .container {
        display: grid;
        grid-template-areas: 
            "header header"
            "sidebar content"
            "footer footer";
        grid-template-columns: 260px 1fr;
        grid-template-rows: auto 1fr auto;
        height: 100vh;
        gap: 10px;
    }
    .header {
        grid-area: header;
        background-color: #f1f3f4;
        text-align: center;
        padding: 14px;
        font-size: 24px;
        font-weight: bold;
        border-bottom: 2px solid #ddd;
        border-radius: 8px;
    }
    .sidebar {
        grid-area: sidebar;
        background-color: #fafafa;
        border-right: 2px solid #ddd;
        border-radius: 8px;
        padding: 12px;
    }
    .content {
        grid-area: content;
        padding: 10px;
        overflow-y: auto;
    }
    .footer {
        grid-area: footer;
        background-color: #f1f3f4;
        text-align: center;
        padding: 6px;
        border-top: 2px solid #ddd;
        font-size: 12px;
        color: gray;
        border-radius: 8px;
    }

    /* Streamlit cleanup */
    .block-container {padding-top: 0rem; padding-bottom: 0rem;}
    header [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    [data-testid="stStatusWidget"], [data-testid="stSidebarNav"] {visibility: hidden; height: 0;}
    </style>

    <div class="container">
        <div class="header">🧬 Topology Fiber Optic Active</div>
        <div class="sidebar" id="sidebar"></div>
        <div class="content" id="content"></div>
        <div class="footer">© 2025 Huawei Network Analyzer</div>
    </div>
""", unsafe_allow_html=True)


# ======================
# Fungsi Highlight
# ======================
def highlight_text(text, keywords):
    if not keywords:
        return text
    result = str(text)
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        result = pattern.sub(
            lambda m: f"<mark style='background-color:yellow;color:black;'>{m.group(0)}</mark>", 
            result
        )
    return result


# ======================
# Session state
# ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "do_search" not in st.session_state:
    st.session_state.do_search = False
if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""


# ======================
# Login
# ======================
def login():
    st.title("🔐 Login")
    password = st.text_input("Masukkan Password:", type="password")
    if st.button("Login"):
        if password == "Jakarta@24":
            st.session_state.authenticated = True
            st.success("Login berhasil! 🎉")
        else:
            st.error("Password salah.")

if not st.session_state.authenticated:
    login()
    st.stop()


# ======================
# Fungsi pencarian
# ======================
def trigger_search():
    st.session_state.do_search = True


# ======================
# Layout Utama
# ======================
col_sidebar, col_content = st.columns([1, 3], gap="medium")

with col_sidebar:
    st.markdown("### 🔧 Pengaturan Pencarian")
    menu_option = st.radio("Pilih Tampilan:", ["Topology"])
    search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
    search_input = st.text_input(
        "🔍 Masukkan keyword (pisahkan dengan koma):",
        key="search_keyword",
        placeholder="Contoh: 16SBY0267, 16SBY0497",
        on_change=trigger_search
    )
    search_nodes = [s.strip() for s in search_input.split(",") if s.strip()]

with col_content:
    st.markdown("## 🌐 Hasil Topology")
    canvas_height = 400

    if not st.session_state.do_search or not search_nodes:
        st.info("ℹ️ Masukkan keyword (pisahkan dengan koma), lalu tekan Enter untuk menampilkan topology.")
    else:
        with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
            file_path = 'SEPTEMBER_FOA - Update_2025.xlsb'
            sheet_name = 'Query CW39_2025'
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
            df.columns = df.columns.str.strip()

            def get_col(df, name, alt=None):
                if name in df.columns: return name
                if alt and alt in df.columns: return alt
                return None

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

            # filtering
            pattern = "|".join(map(re.escape, search_nodes))
            if search_by == "New Site ID":
                df_filtered = df[df[col_site].astype(str).str.contains(pattern, case=False, na=False)]
            elif search_by == "Ring ID":
                df_filtered = df[df[col_ring].astype(str).str.contains(pattern, case=False, na=False)]
            else:
                df_filtered = df[df[col_host].astype(str).str.contains(pattern, case=False, na=False)]

            if df_filtered.empty:
                st.warning("⚠️ Node tidak ditemukan di data.")
            else:
                ring_ids = df_filtered["Ring ID"].dropna().unique()
                for ring in ring_ids:
                    st.markdown(f"### 🔗 Ring ID: {highlight_text(ring, search_nodes)}", unsafe_allow_html=True)

                    ring_df = df[df["Ring ID"] == ring].copy()

                    # tampilkan member ring
                    if col_member_ring and not ring_df.empty:
                        non_na_members = ring_df[col_member_ring].dropna()
                        members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                        st.markdown(
                            f'<p style="font-size:14px; color:gray;">💡 Member Ring: {highlight_text(members_str, search_nodes)}</p>',
                            unsafe_allow_html=True
                        )

                    # setup pyvis
                    net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", directed=False)
                    net.toggle_physics(False)

                    nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                    node_degree = {}
                    for _, r in ring_df.iterrows():
                        s, t = str(r[col_site]).strip(), str(r[col_dest]).strip()
                        if s: node_degree[s] = node_degree.get(s, 0) + 1
                        if t: node_degree[t] = node_degree.get(t, 0) + 1

                    added_nodes = set()

                    def get_node_info(nid):
                        df_match = ring_df[ring_df[col_site].astype(str).str.strip() == nid]
                        if df_match.empty:
                            df_match = ring_df[ring_df[col_dest].astype(str).str.strip() == nid]
                        if df_match.empty:
                            return {"Fiber Type": "", "Site Name": "", "Host Name": "", "FLP Vendor": ""}
                        row0 = df_match.iloc[0]
                        return {
                            "Fiber Type": str(row0[col_fiber]) if pd.notna(row0.get(col_fiber)) else "",
                            "Site Name": str(row0[col_site_name]) if pd.notna(row0.get(col_site_name)) else "",
                            "Host Name": str(row0[col_host]) if pd.notna(row0.get(col_host)) else "",
                            "FLP Vendor": str(row0[col_flp]) if pd.notna(row0.get(col_flp)) else ""
                        }

                    for nid in nodes_order:
                        info = get_node_info(nid)
                        fiber = info["Fiber Type"].strip() if info["Fiber Type"] else ""
                        f_low = fiber.lower()
                        node_image = (
                            "https://img.icons8.com/ios-filled/50/007FFF/router.png" if f_low=="dark fiber" else
                            "https://img.icons8.com/ios-filled/50/21793A/router.png" if f_low in ["p0","p0_1"] else
                            "https://img.icons8.com/ios-filled/50/A2A2C2/router.png"
                        )
                        title = "<br>".join(filter(None, [fiber, nid, info["Site Name"], info["Host Name"], info["FLP Vendor"]]))
                        is_match = any(re.search(re.escape(kw), nid, re.IGNORECASE) for kw in search_nodes)
                        net.add_node(
                            nid,
                            label=nid,
                            shape="image",
                            image=node_image,
                            size=45,
                            font={"color": "red" if is_match else "black"},
                            title=title
                        )
                        added_nodes.add(nid)

                    for _, r in ring_df.iterrows():
                        s, t = str(r[col_site]).strip(), str(r[col_dest]).strip()
                        flp_len = r[col_flp_len] if pd.notna(r.get(col_flp_len)) else ""
                        if s and t and s not in ["nan","none"] and t not in ["nan","none"]:
                            net.add_edge(s, t, label=str(flp_len), title=f"FLP LENGTH: {flp_len}", width=3, color="red")

                    html_str = net.generate_html()
                    html_str = html_str.replace(
                        '<body>',
                        '<body><div class="canvas-border"><style>.vis-network{background-image: linear-gradient(to right, #d0d0d0 1px, transparent 1px), linear-gradient(to bottom, #d0d0d0 1px, transparent 1px); background-size: 50px 50px;}</style>'
                    )
                    components.html(html_str, height=canvas_height, scrolling=False)

                    # tabel member ring
                    st.markdown("#### 📋 Member Ring")
                    table_cols = [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host]
                    display_df = ring_df[table_cols].fillna("").reset_index(drop=True).astype(str)
                    for col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: highlight_text(x, search_nodes))
                    st.markdown(display_df.to_html(escape=False), unsafe_allow_html=True)
