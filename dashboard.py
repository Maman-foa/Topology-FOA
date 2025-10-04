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
# Mode dari URL
# ======================
mode = st.query_params.get("mode", ["user"])[0]  # default = "user"

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
# Login untuk admin
# ======================
if mode == "admin":
    st.title("🔐 Admin Login")
    password = st.text_input("Masukkan Password Admin:", type="password")
    if st.button("Login"):
        if password == "Admin@123":
            st.session_state.admin_authenticated = True
        else:
            st.error("Password salah.")
    if not st.session_state.get("admin_authenticated", False):
        st.stop()
    st.write("✅ Admin mode aktif")

# ======================
# Login untuk user
# ======================
if mode == "user":
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 Login")
        password = st.text_input("Masukkan Password:", type="password")
        st.markdown("""
        <p style="text-align:center; margin-top:10px;">
            Jika lupa password, hubungi admin di:<br>
            <a href="https://wa.me/628977742777" target="_blank" style="text-decoration:none; font-weight:bold; color:green;">
                📲 Hubungi via WhatsApp
            </a>
        </p>
        """, unsafe_allow_html=True)
        if st.button("Login"):
            if password == "Jakarta@24":
                st.session_state.authenticated = True
            else:
                st.error("Password salah.")
        if not st.session_state.authenticated:
            st.stop()

# ======================
# Main App Logic
# ======================
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
st.markdown("""
<h2 style="position:sticky; top:0; background-color:white; padding:12px; z-index:999; border-bottom:1px solid #ddd; margin:0;">
    🧬 Topology Fiber Optic Active
</h2>
""", unsafe_allow_html=True)

# Isi konten app seperti skrip asli Anda...

st.write(f"Mode aktif: {mode}")

# Untuk admin, tampilkan halaman dashboard approve IP
if mode == "admin":
    st.header("Dashboard Admin")
    st.write("Daftar IP/device yang butuh approval")
    # Contoh tombol approve
    if st.button("Approve IP"): st.success("IP berhasil diapprove")

# Untuk user, tampilkan halaman utama topology seperti skrip asli Anda
