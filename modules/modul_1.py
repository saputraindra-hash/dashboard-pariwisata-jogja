import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import streamlit.components.v1 as components
import requests
from shapely.geometry import Point, Polygon

def Tampilkan():
    st.title("🚨 DSS: Keselamatan Wisata & Mitigasi Terpadu")
    st.markdown("Pusat Komando Analisis **Double-Hazard**: Integrasi Navigasi Medis, Keamanan, dan Mitigasi Kawasan Rawan Bencana (KRB).")
    
    col_slider1, col_slider2 = st.columns(2)
    with col_slider1:
        radius_medis = st.slider("Batas Aman Jarak Faskes (Km):", 1.0, 30.0, 10.0, 1.0)
    with col_slider2:
        radius_polisi = st.slider("Batas Aman Jarak Polisi (Km):", 1.0, 30.0, 15.0, 1.0)
        
    batas_medis_m = radius_medis * 1000 
    batas_polisi_m = radius_polisi * 1000 
    
    # ==========================================
    # DATA SIMULASI (MENGATASI API KEY ERROR)
    # ==========================================
    @st.cache_data
    def get_mock_wisata():
        df = pd.DataFrame({
            'nama_tampil': ['Candi Prambanan', 'Pantai Parangtritis', 'Kawasan Kaliurang', 'Jalan Malioboro', 'Tebing Breksi', 'Pantai Baron (Gunungkidul)'],
            'Lat': [-7.7520, -8.0250, -7.6000, -7.7920, -7.7810, -8.1280],
            'Lon': [110.4910, 110.3250, 110.4240, 110.3650, 110.5040, 110.5480]
        })
        return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['Lon'], df['Lat'])], crs="EPSG:4326")

    @st.cache_data
    def get_mock_faskes():
        df = pd.DataFrame({
            'nama_tampil': ['RSUP Dr. Sardjito', 'RSUD Panembahan Senopati', 'RSUD Wonosari', 'Puskesmas Pakem', 'Puskesmas Kretek'],
            'Lat': [-7.7680, -7.8870, -7.9680, -7.6670, -7.9860],
            'Lon': [110.3730, 110.3330, 110.6050, 110.4200, 110.3200]
        })
        return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['Lon'], df['Lat'])], crs="EPSG:4326")

    @st.cache_data
    def get_mock_polisi():
        df = pd.DataFrame({
            'nama_tampil': ['Polresta Yogyakarta', 'Polres Sleman', 'Polres Bantul', 'Polres Gunungkidul'],
            'Lat': [-7.8030, -7.7100, -7.8850, -7.9640],
            'Lon': [110.3640, 110.3340, 110.3300, 110.6020]
        })
        return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['Lon'], df['Lat'])], crs="EPSG:4326")

    @st.cache_data
    def get_mock_krb():
        # Radius Bencana Merapi & Poligon Tsunami Selatan
        merapi = Point(110.446, -7.540).buffer(0.08) 
        tsunami = Polygon([(110.0, -8.20), (110.8, -8.20), (110.8, -7.95), (110.0, -7.95)])
        return gpd.GeoDataFrame({'nama_tampil': ['KRB III Gunung Merapi', 'Zona Rawan Tsunami Selatan']}, geometry=[merapi, tsunami], crs="EPSG:4326")

    def get_osrm_route(lon1, lat1, lon2, lat2):
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get("code") == "Ok":
                r = res["routes"][0]
                return r["distance"]/1000, r["duration"]/60, [[c[1], c[0]] for c in r["geometry"]["coordinates"]]
        except Exception: 
            pass
        return None, None, None

    with st.spinner("🔄 Memuat Ekosistem Geospasial..."):
        wisata_gdf = get_mock_wisata()
        faskes_gdf = get_mock_faskes()
        polisi_gdf = get_mock_polisi()
        krb_gdf = get_mock_krb()
        
        wisata_utm = wisata_gdf.to_crs("EPSG:32749")
        faskes_utm = faskes_gdf.to_crs("EPSG:32749")
        polisi_utm = polisi_gdf.to_crs("EPSG:32749")
        krb_utm = krb_gdf.to_crs("EPSG:32749")
        
        join_faskes = gpd.sjoin_nearest(wisata_utm, faskes_utm, how='left', distance_col='Jarak_Faskes')
        join_polisi = gpd.sjoin_nearest(wisata_utm, polisi_utm, how='left', distance_col='Jarak_Polisi')
        join_krb = gpd.sjoin(wisata_utm, krb_utm, how='left', predicate='intersects')
        
        evaluasi = wisata_gdf.copy()
        evaluasi['Nama_Wisata'] = join_faskes['nama_tampil_left']
        evaluasi['Idx_Faskes'] = join_faskes['index_right']
        evaluasi['Jarak_Faskes'] = join_faskes['Jarak_Faskes']
        evaluasi['Idx_Polisi'] = join_polisi['index_right']
        evaluasi['Jarak_Polisi'] = join_polisi['Jarak_Polisi']
        
        evaluasi['Zona_Bencana'] = join_krb['nama_tampil_right'].fillna("Aman")
        evaluasi['In_KRB'] = evaluasi['Zona_Bencana'] != "Aman"
        
        rawan_medis = evaluasi['Jarak_Faskes'] > batas_medis_m
        rawan_polisi = evaluasi['Jarak_Polisi'] > batas_polisi_m
        
        evaluasi['Status'] = "🔵 Aman"
        evaluasi.loc[rawan_medis | rawan_polisi | evaluasi['In_KRB'], 'Status'] = "🟠 Rawan (Single Hazard)"
        evaluasi.loc[(rawan_medis | rawan_polisi) & evaluasi['In_KRB'], 'Status'] = "🔴 Bahaya Ganda (Double Hazard)"

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Destinasi Wisata", len(evaluasi))
        c2.metric("🏥 Rawan Medis", len(evaluasi[rawan_medis]))
        c3.metric("🚓 Rawan Keamanan", len(evaluasi[rawan_polisi]))
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
        st.markdown("### 🛰️ Sistem Navigasi Respons Cepat (112 & 119)")
        
        df_pilihan = evaluasi[evaluasi['Status'] != "🔵 Aman"]
        daftar_investigasi = df_pilihan['Nama_Wisata'].tolist()
        
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            titik_investigasi = st.selectbox("Pilih Titik Darurat untuk Simulasi Navigasi:", daftar_investigasi)
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True) 
            tombol_routing = st.button("🚨 Kerahkan Bantuan", type="primary", use_container_width=True)

        m_master = folium.Map(location=[-7.90, 110.45], zoom_start=10, tiles='CartoDB positron')

        folium.GeoJson(
            krb_gdf, 
            style_function=lambda x: {'fillColor': '#ff0000', 'color': '#ff0000', 'weight': 1, 'fillOpacity': 0.15},
            tooltip=folium.GeoJsonTooltip(fields=['nama_tampil'], aliases=['Zona Bencana:'])
        ).add_to(m_master)

        for _, r in polisi_gdf.iterrows():
            folium.Marker([r.geometry.y, r.geometry.x], tooltip=f"🚓 {r['nama_tampil']}", icon=folium.Icon(color='darkblue', icon='shield')).add_to(m_master)
        for _, r in faskes_gdf.iterrows():
            folium.CircleMarker([r.geometry.y, r.geometry.x], radius=4, color="green", fill=True, tooltip=f"🏥 {r['nama_tampil']}").add_to(m_master)

        for _, r in evaluasi.iterrows():
            warna = "blue" if r['Status'] == "🔵 Aman" else ("orange" if "Single" in r['Status'] else "red")
            rad = 4 if warna == "blue" else 7
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

        components.html(m_master._repr_html_(), height=600)
