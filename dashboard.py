# ======================
# Konten FLP Vendor
# ======================
if menu_option == "FLP Vendor":
    df_filtered = df[df[col_flp].astype(str).str.contains(search_node, case=False, na=False)]

    if df_filtered.empty:
        st.warning("⚠️ Data tidak ditemukan.")
    else:
        # gabungkan semua Ring ID ke satu kanvas
        net = Network(height="700px", width="100%", bgcolor="#f8f8f8", font_color="black", directed=False)
        net.toggle_physics(True)

        # tambahkan node & edge
        added_nodes = set()
        for _, r in df_filtered.iterrows():
            s = str(r[col_site]).strip()
            t = str(r[col_dest]).strip()
            if not s or not t or s.lower() in ["nan","none"] or t.lower() in ["nan","none"]:
                continue

            # info node
            def get_node_info(nid):
                df_match = df_filtered[df_filtered[col_site].astype(str).str.strip() == nid]
                if df_match.empty:
                    df_match = df_filtered[df_filtered[col_dest].astype(str).str.strip() == nid]
                if df_match.empty:
                    return {"Fiber Type":"", "Site Name":"", "Host Name":"", "FLP Vendor":""}
                row0 = df_match.iloc[0]
                return {
                    "Fiber Type": str(row0[col_fiber]) if col_fiber in row0 and pd.notna(row0[col_fiber]) else "",
                    "Site Name": str(row0[col_site_name]) if col_site_name in row0 and pd.notna(row0[col_site_name]) else "",
                    "Host Name": str(row0[col_host]) if col_host in row0 and pd.notna(row0[col_host]) else "",
                    "FLP Vendor": str(row0[col_flp]) if col_flp in row0 and pd.notna(row0[col_flp]) else ""
                }

            for nid in [s, t]:
                if nid not in added_nodes:
                    info = get_node_info(nid)
                    label_parts = [nid]
                    if info["Site Name"]: label_parts.append(info["Site Name"])
                    if info["Host Name"]: label_parts.append(info["Host Name"])
                    if info["FLP Vendor"]: label_parts.append(info["FLP Vendor"])
                    title = "<br>".join([p for p in label_parts if p])

                    net.add_node(
                        nid,
                        label="\n".join(label_parts),
                        shape="dot",
                        size=25,
                        color={"background": "#007FFF", "border": "#333"},
                        title=title
                    )
                    added_nodes.add(nid)

            flp_len = r[col_flp_len] if col_flp_len in r and pd.notna(r[col_flp_len]) else ""
            net.add_edge(s, t, label=str(flp_len) if flp_len else "", width=2, color="red")

        # generate html & inject search box
        html_str = net.generate_html()
        search_js = """
        <input type="text" id="nodeSearch" placeholder="🔍 Cari Site ID..."
               style="position:absolute; top:10px; left:50px; z-index:999; padding:5px;
                      border:1px solid #ccc; border-radius:4px;">
        <script type="text/javascript">
        var input = document.getElementById('nodeSearch');
        input.addEventListener("keyup", function(event) {
          if (event.key === "Enter") {
            var query = input.value.trim();
            if(query){
                var nodeId = null;
                var allNodes = nodes.get();
                for (var i=0; i<allNodes.length; i++){
                    if (allNodes[i].label.includes(query)){
                        nodeId = allNodes[i].id;
                        break;
                    }
                }
                if(nodeId){
                    network.selectNodes([nodeId]);
                    network.focus(nodeId, {scale:1.5, animation:true});
                } else {
                    alert("Site ID tidak ditemukan!");
                }
            }
          }
        });
        </script>
        """
        html_str = html_str.replace("</body>", search_js + "</body>")
        components.html(html_str, height=800, scrolling=True)
