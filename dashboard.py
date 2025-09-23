import streamlit as st

# ======================
# Session state
# ======================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ======================
# Login dengan HTML
# ======================
def login_html():
    st.markdown(
        """
        <div style="max-width:400px; margin:auto; padding:20px; border:1px solid #ccc; border-radius:10px; background:#f9f9f9;">
            <h3 style="text-align:center;">🔐 Login</h3>
            <form action="" method="post">
                <input type="password" id="password" name="password"
                       placeholder="Masukkan Password"
                       style="width:100%; padding:10px; margin:10px 0; border-radius:5px; border:1px solid #aaa;">
                <button type="submit"
                        style="width:100%; padding:10px; background:#007FFF; color:white; border:none; border-radius:5px;">
                    Login
                </button>
            </form>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Streamlit hanya bisa tangkap input dengan widgetnya sendiri
    # jadi kita "miripkan" dengan HTML form di atas:
    password = st.text_input("", type="password", placeholder="Ketik password di sini")
    if st.button("Login via Python"):
        if password == "admin123":   # Ganti password sesuai kebutuhan
            st.session_state.authenticated = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Password salah!")

if not st.session_state.authenticated:
    login_html()
    st.stop()

# ======================
# Konten utama
# ======================
st.title("🎉 Selamat datang di Topology FOA")
st.write("Halaman ini hanya bisa dilihat setelah login.")
