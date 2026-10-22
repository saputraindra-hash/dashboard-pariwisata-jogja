import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import folium
from streamlit_folium import st_folium
import requests
import os

st.set_page_config(page_title="Command Center Gubernur DIY", layout="wide", initial_sidebar_state="expanded")

# --- NAVIGASI UTAMA ---
st.sidebar.title("🏛️ Menu Gubernur")
menu = st.sidebar.radio("Pilih Sektor Analisis Kebijakan:", [
    "1. Ketimpangan & Kemiskinan (Sosial)",
    "2. Tata Ruang & Pangan (Ekologi)",
    "3. Aglomerasi & Transportasi (Infrastruktur)",
    "4. Distribusi Pariwisata (API Geoportal)"
])
st.sidebar.divider()

def check_file(filename):
    if not os.path.exists(filename):
        st.error(f"⚠️ File '{filename}' tidak ditemukan di sistem. Pastikan Anda telah membuatnya di GitHub.")
        st.stop()

# ==============================================================================
# MENU 1: KETIMPANGAN EKONOMI & KEMISKINAN
# ==============================================================================
if menu == "1. Ketimpangan & Kemiskinan (Sosial)":
    st.title("⚖️ Analisis Pengentasan Kemiskinan & Gini Ratio DIY")
    st.markdown("Clustering K-Means untuk menentukan **Zona Prioritas Bantuan Sosial (Bansos)**.")
    
    check_file('kemiskinan_diy.csv')
    df_soc = pd.read_csv('kemiskinan_diy.csv')
    
    X_soc = df_soc[['Tingkat_Kemiskinan_Persen', 'Gini_Ratio']]
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_soc)
    df_soc['Cluster'] = kmeans.labels_
    
    cluster_centers = kmeans.cluster_centers_[:, 0]
    sorted_idx = np.argsort(cluster_centers)[::-1]
    label_map = {sorted_idx[0]: 'Prioritas 1 (Bansos Mendesak)', sorted_idx[1]: 'Prioritas 2 (Pemberdayaan)', sorted_idx[2]: 'Prioritas 3 (Mandiri)'}
    color_map = {'Prioritas 1 (Bansos Mendesak)': '#e74c3c', 'Prioritas 2 (Pemberdayaan)': '#f1c40f', 'Prioritas 3 (Mandiri)': '#2ecc71'}
    df_soc['Status_Prioritas'] = df_soc['Cluster'].map(label_map)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Kapanewon Prioritas 1 (Merah)", len(df_soc[df_soc['Status_Prioritas'] == 'Prioritas 1 (Bansos Mendesak)']))
    c2.metric("Rata-rata Gini Ratio (Ketimpangan)", f"{df_soc['Gini_Ratio'].mean():.2f}")
    c3.metric("Rata-rata Kemiskinan DIY", f"{df_soc['Tingkat_Kemiskinan_Persen'].mean():.1f}%")
    
    fig_soc = px.scatter(df_soc, x='Tingkat_Kemiskinan_Persen', y='Gini_Ratio', color='Status_Prioritas', 
                         color_discrete_map=color_map, size='Pengangguran_Persen', hover_name='Kapanewon',
                         title="Kuadran Ketimpangan vs Kemiskinan", size_max=20)
    fig_soc.update_layout(template="plotly_white", height=450)
    st.plotly_chart(fig_soc, use_container_width=True)

# ==============================================================================
# MENU 2: TATA RUANG & KETAHANAN PANGAN
# ==============================================================================
elif menu == "2. Tata Ruang & Pangan (Ekologi)":
    st.title("🌾 Command Center Tata Ruang & Ketahanan Pangan")
    st.markdown("Prediksi *Machine Learning* untuk mendeteksi krisis defisit beras akibat alih fungsi lahan.")
    
    check_file('pangan_diy.csv')
    df_pangan_raw = pd.read_csv('pangan_diy.csv')
    df_pangan = df_pangan_raw.groupby('Tahun').sum().reset_index()
    
    st.sidebar.header("🎛️ Simulasi Kebijakan Gubernur")
    moratorium_target = st.sidebar.slider("Rem Laju Alih Fungsi Lahan (%)", min_value=0, max_value=80, value=0, step=10)
    
    X_pangan = df_pangan[['Tahun']].values
    model_kons = LinearRegression().fit(X_pangan, df_pangan['Konsumsi_Beras_Ton'].values)
    model_prod = LinearRegression().fit(X_pangan, df_pangan['Produksi_Beras_Ton'].values)
    
    kemiringan_baru = model_prod.coef_[0] * (1 - (moratorium_target / 100))
    X_future = np.arange(2015, 2036).reshape(-1, 1)
    
    pred_kons = model_kons.predict(X_future)
    pred_prod_aktual = model_prod.predict(X_future)
    pred_prod_simulasi = (X_future.flatten() * kemiringan_baru) + (df_pangan['Produksi_Beras_Ton'].values[-1] - (kemiringan_baru * 2024))
    
    fig_pangan = go.Figure()
    fig_pangan.add_trace(go.Scatter(x=X_future.flatten(), y=pred_kons, mode='lines', name='Tren Konsumsi Beras (Naik)', line=dict(color='#e74c3c', width=3)))
    fig_pangan.add_trace(go.Scatter(x=X_future.flatten(), y=pred_prod_aktual, mode='lines', name='Prediksi Produksi Aktual (Turun)', line=dict(color='#7f8c8d', dash='dot', width=3)))
    
    if moratorium_target > 0:
         fig_pangan.add_trace(go.Scatter(x=X_future.flatten(), y=pred_prod_simulasi, mode='lines', name=f'Produksi Jika Moratorium {moratorium_target}%', line=dict(color='#2ecc71', width=4)))
    
    fig_pangan.update_layout(height=450, template="plotly_white", title="Proyeksi Persilangan Krisis Pangan DIY (2015-2035)")
    st.plotly_chart(fig_pangan, use_container_width=True)

# ==============================================================================
# MENU 3: AGLOMERASI & TRANSPORTASI
# ==============================================================================
elif menu == "3. Aglomerasi & Transportasi (Infrastruktur)":
    st.title("🚦 Manajemen Transportasi Aglomerasi Yogyakarta")
    st.markdown("Analisis Spasial titik temu kemacetan (Bottleneck) kawasan Aglomerasi menggunakan *Geospatial Mapping*.")
    
    check_file('transport_diy.csv')
    df_trans = pd.read_csv('transport_diy.csv')
    df_trans['VC_Ratio'] = df_trans['Volume_Harian'] / df_trans['Kapasitas_Kendaraan']
    
    def status_kemacetan(vc):
        if vc > 1.0: return 'Gridlock (Lumpuh)'
        elif vc > 0.8: return 'Padat Merayap'
        else: return 'Lancar'
        
    df_trans['Status'] = df_trans['VC_Ratio'].apply(status_kemacetan)
    
    c1, c2 = st.columns(2)
    c1.metric("Titik Gridlock (V/C Ratio > 1.0)", len(df_trans[df_trans['Status'] == 'Gridlock (Lumpuh)']))
    c2.metric("Rata-rata Volume Arteri", f"{df_trans['Volume_Harian'].mean():,.0f} Kendaraan/Hari")
    
    st.markdown("### 🗺️ Peta Interaktif V/C Ratio Jalan Arteri DIY")
    m = folium.Map(location=[-7.7829, 110.3670], zoom_start=12, tiles='OpenStreetMap')
    
    for i, row in df_trans.iterrows():
        warna = '#e74c3c' if row['Status'] == 'Gridlock (Lumpuh)' else ('#f39c12' if row['Status'] == 'Padat Merayap' else '#2ecc71')
        html_tooltip = f"<div style='font-family: Arial; font-size: 12px;'><b>{row['Simpang_Jalan']}</b><br>V/C Ratio: {row['VC_Ratio']:.2f}</div>"
        
        folium.CircleMarker(
            location=[row['Lat'], row['Lon']],
            radius=row['Volume_Harian'] / 4000, 
            color=warna, fill=True, fill_color=warna, fill_opacity=0.7, tooltip=html_tooltip
        ).add_to(m)
        
    st_folium(m, width=900, height=500, returned_objects=[])

# ==============================================================================
# MENU 4: PARIWISATA & DISTRIBUSI (API GEOPORTAL JOGJAPROV)
# ==============================================================================
elif menu == "4. Distribusi Pariwisata (API Geoportal)":
    st.title("🗺️ Peta Kunjungan Daya Tarik Wisata (DTW)")
    st.markdown("🌐 *Menarik data secara **Real-Time** dari API Geoportal Pemerintah Daerah Istimewa Yogyakarta.*")
    
    # URL API dengan parameter outSR=4326 agar output berformat Latitude/Longitude standar
    api_url = "https://geoportal.jogjaprov.go.id/server/rest/services/DISPAR/34_DISPAR_KUNJ_DTW_2023_PT/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    
    with st.spinner("🔄 Sedang mengunduh data spasial dari server Geoportal Pemda DIY..."):
        try:
            response = requests.get(api_url, timeout=15)
            data = response.json()
            
            if 'features' in data:
                records = []
                for f in data['features']:
                    attr = f.get('attributes', {})
                    geom = f.get('geometry', {})
                    # Ekstraksi Koordinat
                    if geom:
                        attr['Lon'] = geom.get('x')
                        attr['Lat'] = geom.get('y')
                    records.append(attr)
                
                df_api = pd.DataFrame(records)
                
                # Filter data yang memiliki koordinat valid
                df_map = df_api.dropna(subset=['Lat', 'Lon'])
                
                c_api1, c_api2 = st.columns(2)
                c_api1.metric("Total Destinasi Wisata Ditemukan", len(df_map))
                c_api2.success("Koneksi API Geoportal: Terhubung (200 OK)")
                
                # Render Peta Interaktif
                st.markdown("### 📍 Persebaran Spasial Destinasi Wisata")
                m_wisata = folium.Map(location=[-7.80, 110.40], zoom_start=10, tiles='OpenStreetMap')
                
                for idx, row in df_map.iterrows():
                    # Membuat teks pop-up dinamis yang merangkum semua atribut data yang dikirim API
                    info_teks = "".join([f"<b>{k}</b>: {v}<br>" for k, v in row.to_dict().items() if k not in ['Lat', 'Lon', 'OBJECTID', 'Shape'] and pd.notna(v)])
                    
                    folium.Marker(
                        location=[row['Lat'], row['Lon']],
                        icon=folium.Icon(color='blue', icon='info-sign'),
                        tooltip=f"<div style='font-size:11px; max-width: 250px;'>{info_teks}</div>"
                    ).add_to(m_wisata)
                
                st_folium(m_wisata, width=900, height=500, returned_objects=[])
                
                # Tampilkan Raw Data 
                st.markdown("### 🗄️ Raw Data dari Database Geoportal")
                st.dataframe(df_api, use_container_width=True)
                
                st.info("""
                🎙️ **Panduan Presentasi Gubernur (Skenario Pariwisata Live):**  
                *"Sebagai penutup, kami mendemonstrasikan kapabilitas 'Live Integration'. Layar ini tidak membaca file Excel, melainkan menyedot data langsung secara *real-time* dari server Geoportal Pemda DIY. Saat kita arahkan kursor ke pin biru di atas peta, seluruh metrik kunjungan Daya Tarik Wisata otomatis ditampilkan. Ini membuktikan bahwa Command Center kita sudah siap terintegrasi ke dalam ekosistem Big Data provinsi secara utuh."*
                """)
                
            else:
                st.error("Gagal membaca struktur data (features) dari API Geoportal.")
                
        except Exception as e:
            st.error(f"Koneksi ke API gagal. Server Geoportal mungkin sedang down atau sibuk. Error: {e}")
