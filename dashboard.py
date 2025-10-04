import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import re
import os
import socket

# ======================
# CONFIG
# ======================
APPROVAL_FILE = "ip_approval.csv"  # File untuk menyimpan IP approval

# ======================
# Helper untuk IP & Approval
# ======================
def get_user_ip():
    """Dapatkan IP pengguna."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip
    except:
        return "unknown"

def load_approval_data():
    if os.path.exists(APPROVAL_FILE):
        return pd.read_csv(APPROVAL_FILE)
    return pd.DataFrame(columns=["ip", "approved"])

def save_approval_data(df):
    df.to_csv(APPROVAL_FILE, index=False)

def is_ip_approved(ip):
    df = load_approval_data()
    if not df.empty:
        approved_row = df[(df["ip"] == ip) & (df["approved"] == True)]
        return not approved_row.empty
    return False

def request_approval(ip):
    df = load_approval_data()
    if ip not in df["ip"].values:
        df = pd.concat([df, pd.DataFrame([{"ip": ip, "approved": False}])], ignore_index=True)
        save_approval_data(df)

# ======================
# Auto Admin Approval Panel
# ======================
def admin_auto_approve_panel():
    st.subheader("🔧 Panel Admin - Approve IP")
    df = load_approval_data()

    # Filter IP yang belum diapprove
    pending_ips = df[df["approved"] == False]

    if pending_ips.empty:
        st.info("✅ Tidak ada request approval.")
        return

    st.table(pending_ips)

    for idx, row in pending_ips.iterrows():
        if st.button(f"Approve IP {row['ip']}", key=f"approve_{idx}"):
            df.loc[idx, "approved"] = True
            save_approval_data(df)
            st.success(f"IP {row['ip']} telah diapprove.")
            st.experimental_rerun()

# ======================
# Login Device/IP Approval
# ======================
user_ip = get_user_ip()

if user_ip == "unknown":
    st.error("Tidak dapat mendeteksi IP Anda.")
    st.stop()

if not is_ip_approved(user_ip):
    st.warning(f"Device/IP Anda ({user_ip}) belum diapprove. Silakan hubungi admin via WhatsApp.")
    request_approval(user_ip)
    st.markdown(
        f"""
        <p style="text-align:center; margin-top:10px;">
            Hubungi admin untuk approval:<br>
            <a href="https://wa.me/628977742777" target="_blank" style="text-decoration:none; font-weight:bold; color:green;">
                📲 Hubungi via WhatsApp
            </a>
        </p>
        """,
        unsafe_allow_html=True
    )
    st.stop()

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
# Session state
# ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "do_search" not in st.session_state:
    st.session_state.do_search = False
if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""

# ======================
# Password Login
# ======================
def login():
    st.title("🔐 Login")
    password = st.text_input("Masukkan Password:", type="password")

    st.markdown(
        """
        <p style="text-align:center; margin-top:10px;">
            Jika lupa password, hubungi admin di:<br>
            <a href="https://wa.me/628977742777" target="_blank" style="text-decoration:none; font-weight:bold; color:green;">
                📲 Hubungi via WhatsApp
            </a>
        </p>
        """,
        unsafe_allow_html=True
    )

    if st.button("Login"):
        if password == "Jakarta@24":
            st.session_state.authenticated = True
            st.success("Login berhasil! 🎉")
            admin_auto_approve_panel()  # langsung tampilkan panel approval
        else:
            st.error("Password salah.")

if not st.session_state.authenticated:
    login()
    st.stop()

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
        on_change=lambda: st.session_state.update({"do_search": True})
    )
    search_nodes = [s.strip() for s in search_input.split(",") if s.strip()]

canvas_height = 350

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
