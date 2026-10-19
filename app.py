import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import re

st.set_page_config(page_title="Ultimate DSS Pariwisata Jogja", layout="wide", initial_sidebar_state="expanded")

# --- HEADER PRESENTASI ---
st.title("🏛️ Command Center Pariwisata & Tata Kota Yogyakarta")
st.markdown("*Platform Analitik Eksekutif: Ekonomi, SDM, dan Prediksi Kemacetan Lalu Lintas*")
st.divider()

st.sidebar.header("📁 Upload Dataset (Wajib 3 File)")
file_2024 = st.sidebar.file_uploader("1. Data Pengunjung (2024)", type=["xlsx"])
file_194 = st.sidebar.file_uploader("2. Data Sektoral (194.xlsx)", type=["xlsx"])
file_112 = st.sidebar.file_uploader("3. Data Prioritas (112.xlsx)", type=["xlsx"])

if file_2024 and file_194 and file_112:
    try:
        # --- BACA DATA ---
        df_2024 = pd.read_excel(file_2024, sheet_name=0)
        df_194 = pd.read_excel(file_194, sheet_name=0)
        df_112 = pd.read_excel(file_112, sheet_name=0)

        # --- FUNGSI EKSTRAKSI DATA ANTI-ERROR ---
        def get_194(keyword):
            val = df_194.loc[df_194['Nama Data'].str.contains(keyword, case=False, na=False, regex=True), 'Data 2025']
            return float(val.values[0]) if not val.empty else 0.0

        def get_112(keyword):
            val = df_112.loc[df_112['Nama Data'].str.contains(keyword, case=False, na=False, regex=True), 'Data 2025']
            if val.empty or val.values[0] == 'SIMONEVA': return 0.0
            v_str = str(val.values[0])
            v_clean = re.sub(r'[^\d,\.]', '', v_str).replace('.', '').replace(',', '.')
            return float(v_clean) if v_clean else 0.0

        # --- PEMROSESAN CORE DATA ---
        df_2024['Total'] = df_2024['Pengunjung Mancanegara'] + df_2024['Pengunjung Nusantara']
        df_2024['Luar Malioboro'] = df_2024['Total'] - df_2024['Malioboro']
        total_wisatawan_2024 = df_2024['Total'].sum()
        
        belanja_turis = get_112('Rata-Rata Belanja')
        los_aktual = get_112('Length of Stay')
        
        total_kamar = get_194('Jumlah Kamar Hotel Bintang') + get_194('Jumlah Kamar Hotel Non Bintang')
        kapasitas_kota_bulanan = total_kamar * 2 * 30 
        
        sdm_sertifikasi = get_194('tersertifikasi')
        pokdarwis = get_194('Jumlah Pokdarwis')
        kampung_wisata = get_194('Kampung Wisata')

        # --- PEMODELAN LALU LINTAS (TRAFFIC MODEL) ---
        df_2024['Est_Bus'] = (df_2024['Total'] * 0.30) / 40
        df_2024['Est_Mobil'] = (df_2024['Total'] * 0.50) / 4
        df_2024['Est_Motor'] = (df_2024['Total'] * 0.20) / 2
        df_2024['Total_Kendaraan'] = df_2024['Est_Bus'] + df_2024['Est_Mobil'] + df_2024['Est_Motor']
        
        kapasitas_jalan_maksimal = 150000 
        df_2024['Indeks_Kemacetan'] = (df_2024['Total_Kendaraan'] / kapasitas_jalan_maksimal) * 100

        # --- TABS PRESENTASI ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 1. Executive Summary", 
            "📈 2. Tourist Forecasting", 
            "💰 3. Economic Simulation", 
            "🚨 4. Infrastructure EWS",
            "🚦 5. Traffic Prediction"
        ])

        # ==========================================
        # TAB 1: EXECUTIVE SUMMARY
        # ==========================================
        with tab1:
            st.subheader("Ringkasan Kinerja Makro (Tahun Berjalan)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume Wisatawan", f"{total_wisatawan_2024/1e6:.2f} Juta")
            c2.metric("Estimasi Perputaran Uang", f"Rp {(total_wisatawan_2024 * belanja_turis)/1e12:.2f} T")
            c3.metric("Length of Stay (LoS)", f"{los_aktual} Hari")
            c4.metric("Total Kendaraan Wisata", f"{df_2024['Total_Kendaraan'].sum():,.0f} Unit")
            
            st.divider()
            st.markdown("#### Pemetaan Beban Spasial Tahunan: Malioboro vs Kampung Wisata")
            
            # Perbaikan Grafik Bubble (Hapus pembatas Y-axis agar otomatis menyesuaikan data)
            fig_spatial = go.Figure(data=[go.Scatter(
                x=['Kawasan Malioboro', 'Destinasi Lainnya (Kampung Wisata)'],
                y=[df_2024['Malioboro'].sum(), df_2024['Luar Malioboro'].sum()],
                mode='markers+text',
                marker=dict(size=[df_2024['Malioboro'].sum()/150000, df_2024['Luar Malioboro'].sum()/150000], color=['#e74c3c', '#2ecc71']),
                text=[f"{df_2024['Malioboro'].sum()/1e6:.1f} Juta Turis", f"{df_2024['Luar Malioboro'].sum()/1e6:.1f} Juta Turis"],
                textposition="bottom center"
            )])
            fig_spatial.update_layout(height=450, template="plotly_white") # Pembatas range Y dihapus di sini
            st.plotly_chart(fig_spatial, use_container_width=True)

        # ==========================================
        # TAB 2: TOURIST FORECASTING
        # ==========================================
        with tab2:
            st.subheader("Machine Learning: Prediksi Kedatangan Wisatawan")
            X = np
