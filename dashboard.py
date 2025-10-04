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
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    .canvas-border { border: 3px solid #333333; border-radius: 5px; }
    [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    [data-testid="stSidebar"] > div:first-child { padding-top: 60px; }
    [data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
    [data-testid="stSidebarNav"] {visibility: hidden; height: 0;}
    div[role="alert"] {display: none !important;} /* Hide warning */
    </style>
    """,
    unsafe_allow_html=True
)

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
        for idx, row in approvals.iterrows():
            col1, col2, col3 = st.columns([2,1,1])
            col1.write(f"IP: {row['ip']} — Status: {row['status']} — Request: {row['request_time']}")
            with col2:
                if st.button(f"Approve", key=f"approve_all_{idx}"):
                    approvals.loc[idx, "status"] = "approved"
                    approvals.loc[idx, "approved_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_approvals(approvals)
                    st.experimental_rerun()
            with col3:
                if st.button(f"Reject", key=f"reject_all_{idx}"):
                    approvals.loc[idx, "status"] = "rejected"
                    approvals.loc[idx, "approved_time"] = ""
                    save_approvals(approvals)
                    st.experimental_rerun()
    else:
        st.info("Belum ada device yang terdaftar.")

    st.table(approvals)

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

    # ======================
    # Topology Search
    # ======================
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "do_search" not in st.session_state:
        st.session_state.do_search = False
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

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
            else:
                st.error("Password salah.")

    if not st.session_state.authenticated:
        login()
        st.stop()

    # === Topology Script dari skrip kamu ===
    # Letakkan seluruh isi skrip Topology Search di sini
    # (copy langsung dari skrip yang kamu kirimkan sebelumnya)
    # Aku akan gabungkan penuh, agar topology bisa berjalan setelah login user berhasil

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

    # Di sini lanjutkan bagian search topology seperti skrip yang kamu kirim sebelumnya...
