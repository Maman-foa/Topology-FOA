import streamlit as st
import pandas as pd
import socket
import os
from datetime import datetime
from pyvis.network import Network
import streamlit.components.v1 as components
import re

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide", page_title="Fiber Optic Analyzer", page_icon="🧬")
st.markdown("""
<style>
.block-container { padding-top: 1rem; padding-bottom: 0rem; }
.canvas-border { border: 3px solid #333333; border-radius: 5px; }
[data-testid="stSidebar"] > div:first-child { padding-top: 60px; }
header [data-testid="stToolbar"] { visibility: hidden; height: 0; }
[data-testid="stStatusWidget"] { visibility: hidden; height: 0; }
[data-testid="stSidebarNav"] { visibility: hidden; height: 0; }
</style>
""", unsafe_allow_html=True)

# ======================
# Approval file
# ======================
APPROVAL_FILE = "approved_devices.csv"
if not os.path.exists(APPROVAL_FILE):
    pd.DataFrame(columns=["ip", "status", "request_time", "approved_time"]).to_csv(APPROVAL_FILE, index=False)

def load_approvals():
    return pd.read_csv(APPROVAL_FILE)

def save_approvals(df):
    df.to_csv(APPROVAL_FILE, index=False)

# ======================
# Mode check
# ======================
params = st.experimental_get_query_params()
mode = params.get("mode", [""])[0].lower()

if mode not in ["admin", "user"]:
    st.error("Mode tidak dikenali. Gunakan ?mode=admin atau ?mode=user")
    st.stop()

# ======================
# Admin Mode
# ======================
if mode == "admin":
    st.title("🔧 Admin Dashboard")
    password = st.text_input("Masukkan password admin:", type="password")
    if password != "Jakarta@24":
        st.error("Password salah")
        st.stop()

    st.success("Login Admin berhasil ✅")
    approvals = load_approvals()

    st.subheader("Daftar Request Access")
    requests = approvals[approvals["status"] == "pending"]
    if requests.empty:
        st.info("Tidak ada request akses baru.")
    else:
        for idx, row in requests.iterrows():
            st.write(f"IP: {row['ip']} — Request: {row['request_time']}")
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button(f"Approve {row['ip']}", key=f"approve_{idx}"):
                    approvals.loc[idx, "status"] = "approved"
                    approvals.loc[idx, "approved_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_approvals(approvals)
                    st.experimental_rerun()
            with col2:
                if st.button(f"Reject {row['ip']}", key=f"reject_{idx}"):
                    approvals.loc[idx, "status"] = "rejected"
                    approvals.loc[idx, "approved_time"] = ""
                    save_approvals(approvals)
                    st.experimental_rerun()

    st.subheader("Daftar Semua Device")
    if not approvals.empty:
        st.table(approvals)
    else:
        st.info("Belum ada device yang terdaftar.")

# ======================
# User Mode
# ======================
elif mode == "user":
    ip_user = socket.gethostbyname(socket.gethostname())
    approvals = load_approvals()
    approved_ips = approvals[approvals["status"] == "approved"]["ip"].tolist()

    if ip_user not in approved_ips:
        if ip_user not in approvals["ip"].tolist():
            approvals = pd.concat([approvals, pd.DataFrame([{
                "ip": ip_user,
                "status": "pending",
                "request_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "approved_time": ""
            }])], ignore_index=True)
            save_approvals(approvals)

        st.warning("⚠️ Device/IP Anda belum diapprove. Hubungi admin via WhatsApp.")
        st.markdown(
            '<a href="https://wa.me/628977742777" target="_blank">📲 Hubungi Admin via WhatsApp</a>',
            unsafe_allow_html=True
        )
        st.stop()

    st.success("✅ Akses diberikan. Menampilkan Topologi...")

    # ======================
    # Topology Script
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

    if "do_search" not in st.session_state:
        st.session_state.do_search = False
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

    def trigger_search():
        st.session_state.do_search = True

    col1, col2, col3 = st.columns([1,2,2])
    with col1:
        menu_option = st.radio("Pilih Tampilan:", ["Topology"])
    with col2:
        search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
    with col3:
        search_input = st.text_input(
            "🔍 Masukkan keyword (pisahkan dengan koma):",
            key="search_keyword",
            placeholder="Contoh: 16SBY0267, 16SBY0497",
            on_change=trigger_search
        )
    search_nodes = [s.strip() for s in search_input.split(",") if s.strip()]
    canvas_height = 350

    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <h2 style="
            position:sticky; 
            top:0;  
            background-color:white; 
            padding:12px;
            z-index:999; 
            border-bottom:1px solid #ddd; 
            margin:0;
        ">
            🧬 Topology Fiber Optic Active
        </h2>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.do_search or not search_nodes:
        st.info("ℹ️ Pilih kategori di atas, masukkan keyword (pisahkan dengan koma), lalu tekan Enter untuk menampilkan topology.")
    else:
        with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
            file_path = 'SEPTEMBER_FOA - Update_2025.xlsb'
            sheet_name = 'Query CW39_2025'
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
            df.columns = df.columns.str.strip()
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

        # filtering multiple keyword pakai OR (join dengan |)
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

                if col_member_ring and not ring_df.empty:
                    non_na_members = ring_df[col_member_ring].dropna()
                    members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                    st.markdown(
                        f'<p style="font-size:14px; color:gray; margin-top:-10px;">💡 Member Ring: {highlight_text(members_str, search_nodes)}</p>',
                        unsafe_allow_html=True
                    )

                ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip().replace({"nan": ""})

                nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]
                valid_dest_nodes = set(ring_df[col_dest].dropna().astype(str).str.strip().unique())
                valid_site_nodes = set(ring_df[col_site].dropna().astype(str).str.strip().unique())
                nodes_order = [n for n in nodes_order if n in valid_dest_nodes or n in valid_site_nodes]

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", directed=False)
                net.toggle_physics(False)

                node_degree = {}
                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s:
                        node_degree[s] = node_degree.get(s, 0) + 1
                    if t:
                        node_degree[t] = node_degree.get(t, 0) + 1

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
                    df_match = ring_df[ring_df[col_site].astype(str).str.strip() == nid]
                    if df_match.empty:
                        df_match = ring_df[ring_df[col_dest].astype(str).str.strip() == nid]
                    if df_match.empty:
                        return {"Fiber Type": "", "Site Name": "", "Host Name": "", "FLP Vendor": ""}
                    row0 = df_match.iloc[0]
                    return {
                        "Fiber Type": str(row0[col_fiber]) if col_fiber in row0 and pd.notna(row0[col_fiber]) else "",
                        "Site Name": str(row0[col_site_name]) if col_site_name in row0 and pd.notna(row0[col_site_name]) else "",
                        "Host Name": str(row0[col_host]) if col_host in row0 and pd.notna(row0[col_host]) else "",
                        "FLP Vendor": str(row0[col_flp]) if col_flp in row0 and pd.notna(row0[col_flp]) else ""
                    }

                for nid in nodes_order:
                    info = get_node_info(nid)
                    fiber = info["Fiber Type"].strip() if info["Fiber Type"] else ""
                    if node_degree.get(nid, 0) == 1 and fiber.lower() not in ["p0_1"]:
                        fiber = "P0"
                    f_low = fiber.lower()
                    node_image = (
                        "https://img.icons8.com/ios-filled/50/007FFF/router.png" if f_low=="dark fiber" else
                        "https://img.icons8.com/ios-filled/50/21793A/router.png" if f_low in ["p0","p0_1"] else
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

                    x, y = positions.get(nid, (0,0))
                    is_match = any(
                        re.search(re.escape(kw), nid, re.IGNORECASE) or 
                        re.search(re.escape(kw), title, re.IGNORECASE) 
                        for kw in search_nodes
                    )
                    font_color = "red" if is_match else "black"

                    net.add_node(
                        nid,
                        label="\n".join(label_parts),
                        x=x, y=y,
                        physics=False,
                        size=50,
                        shape="image",
                        image=node_image,
                        color={"border": "007FFF" if f_low=="dark fiber" else ("21793A" if f_low in ["p0","p0_1"] else "A2A2C2"), "background": "white"},
                        title=title,
                        font={"color": font_color}
                    )
                    added_nodes.add(nid)

                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if s and t and s.lower() not in ["nan","none"] and t.lower() not in ["nan","none"]:
                        flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
                        if s not in added_nodes:
                            net.add_node(s, label=s, font={"color": "red" if any(re.search(re.escape(kw), s, re.IGNORECASE) for kw in search_nodes) else "black"})
                            added_nodes.add(s)
                        if t not in added_nodes:
                            net.add_node(t, label=t, font={"color": "red" if any(re.search(re.escape(kw), t, re.IGNORECASE) for kw in search_nodes) else "black"})
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

                # ======================
                # Tabel Excel Member Ring
                # ======================
                table_cols = [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host]
                st.markdown("### 📋 Member Ring")
                display_df = ring_df[table_cols].fillna("").reset_index(drop=True).astype(str)
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: highlight_text(x, search_nodes))
                st.markdown(display_df.to_html(escape=False), unsafe_allow_html=True)


