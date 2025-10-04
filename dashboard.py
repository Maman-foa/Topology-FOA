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
    # ===== Real-time Refresh =====
    st_autorefresh = st.experimental_rerun  # fallback untuk Streamlit <1.25
    try:
        from streamlit.runtime.scriptrunner import add_script_run_ctx
    except ImportError:
        pass
    count = st.experimental_rerun if False else st.autorefresh(interval=5000, key="refresh_admin")

    # ===== Header =====
    devices = load_approved_devices()
    pending = [d for d in devices if not d.get("approved")]
    approved = [d for d in devices if d.get("approved")]

    notif_icon = "🔔" if len(pending) > 0 else "✅"
    notif_text = f" ({len(pending)} pending)" if len(pending) > 0 else ""

    st.title(f"🔐 Admin Panel {notif_icon}{notif_text}")

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

# (selanjutnya tetap sama persis dengan logika topology lama kamu)
