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
mode = st.query_params.get("mode", ["user"])
mode = mode[0] if mode else "user"

if mode not in ["admin", "user"]:
    st.error("Mode tidak dikenali. Gunakan ?mode=admin atau ?mode=user")
    st.stop()

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
else:
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

        st.warning("⚠️ Device/IP Anda belum diapprove. Hubungi admin via WhatsApp.")
        st.markdown(
            '<a href="https://wa.me/628977742777" target="_blank">📲 Hubungi Admin via WhatsApp</a>',
            unsafe_allow_html=True
        )
        st.stop()

    st.success("✅ Akses diberikan. Menampilkan Topologi...")

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
    # Topologi UI
    # ======================
    col1, col2, col3 = st.columns([1,2,2])
    with col1:
        menu_option = st.radio("Pilih Tampilan:", ["Topology"])
    with col2:
        search_by = st.selectbox("Cari berdasarkan:", ["New Site ID", "Ring ID", "Host Name"])
    with col3:
        search_input = st.text_input(
            "🔍 Masukkan keyword (pisahkan dengan koma):",
            placeholder="Contoh: 16SBY0267, 16SBY0497"
        )
        search_nodes = [s.strip() for s in search_input.split(",") if s.strip()]

    if not search_nodes:
        st.info("ℹ️ Masukkan keyword di atas untuk memulai pencarian.")
    else:
        st.markdown("**📊 Menampilkan Topologi berdasarkan pencarian...**")
        # Letakkan logika Topology kamu di sini (dari skrip kedua kamu)
        st.write("Topology aktif untuk user ini")
