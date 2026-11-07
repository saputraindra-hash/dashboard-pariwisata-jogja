import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
from shapely.geometry import Point, Polygon
import json
import os

def Tampilkan():
    st.title("🚨 DSS: Keselamatan Wisata & Mitigasi Terpadu")
    st.markdown("Pusat Komando Analisis **Double-Hazard**: Integrasi Navigasi Medis (Faskes), Keamanan (Kepolisian), dan Mitigasi Kawasan Rawan Bencana (KRB) secara *Real-Time*.")
    
    col_slider1, col_slider2 = st.columns(2)
    with col_slider1:
        radius_medis = st.slider("Batas Aman Jarak Faskes (Km):", 1.0, 20.0, 5.0, 0.5)
    with col_slider2:
        radius_polisi = st.slider("Batas Aman Jarak Polisi (Km):", 1.0, 20.0, 7.0, 0.5)
        
    batas_medis_m = radius_medis * 1000 
    batas_polisi_m = radius_polisi * 1000 
    
    @st.cache_data(ttl=3600)
    def fetch_api_gdf(url, geom_type="point", backup_file="backup.json"):
        try:
            res = requests.get(url, timeout=10).json()
            with open(backup_file, 'w') as f:
                json.dump(res, f)
        except Exception:
            if os.path.exists(backup_file):
                with open(backup_file, 'r') as f:
                    res = json.load(f)
            else:
                return gpd.GeoDataFrame(), {}
                
        if 'features' not in res: return gpd.GeoDataFrame(), res
        
        records = []
        for f in res['features']:
            geom = f.get('geometry')
            if not geom: continue
            attr = f.get('attributes', {})
            
            if geom_type == "point":
                attr['Lon'], attr['Lat'] = geom.get('x'), geom.get('y')
                nama = "Tidak Bernama"
                for key, value in attr.items():
                    if any(x in key.lower() for x in ['nama', 'name', 'nm_', 'faskes', 'dtw', 'wisata']):
                        if value and not any(x in key.lower() for x in ['kode', 'kd_', 'id']):
                            nama = str(value).strip()
                            break
                attr['nama_tampil'] = nama
            records.append(attr)
            
        df = pd.DataFrame(records)
        if geom_type == "point" and not df.empty:
            df = df.dropna(subset=['Lat', 'Lon'])
            return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['Lon'], df['Lat'])], crs="EPSG:4326"), res
        return gpd.GeoDataFrame(), res

    def get_mock_polisi():
        # Data Simulasi Polisi jika API belum siap
        df = pd.DataFrame({
            'nama_tampil': ['Polresta Yogyakarta', 'Polres Sleman', 'Polres Bantul', 'Polres Gunungkidul', 'Polres Kulon Progo', 'Polsek Depok Timur'],
            'Lat': [-7.803, -7.710, -7.885, -7.964, -7.860, -7.755],
            'Lon': [110.364, 110.334, 110.330, 110.602, 110.155, 110.405]
        })
        return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['Lon'], df['Lat'])], crs="EPSG:4326")

    def get_mock_krb():
        # Data Simulasi Poligon Bencana: Merapi (Radius 13km) & Tsunami Pantai Selatan
        merapi = Point(110.446, -7.540).buffer(0.12) 
        tsunami = Polygon([(110.0, -8.05), (110.8, -8.05), (110.8, -7.98), (110.0, -7.98)])
        return gpd.GeoDataFrame({'nama_tampil': ['KRB III Gunung Merapi', 'Zona Rawan Tsunami Selatan']}, geometry=[merapi, tsunami], crs="EPSG:4326")

    def get_osrm_route(lon1, lat1, lon2, lat2):
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get("code") == "Ok":
                r = res["routes"][0]
                return r["distance"]/1000, r["duration"]/60, [[c[1], c[0]] for c in r["geometry"]["coordinates"]]
        except: pass
        return None, None, None

    with st.spinner("🔄 Memuat Ekosistem Geospasial (Wisata, Medis, Polisi, KRB Bencana)..."):
        url_wisata = "https://geoportal.jogjaprov.go.id/server/rest/services/DISPAR/34_DISPAR_KUNJ_DTW_2023_PT/FeatureServer/0/query?outFields=*&where=1%3D1&outSR=4326&f=json"
        url_faskes = "https://geoportal.jogjaprov.go.id/server/rest/services/BPJS/_34_BPJS_FASKES_PT/FeatureServer/216/query?outFields=*&where=1%3D1&outSR=4326&f=json"
        
        wisata_gdf, _ = fetch_api_gdf(url_wisata, "point", "backup_wisata.json")
        faskes_gdf, _ = fetch_api_gdf(url_faskes, "point", "backup_faskes.json")
        polisi_gdf = get_mock_polisi()
        krb_gdf = get_mock_krb()
        
        if not wisata_gdf.empty and not faskes_gdf.empty:
            wisata_utm = wisata_gdf.to_crs("EPSG:32749")
            faskes_utm = faskes_gdf.to_crs("EPSG:32749")
            polisi_utm = polisi_gdf.to_crs("EPSG:32749")
            krb_utm = krb_gdf.to_crs("EPSG:32749")
            
            # 1. Join Faskes
            join_faskes = gpd.sjoin_nearest(wisata_utm, faskes_utm, how='left', distance_col='Jarak_Faskes')
            # 2. Join Polisi
            join_polisi = gpd.sjoin_nearest(wisata_utm, polisi_utm, how='left', distance_col='Jarak_Polisi')
            # 3. Overlay KRB
            join_krb = gpd.sjoin(wisata_utm, krb_utm, how='left', predicate='intersects')
            
            evaluasi = wisata_gdf.copy()
            nama_col = 'nama_tampil_left' if 'nama_tampil_left' in join_faskes.columns else 'nama_tampil'
            evaluasi['Nama_Wisata'] = join_faskes[nama_col]
            evaluasi['Idx_Faskes'] = join_faskes['index_right']
            evaluasi['Jarak_Faskes'] = join_faskes['Jarak_Faskes']
            evaluasi['Idx_Polisi'] = join_polisi['index_right']
            evaluasi['Jarak_Polisi'] = join_polisi['Jarak_Polisi']
            
            # Deteksi Bencana
            evaluasi['Zona_Bencana'] = join_krb['nama_tampil_right'].fillna("Aman")
            evaluasi['In_KRB'] = evaluasi['Zona_Bencana'] != "Aman"
            
            # Kategorisasi Keamanan
            rawan_medis = evaluasi['Jarak_Faskes'] > batas_medis_m
            rawan_polisi = evaluasi['Jarak_Polisi'] > batas_polisi_m
            
            evaluasi['Status'] = "🔵 Aman"
            evaluasi.loc[rawan_medis | rawan_polisi | evaluasi['In_KRB'], 'Status'] = "🟠 Rawan (Single Hazard)"
            evaluasi.loc[(rawan_medis | rawan_polisi) & evaluasi['In_KRB'], 'Status'] = "🔴 Bahaya Ganda (Double Hazard)"

            # ==================================================================
            # DASHBOARD ANALITIK EKSEKUTIF
            # ==================================================================
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Destinasi Wisata", len(evaluasi))
            c2.metric("🏥 Rawan Akses Medis", len(evaluasi[rawan_medis]))
            c3.metric("🚓 Rawan Akses Keamanan", len(evaluasi[rawan_polisi]))
            c4.metric("🌋 Masuk Zona Bencana", len(evaluasi[evaluasi['In_KRB']]))
            
            st.markdown("### 📊 Analisis Double-Hazard (Kawasan Paling Berisiko)")
            st.warning("Menampilkan destinasi yang berada di dalam **Kawasan Rawan Bencana (Merapi/Tsunami)** sekaligus memiliki jarak yang jauh dari intervensi Medis & Polisi.")
            
            df_bahaya = evaluasi[evaluasi['Status'] == "🔴 Bahaya Ganda (Double Hazard)"].copy()
            if not df_bahaya.empty:
                df_tabel = df_bahaya[['Nama_Wisata', 'Zona_Bencana', 'Jarak_Faskes', 'Jarak_Polisi']].copy()
                df_tabel['Jarak Faskes (Km)'] = (df_tabel['Jarak_Faskes'] / 1000).round(1)
                df_tabel['Jarak Polisi (Km)'] = (df_tabel['Jarak_Polisi'] / 1000).round(1)
                df_tabel = df_tabel[['Nama_Wisata', 'Zona_Bencana', 'Jarak Faskes (Km)', 'Jarak Polisi (Km)']].reset_index(drop=True)
                df_tabel.index += 1
                st.dataframe(df_tabel, use_container_width=True)
            else:
                st.success("Terkendali. Tidak ada destinasi dengan status Bahaya Ganda pada batas radius saat ini.")

            st.markdown("---")
            # ==================================================================
            # PETA & DUAL-ROUTING OSRM (MEDIS + POLISI)
            # ==================================================================
            st.markdown("### 🛰️ Sistem Navigasi Respons Cepat (112 & 119)")
            
            df_pilihan = evaluasi[evaluasi['Status'] != "🔵 Aman"]
            daftar_investigasi = df_pilihan['Nama_Wisata'].tolist()
            
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                titik_investigasi = st.selectbox("Pilih Titik Darurat untuk Simulasi Navigasi:", daftar_investigasi)
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True) 
                tombol_routing = st.button("🚨 Kerahkan Bantuan", type="primary", use_container_width=True)

            m_master = folium.Map(location=[-7.90, 110.50], zoom_start=10, tiles='CartoDB positron')

            # Render Poligon KRB
            folium.GeoJson(
                krb_gdf, 
                style_function=lambda x: {'fillColor': '#ff0000', 'color': '#ff0000', 'weight': 1, 'fillOpacity': 0.15},
                tooltip=folium.GeoJsonTooltip(fields=['nama_tampil'], aliases=['Zona Bencana:'])
            ).add_to(m_master)

            # Render Polisi & Faskes
            for _, r in polisi_gdf.iterrows():
                folium.Marker([r.geometry.y, r.geometry.x], tooltip=f"🚓 {r['nama_tampil']}", icon=folium.Icon(color='darkblue', icon='shield')).add_to(m_master)
            for _, r in faskes_gdf.iterrows():
                folium.CircleMarker([r.geometry.y, r.geometry.x], radius=3, color="green", fill=True, tooltip=f"🏥 {r['nama_tampil']}").add_to(m_master)

            # Render Wisata
            for _, r in evaluasi.iterrows():
                warna = "blue" if r['Status'] == "🔵 Aman" else ("orange" if "Single" in r['Status'] else "red")
                rad = 4 if warna == "blue" else 6
                folium.CircleMarker([r.geometry.y, r.geometry.x], radius=rad, color=warna, fill=True, tooltip=f"{r['Nama_Wisata']} ({r['Status']})").add_to(m_master)

            if tombol_routing and titik_investigasi:
                w_row = evaluasi[evaluasi['Nama_Wisata'] == titik_investigasi].iloc[0]
                lon_w, lat_w = w_row.geometry.x, w_row.geometry.y
                
                f_row = faskes_gdf.loc[w_row['Idx_Faskes']]
                p_row = polisi_gdf.loc[w_row['Idx_Polisi']]
                
                with st.spinner("🛰️ Menghitung Rute Bantuan Ganda..."):
                    dist_f, dur_f, route_f = get_osrm_route(lon_w, lat_w, f_row.geometry.x, f_row.geometry.y)
                    dist_p, dur_p, route_p = get_osrm_route(lon_w, lat_w, p_row.geometry.x, p_row.geometry.y)
                    
                    c_info1, c_info2 = st.columns(2)
                    if route_f:
                        c_info1.error(f"🚑 **Ambulans ({f_row['nama_tampil']})**\n\nJarak: {dist_f:.1f} Km | ETA: {dur_f:.0f} Menit")
                        folium.PolyLine(route_f, color="#d9534f", weight=6, opacity=0.8, tooltip="Rute Ambulans").add_to(m_master)
                    if route_p:
                        c_info2.info(f"🚓 **Polisi ({p_row['nama_tampil']})**\n\nJarak: {dist_p:.1f} Km | ETA: {dur_p:.0f} Menit")
                        folium.PolyLine(route_p, color="#0275d8", weight=6, opacity=0.8, tooltip="Rute Patroli Polisi").add_to(m_master)
                        
                    if route_f or route_p:
                        m_master.fit_bounds(route_f if route_f else route_p)

            st_folium(m_master, width=900, height=550, returned_objects=[])
        else:
            st.error("🚨 Gagal memuat data geospasial.")
