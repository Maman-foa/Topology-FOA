import streamlit as st
import pandas as pd
import socket
import os
import re
from datetime import datetime
from pyvis.network import Network
import streamlit.components.v1 as components

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide", page_title="Fiber Optic Analyzer", page_icon="🧬")
st.markdown(
    """
    <style>
    .block-container { 
        padding-top: 1rem; 
        padding-bottom: 0rem; 
    }
    .canvas-border { 
        border: 3px solid #333333; 
        border-radius: 5px; 
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 60px;
    }
    header [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    [data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
    [data-testid="stSidebarNav"] {visibility: hidden; height: 0;}
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# Simpan file approval
# ======================
APPROVAL_FILE = "approved_devices.csv"
if not os.path.exists(APPROVAL_FILE):
    pd.DataFrame(columns=["ip", "status", "request_time", "approved_time"]).to_csv(APPROVAL_FILE, index=False)

def load_approvals():
    return pd.read_csv(APPROVAL_FILE)

def save_approvals(df):
    df.to_csv(APPROVAL_FILE, index=False)

# ======================
# Dapatkan mode (admin/user)
# ======================
mode = st.query_params.get("mode", ["user"])[0]

# ======================
# Highlight Text Function
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
# MODE ADMIN
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
            if st.button(f"Approve {row['ip']}", key=idx):
                approvals.loc[idx, "status"] = "approved"
                approvals.loc[idx, "approved_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_approvals(approvals)
                st.experimental_rerun()

    st.subheader("Daftar Semua Device")
    st.table(approvals)

# ======================
# MODE USER
# ======================
elif mode == "user":
    ip_user = socket.gethostbyname(socket.gethostname())
    approvals = load_approvals()
    approved_ips = approvals[approvals["status"] == "approved"]["ip"].tolist()

    if ip_user not in approved_ips:
        if ip_user not in approvals["ip"].tolist():
            approvals = approvals.append({
                "ip": ip_user,
                "status": "pending",
                "request_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "approved_time": ""
            }, ignore_index=True)
            save_approvals(approvals)

        st.warning("Device/IP Anda belum diapprove. Hubungi admin via WhatsApp.")
        st.markdown(
            '<a href="https://wa.me/628977742777" target="_blank">📲 Hubungi Admin via WhatsApp</a>',
            unsafe_allow_html=True
        )
        st.stop()

    st.success("✅ Akses diberikan. Menampilkan Topologi...")

    # === Bagian Topology ===
    col1, col2, col3 = st.columns([1,2,2])
    with col1:
        menu_option = st.radio("Pilih Tampilan:", ["Topology"])
    with col2:
        search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
    with col3:
        search_input = st.text_input(
            "🔍 Masukkan keyword (pisahkan dengan koma):",
            key="search_keyword",
            placeholder="Contoh: 16SBY0267, 16SBY0497"
        )
        search_nodes = [s.strip() for s in search_input.split(",") if s.strip()]

    canvas_height = 350

    if not search_nodes:
        st.info("ℹ️ Pilih kategori di atas, masukkan keyword (pisahkan dengan koma), lalu tekan Enter untuk menampilkan topology.")
    else:
        with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
            file_path = 'SEPTEMBER_FOA - Update_2025.xlsb'
            sheet_name = 'Query CW39_2025'
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
            df.columns = df.columns.str.strip()

            col_site = "New Site ID"
            col_dest = "New Destination"
            col_fiber = "Fiber Type"
            col_site_name = "Site Name"
            col_host = "Host Name"
            col_flp = "FLP Vendor"
            col_flp_len = "FLP LENGTH"
            col_syskey = "System Key"
            col_dest_name = "Destination Name"
            col_ring = "Ring ID"
            col_member_ring = "Member Ring"

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
                    nodes_order = list(pd.unique(pd.concat([ring_df[col_site], ring_df[col_dest]], ignore_index=True)))
                    nodes_order = [str(n).strip() for n in nodes_order if pd.notna(n) and str(n).strip().lower() not in ["", "none"]]

                    net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", directed=False)
                    net.toggle_physics(False)

                    positions = {nid: (i*200, (i//8)*200) for i, nid in enumerate(nodes_order)}

                    added_nodes = set()
                    for nid in nodes_order:
                        label_parts = [nid]
                        net.add_node(nid, label="\n".join(label_parts), x=positions[nid][0], y=positions[nid][1], physics=False, size=50)

                    for _, r in ring_df.iterrows():
                        s = str(r[col_site]).strip()
                        t = str(r[col_dest]).strip()
                        if s and t:
                            net.add_edge(s, t)

                    html_str = net.generate_html()
                    html_str = html_str.replace(
                        '<body>',
                        '<body><div class="canvas-border"></div>'
                    )
                    components.html(html_str, height=canvas_height, scrolling=False)
else:
    st.error("Mode tidak dikenali. Gunakan ?mode=admin atau ?mode=user")
