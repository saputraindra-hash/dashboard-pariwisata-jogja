import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import os

st.set_page_config(page_title="Command Center Gubernur DIY", layout="wide", initial_sidebar_state="expanded")

# --- NAVIGASI UTAMA ---
st.sidebar.title("🏛️ Menu Gubernur")
menu = st.sidebar.radio("Pilih Sektor Analisis Kebijakan:", [
    "1. Ketimpangan & Kemiskinan (Sosial)",
    "2. Tata Ruang & Pangan (Ekologi)",
    "3. Aglomerasi & Transportasi (Infrastruktur)"
])
st.sidebar.divider()

# Fungsi untuk mengecek keberadaan file
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
    fig_soc.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig_soc, use_container_width=True)
    
    st.dataframe(df_soc[['Kapanewon', 'Kabupaten', 'Tingkat_Kemiskinan_Persen', 'Gini_Ratio', 'Status_Prioritas']].sort_values(by='Tingkat_Kemiskinan_Persen', ascending=False), use_container_width=True)

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
    
    fig_pangan.update_layout(height=500, template="plotly_white", title="Proyeksi Persilangan Krisis Pangan DIY (2015-2035)")
    st.plotly_chart(fig_pangan, use_container_width=True)

# ==============================================================================
# MENU 3: AGLOMERASI & TRANSPORTASI
# ==============================================================================
elif menu == "3. Aglomerasi & Transportasi (Infrastruktur)":
    st.title("🚦 Manajemen Transportasi Aglomerasi Yogyakarta")
    st.markdown("Pemetaan titik kemacetan (Bottleneck) dan kalkulasi *Volume-to-Capacity (V/C) Ratio*.")
    
    check_file('transport_diy.csv')
    df_trans = pd.read_csv('transport_diy.csv')
    df_trans['VC_Ratio'] = df_trans['Volume_Harian'] / df_trans['Kapasitas_Kendaraan']
    
    def status_kemacetan(vc):
        if vc > 1.0: return 'Gridlock (Lumpuh)'
        elif vc > 0.8: return 'Padat Merayap'
        else: return 'Lancar'
        
    df_trans['Status'] = df_trans['VC_Ratio'].apply(status_kemacetan)
    color_trans_map = {'Gridlock (Lumpuh)': '#e74c3c', 'Padat Merayap': '#f1c40f', 'Lancar': '#2ecc71'}
    
    c1, c2 = st.columns(2)
    c1.metric("Titik Gridlock (V/C Ratio > 1.0)", len(df_trans[df_trans['Status'] == 'Gridlock (Lumpuh)']))
    c2.metric("Rata-rata Volume Arteri", f"{df_trans['Volume_Harian'].mean():,.0f} Kendaraan/Hari")
    
    fig_trans = px.scatter(df_trans, x='Simpang_Jalan', y='VC_Ratio', size='Volume_Harian', color='Status',
                           color_discrete_map=color_trans_map, hover_name='Wilayah', size_max=40,
                           title="Peta Beban Kemacetan (Volume-to-Capacity Ratio) Kawasan Aglomerasi")
    fig_trans.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Batas Maksimal Kapasitas Jalan (V/C = 1.0)")
    fig_trans.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig_trans, use_container_width=True)
    
    st.dataframe(df_trans[['Simpang_Jalan', 'Wilayah', 'Volume_Harian', 'VC_Ratio', 'Status']].sort_values(by='VC_Ratio', ascending=False), use_container_width=True)
