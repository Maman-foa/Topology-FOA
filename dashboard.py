import streamlit as st
import pandas as pd
import socket
import os
from datetime import datetime

# ======================
# Hapus warning Streamlit deprecated
# ======================
st.markdown(
    """
    <style>
    .stAlert {display: none !important;}
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
# Dapatkan mode (admin/user) — update sesuai Streamlit terbaru
# ======================
mode = st.query_params.get("mode", ["user"])[0]

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
    # === Letakkan skrip Topology kamu di sini ===
    st.write("**Topology aktif untuk user ini**")

else:
    st.error("Mode tidak dikenali. Gunakan ?mode=admin atau ?mode=user")
