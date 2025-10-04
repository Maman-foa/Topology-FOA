import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import socket
import re
import json
import os

# ======================
# Konfigurasi halaman
# ======================
st.set_page_config(page_title="Fiber Optic Analyzer", layout="wide", page_icon="🧬")

st.markdown("""
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
""", unsafe_allow_html=True)

# ======================
# File penyimpanan approval device
# ======================
APPROVAL_FILE = "approved_devices.json"

if not os.path.exists(APPROVAL_FILE):
    with open(APPROVAL_FILE, "w") as f:
        json.dump([], f)

# ======================
# Fungsi utilitas approval
# ======================
def load_approved_devices():
    with open(APPROVAL_FILE, "r") as f:
        return json.load(f)

def save_approved_devices(data):
    with open(APPROVAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ======================
# Dapatkan info device/IP
# ======================
def get_device_info():
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "Unknown"
    hostname = socket.gethostname()
    return ip, hostname

# ======================
# Mode app (admin / user)
# ======================
query_params = st.query_params
mode = query_params.get("mode", "user")
mode = mode.lower().strip()

if mode not in ["admin", "user"]:
    st.error("❌ Mode tidak dikenali. Gunakan ?mode=admin atau ?mode=user")
    st.stop()

# ======================
# Fungsi highlight
# ======================
def highlight_text(text, keywords):
    if not keywords:
        return text
    result = str(text)
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        result = pattern.sub(lambda m: f"<mark style='background-color:yellow;color:black;'>{m.group(0)}</mark>", result)
    return result

# ==========================================================
# ====================== MODE ADMIN =========================
# ==========================================================
if mode == "admin":
    st.title("🔐 Admin Panel – Approval Device")

    devices = load_approved_devices()
    pending = [d for d in devices if not d.get("approved")]
    approved = [d for d in devices if d.get("approved")]

    st.subheader("📥 Pending Approval")
    if pending:
        for dev in pending:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**IP:** {dev['ip']}")
            with col2:
                st.write(f"**Hostname:** {dev['hostname']}")
            with col3:
                if st.button("✅ Approve", key=f"approve_{dev['ip']}"):
                    dev["approved"] = True
                    save_approved_devices(devices)
                    st.success(f"Device {dev['ip']} disetujui ✅")
                    st.rerun()
                if st.button("❌ Reject", key=f"reject_{dev['ip']}"):
                    devices.remove(dev)
                    save_approved_devices(devices)
                    st.warning(f"Device {dev['ip']} dihapus ❌")
                    st.rerun()
    else:
        st.info("Tidak ada device pending approval.")

    st.subheader("📋 Device Approved")
    if approved:
        for dev in approved:
            st.write(f"✅ {dev['ip']} – {dev['hostname']}")
    else:
        st.info("Belum ada device yang diapprove.")
    st.stop()

# ==========================================================
# ====================== MODE USER ==========================
# ==========================================================
ip, hostname = get_device_info()
devices = load_approved_devices()
found = next((d for d in devices if d["ip"] == ip), None)

if not found:
    devices.append({"ip": ip, "hostname": hostname, "approved": False})
    save_approved_devices(devices)
    found = {"ip": ip, "hostname": hostname, "approved": False}

st.title("🌐 Fiber Optic Topology")

if not found.get("approved"):
    st.warning("⚠️ Device/IP Anda belum diapprove.\nSilakan hubungi admin untuk approval.")
    st.markdown("""
        <p style="text-align:center;">
            📲 <a href="https://wa.me/628977742777" target="_blank" 
            style="text-decoration:none; color:green; font-weight:bold;">Hubungi Admin via WhatsApp</a>
        </p>
    """, unsafe_allow_html=True)
    st.info(f"**IP:** {ip}\n\n**Hostname:** {hostname}")
    st.stop()

# ======================
# Session state user
# ======================
if "do_search" not in st.session_state:
    st.session_state.do_search = False
if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""

# ======================
# Fungsi pencarian
# ======================
def trigger_search():
    st.session_state.do_search = True

# ======================
# Menu + Search
# ======================
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

# ======================
# Helper get_col
# ======================
def get_col(df, name, alt=None):
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

# ======================
# Tampilan utama user
# ======================
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
st.markdown("""
<h2 style="
    position:sticky;
    top:0;
    background-color:white;
    padding:12px;
    z-index:999;
    border-bottom:1px solid #ddd;
    margin:0;">
    🧬 Topology Fiber Optic Active
</h2>
""", unsafe_allow_html=True)

if not st.session_state.do_search or not search_nodes:
    st.info("ℹ️ Pilih kategori, masukkan keyword (pisahkan dengan koma), lalu tekan Enter untuk tampilkan topology.")
else:
    with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
        file_path = 'SEPTEMBER_FOA - Update_2025.xlsb'
        sheet_name = 'Query CW39_2025'
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

        col_site = get_col(df, "New Site ID")
        col_dest = get_col(df, "New Destenation", alt="New Destination")
        if not col_dest:
            st.error("Kolom tujuan (New Destination) tidak ditemukan di file Excel.")
            st.stop()

        col_fiber = get_col(df, "Fiber Type")
        col_site_name = get_col(df, "Site Name")
        col_host = get_col(df, "Host Name", alt="Hostname")
        col_flp = get_col(df, "FLP Vendor")
        col_flp_len = get_col(df, "FLP LENGTH")
        col_syskey = get_col(df, "System Key")
        col_dest_name = get_col(df, "Destination Name")
        col_ring = get_col(df, "Ring ID")
        col_member_ring = get_col(df, "Member Ring")

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
            for ring in df_filtered["Ring ID"].dropna().unique():
                st.markdown(f"### 🔗 Ring ID: {highlight_text(ring, search_nodes)}", unsafe_allow_html=True)
                ring_df = df[df["Ring ID"] == ring].copy()

                if col_member_ring and not ring_df.empty:
                    non_na_members = ring_df[col_member_ring].dropna()
                    members_str = str(non_na_members.iloc[0]) if not non_na_members.empty else ""
                    st.markdown(f"<p style='font-size:14px; color:gray;'>💡 Member Ring: {highlight_text(members_str, search_nodes)}</p>", unsafe_allow_html=True)

                ring_df[col_site] = ring_df[col_site].astype(str).str.strip()
                ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip().replace({"nan": ""})

                net = Network(height=f"{canvas_height}px", width="100%", bgcolor="#f8f8f8", directed=False)
                net.toggle_physics(False)

                for _, r in ring_df.iterrows():
                    s = str(r[col_site]).strip()
                    t = str(r[col_dest]).strip()
                    if not s or not t:
                        continue
                    net.add_node(s, label=s)
                    net.add_node(t, label=t)
                    net.add_edge(s, t)

                html_str = net.generate_html()
                html_str = html_str.replace('<body>', '<body><div class="canvas-border">')
                components.html(html_str, height=canvas_height, scrolling=False)

                # tampilkan tabel
                table_cols = [c for c in [col_syskey, col_flp, col_site, col_site_name, col_dest, col_dest_name, col_fiber, col_ring, col_host] if c]
                display_df = ring_df[table_cols].fillna("").astype(str)
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: highlight_text(x, search_nodes))
                st.markdown("### 📋 Member Ring")
                st.markdown(display_df.to_html(escape=False), unsafe_allow_html=True)
