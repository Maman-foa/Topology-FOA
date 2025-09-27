import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import re

# ======================
# Page config & CSS
# ======================
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .block-container { 
        padding-top: 1rem; 
        padding-bottom: 0rem; 
    }
    mark {
        background-color: yellow;
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# Upload File
# ======================
uploaded_file = st.file_uploader("📂 Upload file Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    col_site = "New Site ID"
    col_dest = "New Destenation"
    col_ring = "Ring ID"

    # ======================
    # Input Search
    # ======================
    def trigger_search():
        st.session_state["search_triggered"] = True

    search_input = st.text_input(
        "🔍 Masukkan keyword (pisahkan dengan koma):",
        key="search_keyword",
        placeholder="Contoh: 16SBY0267, 16SBY0497",
        on_change=trigger_search
    )
    search_nodes = [s.strip() for s in search_input.split(",") if s.strip()]

    # ======================
    # Filtering
    # ======================
    if search_nodes:
        # Filter semua data yg mengandung salah satu keyword
        mask = df[col_site].astype(str).str.contains("|".join(search_nodes), case=False, na=False) | \
               df[col_dest].astype(str).str.contains("|".join(search_nodes), case=False, na=False) | \
               df[col_ring].astype(str).str.contains("|".join(search_nodes), case=False, na=False)

        df_filtered = df[mask].copy()

        if not df_filtered.empty:
            # Gabungkan semua Ring ID yang ketemu
            ring_ids = df_filtered[col_ring].dropna().unique()
            ring_ids_str = ", ".join(ring_ids)

            # Ambil semua data dari ring-ring tersebut
            ring_df_all = df[df[col_ring].isin(ring_ids)].copy()

            # ======================
            # Info Member Ring
            # ======================
            st.subheader("📌 Informasi Ring")
            st.markdown(f"**Ring ID Terdeteksi:** {ring_ids_str}")

            # ======================
            # Highlight function
            # ======================
            def highlight_text(text, keywords):
                if not keywords:
                    return text
                result = str(text)
                for kw in keywords:
                    pattern = re.compile(re.escape(kw), re.IGNORECASE)
                    result = pattern.sub(
                        lambda m: f"<mark>{m.group(0)}</mark>", 
                        result
                    )
                return result

            # ======================
            # Topology Network (satu kanvas saja)
            # ======================
            net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")

            for _, row in ring_df_all.iterrows():
                site = str(row[col_site])
                dest = str(row[col_dest])
                ring = str(row[col_ring])

                for node in [site, dest]:
                    is_match = any(re.search(re.escape(kw), node, re.IGNORECASE) for kw in search_nodes)
                    color = "red" if is_match else "lightblue"
                    net.add_node(node, label=node, color=color)

                net.add_edge(site, dest, title=ring)

            net.repulsion(node_distance=150, central_gravity=0.3,
                          spring_length=110, spring_strength=0.10,
                          damping=0.95)
            net.save_graph("network.html")

            with open("network.html", "r", encoding="utf-8") as f:
                components.html(f.read(), height=650)

            # ======================
            # Tabel Gabungan
            # ======================
            st.subheader("📑 Tabel Hasil Gabungan")
            df_display = ring_df_all.copy()
            df_display = df_display.applymap(lambda x: highlight_text(x, search_nodes))
            st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

        else:
            st.warning("⚠️ Tidak ada data yang cocok dengan keyword.")
    else:
        st.info("ℹ️ Masukkan keyword untuk mulai pencarian.")
