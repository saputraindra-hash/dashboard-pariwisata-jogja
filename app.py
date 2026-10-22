import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import requests
import geopandas as gpd
from shapely.geometry import Point
import os

st.set_page_config(page_title="Command Center Gubernur DIY", layout="wide", initial_sidebar_state="expanded")

# --- NAVIGASI UTAMA ---
st.sidebar.title("🏛️ Menu Gubernur")
menu = st.sidebar.radio("Pilih Sektor Analisis Kebijakan:", [
    "1. Ketimpangan & Kemiskinan (Sosial)",
    "2. Tata Ruang & Pangan (Ekologi)",
    "3. Aglomerasi & Transportasi (Infrastruktur)",
    "4. Distribusi Pariwisata (API Geoportal)",
    "5. Peta 3D Topografi & Tata Ruang",
    "6. Master Overlay & AI Keselamatan"
])
st.sidebar.divider()

def check_file(filename):
    if not os.path.exists(filename):
        st.error(f"⚠️ File '{filename}' tidak ditemukan. Pastikan file dummy/CSV sudah ada di repositori.")
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
    c1.metric("Kapanewon Prioritas 1", len(df_soc[df_soc['Status_Prioritas'] == 'Prioritas 1 (Bansos Mendesak)']))
    c2.metric("Rata-rata Gini Ratio", f"{df_soc['Gini_Ratio'].mean():.2f}")
    c3.metric("Rata-rata Kemiskinan DIY", f"{df_soc['Tingkat_Kemiskinan_Persen'].mean():.1f}%")
    
    fig_soc = px.scatter(df_soc, x='Tingkat_Kemiskinan_Persen', y='Gini_Ratio', color='Status_Prioritas', 
                         color_discrete_map=color_map, size='Pengangguran_Persen', hover_name='Kapanewon',
                         title="Kuadran Ketimpangan vs Kemiskinan", size_max=20)
    fig_soc.update_layout(template="plotly_white", height=450)
    st.plotly_chart(fig_soc, use_container_width=True)
    
    st.info("🎙️ **Panduan:** Fokuskan Bansos eksklusif ke wilayah merah (Prioritas 1) agar Gini Ratio turun.")

# ==============================================================================
# MENU 2: TATA RUANG & KETAHANAN PANGAN
# ==============================================================================
elif menu == "2. Tata Ruang & Pangan (Ekologi)":
    st.title("🌾 Command Center Tata Ruang & Ketahanan Pangan")
    st.markdown("Prediksi *Machine Learning* untuk mendeteksi krisis defisit beras.")
    
    check_file('pangan_diy.csv')
    df_pangan = pd.read_csv('pangan_diy.csv').groupby('Tahun').sum().reset_index()
    
    st.sidebar.header("🎛️ Simulasi Kebijakan")
    moratorium = st.sidebar.slider("Rem Laju Alih Fungsi Lahan (%)", 0, 80, 0, 10)
    
    X_pangan = df_pangan[['Tahun']].values
    model_kons = LinearRegression().fit(X_pangan, df_pangan['Konsumsi_Beras_Ton'].values)
    model_prod = LinearRegression().fit(X_pangan, df_pangan['Produksi_Beras_Ton'].values)
    
    kemiringan_baru = model_prod.coef_[0] * (1 - (moratorium / 100))
    X_future = np.arange(2015, 2036).reshape(-1, 1)
    
    pred_kons = model_kons.predict(X_future)
    pred_prod_aktual = model_prod.predict(X_future)
    pred_prod_simulasi = (X_future.flatten() * kemiringan_baru) + (df_pangan['Produksi_Beras_Ton'].values[-1] - (kemiringan_baru * 2024))
    
    fig_pangan = go.Figure()
    fig_pangan.add_trace(go.Scatter(x=X_future.flatten(), y=pred_kons, mode='lines', name='Konsumsi Beras', line=dict(color='#e74c3c', width=3)))
    fig_pangan.add_trace(go.Scatter(x=X_future.flatten(), y=pred_prod_aktual, mode='lines', name='Produksi Aktual', line=dict(color='#7f8c8d', dash='dot', width=3)))
    
    if moratorium > 0:
         fig_pangan.add_trace(go.Scatter(x=X_future.flatten(), y=pred_prod_simulasi, mode='lines', name=f'Produksi (Moratorium {moratorium}%)', line=dict(color='#2ecc71', width=4)))
    
    fig_pangan.update_layout(height=450, template="plotly_white", title="Proyeksi Persilangan Krisis Pangan DIY")
    st.plotly_chart(fig_pangan, use_container_width=True)

# ==============================================================================
# MENU 3: AGLOMERASI & TRANSPORTASI
# ==============================================================================
elif menu == "3. Aglomerasi & Transportasi (Infrastruktur)":
    st.title("🚦 Manajemen Transportasi Aglomerasi Yogyakarta")
    
    check_file('transport_diy.csv')
    df_trans = pd.read_csv('transport_diy.csv')
    df_trans['VC_Ratio'] = df_trans['Volume_Harian'] / df_trans['Kapasitas_Kendaraan']
    df_trans['Status'] = df_trans['VC_Ratio'].apply(lambda x: 'Gridlock' if x > 1.0 else ('Padat' if x > 0.8 else 'Lancar'))
    
    c1, c2 = st.columns(2)
    c1.metric("Titik Gridlock", len(df_trans[df_trans['Status'] == 'Gridlock']))
    
    m = folium.Map(location=[-7.7829, 110.3670], zoom_start=12, tiles='OpenStreetMap')
    for i, row in df_trans.iterrows():
        warna = '#e74c3c' if row['Status'] == 'Gridlock' else ('#f39c12' if row['Status'] == 'Padat' else '#2ecc71')
        folium.CircleMarker([row['Lat'], row['Lon']], radius=row['Volume_Harian']/4000, color=warna, fill=True, fill_color=warna, fill_opacity=0.7, tooltip=f"V/C Ratio: {row['VC_Ratio']:.2f}").add_to(m)
        
    st_folium(m, width=900, height=500, returned_objects=[])

# ==============================================================================
# MENU 4: PARIWISATA & DISTRIBUSI (API + CLUSTERING)
# ==============================================================================
elif menu == "4. Distribusi Pariwisata (API Geoportal)":
    st.title("🗺️ Evaluasi Kawasan Strategis Pariwisata (KSP)")
    api_url = "https://geoportal.jogjaprov.go.id/server/rest/services/DISPAR/34_DISPAR_KUNJ_DTW_2023_PT/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    
    with st.spinner("🔄 Sedang memproses algoritma evaluasi spasial..."):
        try:
            response = requests.get(api_url, timeout=15).json()
            records = [{'Lon': f['geometry'].get('x'), 'Lat': f['geometry'].get('y'), **f['attributes']} for f in response.get('features', []) if f.get('geometry')]
            df_map = pd.DataFrame(records).dropna(subset=['Lat', 'Lon'])
            
            kmeans_spatial = KMeans(n_clusters=3, random_state=42, n_init=10)
            df_map['Kawasan_Cluster'] = kmeans_spatial.fit_predict(df_map[['Lat', 'Lon']])
            cluster_colors = {0: '#e74c3c', 1: '#3498db', 2: '#f1c40f'}
            
            m_wisata = folium.Map(location=[-7.80, 110.40], zoom_start=10, tiles='OpenStreetMap')
            for idx, row in df_map.iterrows():
                folium.CircleMarker([row['Lat'], row['Lon']], radius=6, color=cluster_colors[row['Kawasan_Cluster']], fill=True, fill_color=cluster_colors[row['Kawasan_Cluster']], fill_opacity=0.9).add_to(m_wisata)
            
            st_folium(m_wisata, width=900, height=500, returned_objects=[])
        except Exception as e:
            st.error(f"Gagal memuat API: {e}")

# ==============================================================================
# MENU 5: PETA 3D GEOPORTAL (IFRAME)
# ==============================================================================
elif menu == "5. Peta 3D Topografi & Tata Ruang":
    st.title("🌍 Analisis Topografi & Tata Ruang 3D")
    url_3d = "https://geoportal.jogjaprov.go.id/portal/home/webscene/viewer.html?layers=9e6ed007c45844178ac40d591ce611b8&viewpoint=cam:110.38658731,-7.88794756,149559.231;0,0.489"
    with st.spinner("Memuat ruang 3D..."):
        components.iframe(url_3d, height=650, scrolling=True)
# ==============================================================================
# MENU 6: AI KESELAMATAN BERBASIS JARINGAN JALAN (DIJKSTRA)
# ==============================================================================
elif menu == "6. Master Overlay & AI Keselamatan":
    import networkx as nx
    import itertools
    
    st.title("🚨 DSS: Keselamatan Wisata Berbasis Jaringan Jalan")
    st.markdown("Algoritma **Dijkstra Shortest Path** menghitung jarak tempuh aktual menyusuri **API Jalan Provinsi**.")
    
    radius_aman_km = st.slider("Tentukan Batas Jarak Aman Faskes (Kilometer):", 1.0, 30.0, 10.0, 1.0)
    batas_meter = radius_aman_km * 1000 
    
    @st.cache_data(ttl=3600)
    def fetch_api_gdf(url, geom_type="point"):
        try:
            res = requests.get(url, timeout=15).json()
            if 'features' not in res: return gpd.GeoDataFrame(), res
            
            records = []
            for f in res['features']:
                geom = f.get('geometry')
                if not geom: continue
                attr = f.get('attributes', {})
                if geom_type == "point":
                    attr['Lon'], attr['Lat'] = geom.get('x'), geom.get('y')
                records.append(attr)
                
            df = pd.DataFrame(records)
            if geom_type == "point":
                df = df.dropna(subset=['Lat', 'Lon'])
                geometry = [Point(xy) for xy in zip(df['Lon'], df['Lat'])]
                return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326"), res
            
            # Khusus untuk garis jalan (LineString disederhanakan untuk NetworkX)
            return df, res
        except:
            return gpd.GeoDataFrame(), {}

    with st.spinner("🔄 Membangun Jaringan Graf Jalan & Menjalankan Algoritma Dijkstra..."):
        url_wisata = "https://geoportal.jogjaprov.go.id/server/rest/services/DISPAR/34_DISPAR_KUNJ_DTW_2023_PT/FeatureServer/0/query?outFields=*&where=1%3D1&outSR=4326&f=json"
        url_faskes = "https://geoportal.jogjaprov.go.id/server/rest/services/BPJS/_34_BPJS_FASKES_PT/FeatureServer/216/query?outFields=*&where=1%3D1&outSR=4326&f=json"
        url_jalan = "https://geoportal.jogjaprov.go.id/server/rest/services/DPUPESDM/34_DPUPESDM_JALANPROVINSI_2024_LN/FeatureServer/0/query?outFields=*&where=1%3D1&outSR=4326&f=json"

        wisata_gdf, _ = fetch_api_gdf(url_wisata, "point")
        faskes_gdf, _ = fetch_api_gdf(url_faskes, "point")
        _, raw_jalan = fetch_api_gdf(url_jalan, "line")

        # 1. MEMBANGUN GRAPH JARINGAN JALAN DARI DATA MENTAH JSON
        G = nx.Graph()
        
        if 'features' in raw_jalan:
            for f in raw_jalan['features']:
                if 'geometry' in f and 'paths' in f['geometry']:
                    for path in f['geometry']['paths']:
                        # Menghubungkan setiap pasang titik dalam satu ruas jalan
                        for i in range(len(path)-1):
                            p1 = (path[i][0], path[i][1])
                            p2 = (path[i+1][0], path[i+1][1])
                            # Jarak euklidean sementara antar simpul sebagai bobot sisi (edge weight)
                            jarak_simpul = Point(p1).distance(Point(p2)) * 111000 # Asumsi 1 derajat ~ 111 km
                            G.add_edge(p1, p2, weight=jarak_simpul)

        # 2. ALGORITMA DIJKSTRA UNTUK SEMUA WISATA KE SEMUA FASKES
        # Catatan: Karena iterasi ini bisa berat, kita ambil contoh 50 wisata pertama untuk kecepatan presentasi
        wisata_sample = wisata_gdf.head(50)
        
        def cari_simpul_terdekat(graph, titik):
            # Mencari persimpangan jalan terdekat dari titik wisata/faskes (Snapping)
            nodes = list(graph.nodes)
            return min(nodes, key=lambda n: Point(n).distance(titik)) if nodes else None

        hasil_evaluasi = []
        for idx, wisata in wisata_sample.iterrows():
            titik_w = Point(wisata['Lon'], wisata['Lat'])
            simpul_w = cari_simpul_terdekat(G, titik_w)
            
            jarak_terpendek = float('inf')
            
            if simpul_w:
                for jdx, faskes in faskes_gdf.iterrows():
                    titik_f = Point(faskes['Lon'], faskes['Lat'])
                    simpul_f = cari_simpul_terdekat(G, titik_f)
                    
                    if simpul_f and nx.has_path(G, simpul_w, simpul_f):
                        # Eksekusi Algoritma Dijkstra
                        jarak = nx.shortest_path_length(G, source=simpul_w, target=simpul_f, weight='weight')
                        if jarak < jarak_terpendek:
                            jarak_terpendek = jarak
            
            hasil_evaluasi.append(jarak_terpendek)
            
        wisata_sample['Jarak_Jalan_Meter'] = hasil_evaluasi
        
        # 3. FILTER & VISUALISASI
        blank_spots = wisata_sample[wisata_sample['Jarak_Jalan_Meter'] > batas_meter]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Simpul Jalan (Nodes)", len(G.nodes))
        c2.metric("Titik Wisata Dievaluasi", len(wisata_sample))
        c3.metric(f"🚨 Blank Spot Jalan (> {radius_aman_km} Km)", len(blank_spots), delta_color="inverse")

        m_master = folium.Map(location=[-7.90, 110.50], zoom_start=10, tiles='OpenStreetMap')

        # Visualisasi Titik Rawan
        for idx, row in wisata_sample.iterrows():
            jarak_km = row['Jarak_Jalan_Meter'] / 1000
            if jarak_km == float('inf'): continue # Terisolasi / tidak ada jalan
            
            warna = "red" if jarak_km > radius_aman_km else "blue"
            radius_lingkaran = 8 if jarak_km > radius_aman_km else 4
            status_teks = "RAWAN" if jarak_km > radius_aman_km else "AMAN"
            
            nama_dtw = row.get('nama', 'Destinasi Wisata')
            tooltip = f"<b>{nama_dtw}</b><br>Rute Jalan ke Faskes: {jarak_km:.2f} Km<br>Status: {status_teks}"
            
            folium.CircleMarker(
                [row.geometry.y, row.geometry.x], radius=radius_lingkaran, color=warna, fill=True, fill_opacity=0.8, tooltip=tooltip
            ).add_to(m_master)

        st_folium(m_master, width=900, height=550, returned_objects=[])
            st.error("Gagal menarik data dari server Geoportal untuk menjalankan analisis.")
