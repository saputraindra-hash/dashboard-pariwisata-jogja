import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import requests
import networkx as nx
from shapely.geometry import Point
import json
import os
import numpy as np

# ==============================================================================
# KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(page_title="Command Center Gubernur DIY", layout="wide", page_icon="🏛️")

st.sidebar.title("🏛️ Command Center DIY")
st.sidebar.markdown("Decision Support System (DSS)")
menu = st.sidebar.radio("Navigasi Modul:", [
    "1. Kemiskinan & Ketimpangan",
    "2. Tata Ruang & Pangan",
    "3. Aglomerasi & Transportasi",
    "4. Mitigasi Pariwisata 3D",
    "5. Peta Evakuasi Regional",
    "6. Master Overlay & AI Keselamatan"
])

# ==============================================================================
# MENU 1 - 5 (KERANGKA PRESENTASI)
# ==============================================================================
if menu == "1. Kemiskinan & Ketimpangan":
    st.title("📊 Modul 1: Pengentasan Kemiskinan")
    st.info("Visualisasi Clustering Kapanewon Prioritas 1 untuk penyaluran Jaring Pengaman Sosial.")
    c1, c2 = st.columns(2)
    c1.metric("Gini Ratio Target", "0.380", "-0.015")
    c2.metric("Anggaran Efektif", "Rp 45 Miliar", "+12%")

elif menu == "2. Tata Ruang & Pangan":
    st.title("🌾 Modul 2: Ketahanan Pangan & Ekologi")
    moratorium = st.slider("Simulasi Moratorium Alih Fungsi Lahan (%)", 0, 100, 20)
    st.line_chart(np.random.randn(20, 2) * moratorium)

elif menu == "3. Aglomerasi & Transportasi":
    st.title("🛣️ Modul 3: V/C Ratio Jalan Provinsi")
    st.warning("Deteksi Gridlock pada kawasan aglomerasi perkotaan Yogyakarta.")

elif menu == "4. Mitigasi Pariwisata 3D":
    st.title("🌋 Modul 4: Mitigasi 3D (Web Scene)")
    st.info("Integrasi Topografi Elevasi untuk Evakuasi Tsunami dan Erupsi Merapi.")

elif menu == "5. Peta Evakuasi Regional":
    st.title("🗺️ Modul 5: Rencana Evakuasi Regional")
    st.success("Sistem pemetaan daya tampung barak pengungsian berbasis Geoportal.")

# ==============================================================================
# MENU 6: HYBRID AI & OSRM GLOBAL ROUTING API
# ==============================================================================
elif menu == "6. Master Overlay & AI Keselamatan":
    import json
    import os
    
    st.title("🚨 DSS: Keselamatan Wisata (AI Routing API)")
    st.markdown("Menggabungkan data internal Geoportal Pemda dengan **Global Routing API (OSRM)** untuk simulasi navigasi ambulans presisi tinggi hingga ke jalan desa.")
    
    radius_aman_km = st.slider("Batas Toleransi Jarak Faskes (Km):", 1.0, 20.0, 5.0, 0.5)
    batas_meter = radius_aman_km * 1000 
    
    @st.cache_data(ttl=3600)
    def fetch_api_gdf(url, geom_type="point", backup_file="backup.json"):
        try:
            res = requests.get(url, timeout=10).json()
            with open(backup_file, 'w') as f:
                json.dump(res, f)
        except:
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
                nama_ditemukan = "Tidak Bernama"
                for key, value in attr.items():
                    k = key.lower()
                    if any(x in k for x in ['nama', 'name', 'nm_', 'faskes', 'ppk', 'rs', 'puskesmas', 'dtw', 'wisata']):
                        if value and not any(x in k for x in ['kode', 'kd_', 'id']):
                            nama_ditemukan = str(value).strip()
                            break
                attr['nama_tampil'] = nama_ditemukan
                
            records.append(attr)
            
        df = pd.DataFrame(records)
        if geom_type == "point":
            df = df.dropna(subset=['Lat', 'Lon'])
            geometry = [Point(xy) for xy in zip(df['Lon'], df['Lat'])]
            return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326"), res
        return df, res

    with st.spinner("🔄 Memuat Geospasial Pemda (API / Offline Cache)..."):
        url_wisata = "https://geoportal.jogjaprov.go.id/server/rest/services/DISPAR/34_DISPAR_KUNJ_DTW_2023_PT/FeatureServer/0/query?outFields=*&where=1%3D1&outSR=4326&f=json"
        url_faskes = "https://geoportal.jogjaprov.go.id/server/rest/services/BPJS/_34_BPJS_FASKES_PT/FeatureServer/216/query?outFields=*&where=1%3D1&outSR=4326&f=json"
        
        wisata_gdf, _ = fetch_api_gdf(url_wisata, "point", "backup_wisata.json")
        faskes_gdf, _ = fetch_api_gdf(url_faskes, "point", "backup_faskes.json")
        
        # KITA TIDAK LAGI MENGUNDUH DATA JALAN PROVINSI YANG BERAT KARENA SUDAH PAKAI API OSRM

        if not wisata_gdf.empty and not faskes_gdf.empty:
            faskes_gdf = faskes_gdf.reset_index(drop=True)
            
            wisata_utm = wisata_gdf.to_crs("EPSG:32749")
            faskes_utm = faskes_gdf.to_crs("EPSG:32749")
            
            evaluasi = gpd.sjoin_nearest(wisata_utm, faskes_utm, how='left', distance_col='Jarak_Udara_Meter')
            evaluasi = evaluasi.to_crs("EPSG:4326")
            
            zona_aman = evaluasi[evaluasi['Jarak_Udara_Meter'] <= batas_meter]
            zona_bahaya = evaluasi[evaluasi['Jarak_Udara_Meter'] > batas_meter]

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Destinasi", len(evaluasi))
            c2.metric("🔵 Zona Aman (Udara)", len(zona_aman))
            c3.metric(f"🔴 Zona Bahaya (> {radius_aman_km} Km)", len(zona_bahaya), delta_color="inverse")

            st.markdown("### 🚑 Investigasi Rute Darurat dengan Global API")
            
            daftar_bahaya = zona_bahaya['nama_tampil_left'].tolist() if 'nama_tampil_left' in zona_bahaya.columns else zona_bahaya['nama_tampil'].tolist()
            
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                titik_investigasi = st.selectbox("Pilih Titik Wisata Rawan:", daftar_bahaya)
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True) 
                tombol_routing = st.button("🚨 Eksekusi API Routing", type="primary", use_container_width=True)

            m_master = folium.Map(location=[-7.90, 110.50], zoom_start=10, tiles='OpenStreetMap')

            for idx, row in zona_aman.iterrows():
                nama = row.get('nama_tampil_left', row.get('nama_tampil', 'Wisata'))
                folium.CircleMarker([row.geometry.y, row.geometry.x], radius=4, color="blue", fill=True, tooltip=f"AMAN: {nama}").add_to(m_master)

            for idx, row in zona_bahaya.iterrows():
                nama = row.get('nama_tampil_left', row.get('nama_tampil', 'Wisata'))
                folium.CircleMarker([row.geometry.y, row.geometry.x], radius=6, color="red", fill=True, tooltip=f"BAHAYA: {nama}").add_to(m_master)

            for idx, row in faskes_gdf.iterrows():
                folium.CircleMarker([row.geometry.y, row.geometry.x], radius=3, color="green", fill=True, tooltip=f"Faskes: {row['nama_tampil']}").add_to(m_master)

            # --- EKSEKUSI OSRM API SAAT TOMBOL DITEKAN ---
            if tombol_routing and titik_investigasi:
                kolom_nama = 'nama_tampil_left' if 'nama_tampil_left' in evaluasi.columns else 'nama_tampil'
                w_row = zona_bahaya[zona_bahaya[kolom_nama] == titik_investigasi].iloc[0]
                
                idx_faskes = w_row['index_right']
                f_row = faskes_gdf.loc[idx_faskes]
                
                # Koordinat Asal dan Tujuan
                lon1, lat1 = w_row.geometry.x, w_row.geometry.y
                lon2, lat2 = f_row.geometry.x, f_row.geometry.y
                
                # Memanggil API OSRM (Format: lon,lat;lon,lat)
                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
                
                try:
                    with st.spinner("🛰️ Menghubungkan ke Satelit Routing Global..."):
                        res_route = requests.get(osrm_url).json()
                        
                        if res_route.get("code") == "Ok":
                            rute_data = res_route["routes"][0]
                            jarak_km = rute_data["distance"] / 1000
                            durasi_menit = rute_data["duration"] / 60
                            koordinat_geojson = rute_data["geometry"]["coordinates"]
                            
                            # OSRM memberikan format [lon, lat], Folium butuh [lat, lon]
                            rute_latlon = [[coord[1], coord[0]] for coord in koordinat_geojson]
                            
                            st.warning(f"🚨 **Hasil Analisis Satelit:** Jarak jalan raya aslinya adalah **{jarak_km:.2f} Km**. Waktu tempuh darurat ambulans diperkirakan **{durasi_menit:.0f} Menit**.")
                            
                            folium.PolyLine(rute_latlon, color="#ff0000", weight=7, opacity=0.9).add_to(m_master)
                            m_master.fit_bounds(rute_latlon)
                        else:
                            st.error("⚠️ Gagal menemukan rute. Area mungkin terisolasi penuh.")
                except:
                    st.error("⚠️ Gagal terhubung ke API Routing Global.")

            st_folium(m_master, width=900, height=550, returned_objects=[])
            
        else:
            st.error("🚨 Gagal memuat data geospasial dari Pemda maupun Cache Offline.")
        else:
            st.error("🚨 Gagal memuat data geospasial dari API maupun Cache Offline.")
