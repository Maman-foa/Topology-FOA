import streamlit as st
import pandas as pd
import socket
import os
import datetime
import requests
from pyvis.network import Network
import streamlit.components.v1 as components

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide", page_title="Fiber Optic Topology")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h1, h2, h3, h4, h5, h6 {text-align: center;}
    .success-box {
        background-color: #e6ffe6; border: 1px solid #00cc44; padding: 10px;
        border-radius: 10px; color: #006622; text-align:center;
    }
    .warning-box {
        background-color: #fff4e6; border: 1px solid #ffa31a; padding: 10px;
        border-radius: 10px; color: #cc6600; text-align:center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# File CSV Approval
# ======================
APPROVAL_FILE = "approved_devices.csv"
if not os.path.exists(APPROVAL_FILE):
    pd.DataFrame(columns=["ip", "hostname", "status", "request_time", "approved_time"]).to_csv(APPROVAL_FILE, index=False)

# ======================
# Fungsi ambil IP publik
# ======================
def get_client_ip():
    try:
        ip = requests.get('https://api.ipify.org').text.strip()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())

# ======================
# Fungsi cek dan update approval
# ======================
def check_approval(ip, hostname):
    df = pd.read_csv(APPROVAL_FILE)
    if ip in df["ip"].values:
        status = df.loc[df["ip"] == ip, "status"].iloc[0]
        return status
    else:
        new_entry = pd.DataFrame([{
            "ip": ip,
            "hostname": hostname,
            "status": "pending",
            "request_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "approved_time": ""
        }])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(APPROVAL_FILE, index=False)
        return "pending"

# ======================
# Mode app
# ======================
mode = st.query_params.get("mode", ["user"])[0].lower().strip()

if mode not in ["admin", "user"]:
    st.error("❌ Mode tidak dikenali. Gunakan `?mode=admin` atau `?mode=user`")
    st.stop()

# ======================
# MODE ADMIN
# ======================
if mode == "admin":
    st.title("🔐 Admin Panel – Approval Device")

    df = pd.read_csv(APPROVAL_FILE)

    if df.empty:
        st.info("Belum ada request dari device manapun.")
        st.stop()

    # Pilih device berdasarkan status
    st.subheader("Daftar Device Pending Approval")
    pending_df = df[df["status"] == "pending"]
    approved_df = df[df["status"] == "approved"]

    if not pending_df.empty:
        selected_ip = st.selectbox("Pilih Device Pending:", pending_df["ip"])
        hostname = pending_df.loc[pending_df["ip"] == selected_ip, "hostname"].iloc[0]
        st.write(f"Hostname: `{hostname}`")

        col1, col2 = st.columns(2)
        if col1.button("✅ Approve"):
            df.loc[df["ip"] == selected_ip, "status"] = "approved"
            df.loc[df["ip"] == selected_ip, "approved_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.to_csv(APPROVAL_FILE, index=False)
            st.success(f"✅ Device {selected_ip} telah diapprove.")
            st.rerun()
        if col2.button("❌ Reject"):
            df = df[df["ip"] != selected_ip]
            df.to_csv(APPROVAL_FILE, index=False)
            st.warning(f"❌ Device {selected_ip} telah dihapus/reject.")
            st.rerun()
    else:
        st.info("Tidak ada device pending saat ini.")

    # Tabel Approved
    st.subheader("📋 Daftar Device Approved")
    if not approved_df.empty:
        st.dataframe(approved_df)
    else:
        st.info("Belum ada device yang diapprove.")

# ======================
# MODE USER
# ======================
elif mode == "user":
    st.title("🌐 Fiber Optic Topology")

    ip_user = get_client_ip()
    hostname_user = socket.gethostname()
    status = check_approval(ip_user, hostname_user)

    if status == "pending":
        st.markdown(
            f"""
            <div class="warning-box">
                ⚠️ Device/IP Anda belum diapprove.<br>
                Silakan hubungi admin untuk approval.
                <br><br>
                📲 Hubungi Admin via <a href="https://wa.me/6281234567890" target="_blank">WhatsApp</a>
                <br><br>
                <small><b>IP:</b> {ip_user}<br><b>Hostname:</b> {hostname_user}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    elif status == "approved":
        st.markdown(
            f"""
            <div class="success-box">
                ✅ Device/IP Anda sudah diapprove. Selamat datang!
                <br><br>
                <small><b>IP:</b> {ip_user}<br><b>Hostname:</b> {hostname_user}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ============== TOPOLOGY SECTION (asli punyamu) ==============
        # Contoh: ring_df diambil dari CSV lokal
        try:
            ring_df = pd.read_csv("data_topology.csv")
        except FileNotFoundError:
            st.warning("File data_topology.csv tidak ditemukan.")
            st.stop()

        # Clean-up kolom
        col_src, col_dest = ring_df.columns[:2]
        ring_df[col_src] = ring_df[col_src].astype(str).str.strip().replace({"nan": ""})
        ring_df[col_dest] = ring_df[col_dest].astype(str).str.strip().replace({"nan": ""})

        # Search bar
        keyword = st.text_input("🔍 Cari Node:", "")
        if keyword:
            filtered = ring_df[ring_df.apply(lambda x: keyword.lower() in x.astype(str).str.lower().to_string(), axis=1)]
        else:
            filtered = ring_df

        # Build Network
        net = Network(height="600px", bgcolor="#ffffff", font_color="black", directed=False)
        for _, row in filtered.iterrows():
            net.add_node(row[col_src], label=row[col_src])
            net.add_node(row[col_dest], label=row[col_dest])
            net.add_edge(row[col_src], row[col_dest])
        net.save_graph("topology.html")
        components.html(open("topology.html").read(), height=650)

        # Show Table
        st.dataframe(filtered)

    else:
        st.error("Terjadi kesalahan status device. Hubungi admin.")
