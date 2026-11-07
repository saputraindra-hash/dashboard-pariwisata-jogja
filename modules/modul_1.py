import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import streamlit.components.v1 as components # Menggunakan komponen native Streamlit
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
        df = pd.DataFrame({
            'nama_tampil': ['Polresta Yogyakarta', 'Polres Sleman', 'Polres Bantul', 'Polres Gunungkidul', 'Polres Kulon Progo', 'Polsek Depok Timur'],
            'Lat': [-7.803, -7.710, -7.885, -7.964, -7.860, -7.755],
            'Lon': [110.364, 110.334, 110.330, 110.602, 110.155, 110.405]
        })
        return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df['Lon'], df['Lat'])], crs="EPSG:4326")

    def get_mock_krb():
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
            
            join_faskes = gpd.sjoin_nearest(wisata_utm, faskes_utm, how='left', distance_col='Jarak_Faskes')
            join_polisi = gpd.sjoin_nearest(wisata_utm, polisi_utm, how='left', distance_col='Jarak_Polisi')
            join_krb = gpd.sjoin(wisata_utm, krb_utm, how='left', predicate='intersects')
            
            evaluasi = wisata_gdf.copy()
            nama_col = 'nama_tampil_left' if 'nama_tampil_left' in join_faskes.columns else 'nama_tampil'
            evaluasi['Nama_Wisata'] = join_faskes[nama_col]
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
            c2.metric("🏥 Rawan Akses Medis", len(evaluasi[rawan_medis]))
            c3.metric("🚓 Rawan Akses Keamanan", len(evaluasi[rawan_polisi]))
            c4.metric("🌋 Masuk Zona Bencana", len(evaluasi[evaluasi['In_KRB']]))
            
            st.markdown("### 📊 Analisis Double-Hazard (Kawasan Paling Berisiko)")
            st.warning("Menampilkan destinasi yang berada di dalam **Kawasan Rawan Bencana (Merapi/Tsunami)** sekaligus memiliki jarak yang jauh dari intervensi Medis & Polisi.")
            
            df_bahaya = evaluasi[evaluasi['Status'] == "🔴 Bahaya Ganda (Double Hazard)"].copy()
            if not df_bahaya.empty:
                df_tabel = df_bahaya[['Nama_Wisata', 'Zona_Bencana', 'Jarak_Faskes', 'Jarak_Polisi']].copy()
                df_tabel['Jarak Faskes (Km)'] = (df_tabel['Jarak_Faskes'] / 1000).round(1)
                df_tabel['Jarak Polisi (Km)'] = (df_t
