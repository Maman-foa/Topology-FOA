import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import socket
import re
import json
import os
from datetime import datetime

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
mode = query_params.get("mode", "user").lower().strip()

if mode not in ["admin", "user"]:
    st.error("❌ Mode tidak dikenali. Gunakan ?mode=admin atau ?mode=user")
    st.stop()

# ======================
# Fungsi highlight teks
# ======================
def highlight_text(text, keywords):
    if not keywords:
        return text
    result = str(text)
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        result = pattern.sub(
            lambda m: f"<mark style='background-color:yellow;color:black;'>{m.group(0)}</mark>", result
        )
    return result

# ==========================================================
# ====================== MODE ADMIN =========================
# ==========================================================
if mode == "admin":
    st.title("🔧 Admin Dashboard")
    password = st.text_input("Masukkan password admin:", type="password")
    if password != "Jakarta@24":
        st.error("Password salah ❌")
        st.stop()

    st.success("Login Admin berhasil ✅")
    devices = load_approved_devices()

    pending = [d for d in devices if not d.get("approved")]
    approved = [d for d in devices if d.get("approved")]

    st.subheader("📥 Pending Approval")
    if pending:
        for d in pending:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**IP:** {d['ip']}")
            with col2:
                st.write(f"**Hostname:** {d['hostname']}")
            with col3:
                if st.button(f"✅ Approve {d['ip']}", key=f"approve_{d['ip']}"):
                    d["approved"] = True
                    d["approved_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_approved_devices(devices)
                    st.success(f"{d['ip']} berhasil diapprove ✅")
                    st.rerun()
                if st.button(f"❌ Reject {d['ip']}", key=f"reject_{d['ip']}"):
                    devices.remove(d)
                    save_approved_devices(devices)
                    st.warning(f"{d['ip']} telah direject ❌")
                    st.rerun()
    else:
        st.info("Tidak ada request akses baru.")

    st.subheader("📋 Device Approved")
    if approved:
        for d in approved:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"✅ **{d['ip']}** — {d['hostname']}")
            with col2:
                st.write(f"Approved at: {d.get('approved_time', '-')}")
            with col3:
                if st.button(f"❌ Reject {d['ip']}", key=f"reject_approved_{d['ip']}"):
                    devices.remove(d)
                    save_approved_devices(devices)
                    st.warning(f"{d['ip']} telah direject ❌")
                    st.rerun()
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

st.title("🧬 Fiber Optic Topology")

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

# ========== Jika sudah approved ==========
st.success("✅ Akses diberikan. Menampilkan Topology...")

# ======================
# Session State
# ======================
if "do_search" not in st.session_state:
    st.session_state.do_search = False
if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""

def trigger_search():
    st.session_state.do_search = True

# ======================
# Menu + Search
# ======================
col1, col2, col3 = st.columns([1, 2, 2])
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
# Helper function untuk kolom
# ======================
def get_col(df, name, alt=None):
    if name in df.columns:
        return name
    if alt and alt in df.columns:
        return alt
    return None

# ======================
# Main Area (Ring & Topology)
# ======================
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <h2 style="position:sticky; top:0; background-color:white; padding:12px;
               z-index:999; border-bottom:1px solid #ddd; margin:0;">
        🧬 Topology Fiber Optic Active
    </h2>
    """,
    unsafe_allow_html=True
)

if not st.session_state.do_search or not search_nodes:
    st.info("ℹ️ Pilih kategori di atas, masukkan keyword (pisahkan dengan koma), lalu tekan Enter untuk menampilkan topology.")
else:
    with st.spinner("⏳ Sedang memuat data dan membangun topology..."):
        # TODO: Ganti dengan file kamu
        file_path = 'SEPTEMBER_FOA - Update_2025.xlsb'
        sheet_name = 'Query CW39_2025'
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="pyxlsb")
        df.columns = df.columns.str.strip()

        # Cek kolom penting
        col_site = get_col(df, "New Site ID")
        col_dest = get_col(df, "New Destination", alt="New Destenation")
        if not col_site or not col_dest:
            st.error("Kolom 'New Site ID' atau 'New Destination' tidak ditemukan di Excel.")
            st.stop()

        # Filter sesuai input
        pattern = "|".join(map(re.escape, search_nodes))
        if search_by == "New Site ID":
            df_filtered = df[df[col_site].astype(str).str.contains(pattern, case=False, na=False)]
        elif search_by == "Ring ID":
            col_ring = get_col(df, "Ring ID")
            df_filtered = df[df[col_ring].astype(str).str.contains(pattern, case=False, na=False)]
        else:
            col_host = get_col(df, "Host Name", alt="Hostname")
            df_filtered = df[df[col_host].astype(str).str.contains(pattern, case=False, na=False)]

        if df_filtered.empty:
            st.warning("⚠️ Node tidak ditemukan di data.")
        else:
            st.dataframe(df_filtered.head())
            net = Network(height="550px", width="100%", bgcolor="#FFFFFF", directed=False)
            for _, row in df_filtered.iterrows():
                s = str(row[col_site]).strip()
                t = str(row[col_dest]).strip()
                if s and t:
                    net.add_node(s, label=s)
                    net.add_node(t, label=t)
                    net.add_edge(s, t)

            net.save_graph("topology.html")
            HtmlFile = open("topology.html", "r", encoding="utf-8")
            components.html(HtmlFile.read(), height=550)
