import streamlit as st
import pandas as pd
import socket
import os
from datetime import datetime
import requests

# ======================
# Fungsi dapatkan public IP
# ======================
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return socket.gethostbyname(socket.gethostname())

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
if "mode" in st.query_params:
    mode = st.query_params["mode"][0].lower()
else:
    mode = "user"

# ======================
# Mode Admin
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
# Mode User
# ======================
else:
    ip_user = get_public_ip()
    approvals = load_approvals()
    approved_ips = approvals[approvals["status"] == "approved"]["ip"].tolist()

    if ip_user not in approved_ips:
        if ip_user not in approvals["ip"].tolist():
            new_request = pd.DataFrame([{
                "ip": ip_user,
                "status": "pending",
                "request_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "approved_time": ""
            }])
            approvals = pd.concat([approvals, new_request], ignore_index=True)
            save_approvals(approvals)

        st.warning("⚠️ Device/IP Anda belum diapprove. Hubungi admin via WhatsApp.")
        st.markdown(
            '<a href="https://wa.me/628977742777" target="_blank">📲 Hubungi Admin via WhatsApp</a>',
            unsafe_allow_html=True
        )
        st.stop()

    st.success("✅ Akses diberikan. Menampilkan Topologi...")
    # === Letakkan skrip Topology kamu di sini ===
    st.write("**Topology aktif untuk user ini**")
