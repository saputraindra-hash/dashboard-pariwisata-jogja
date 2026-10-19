import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        # Asumsi Proporsi Kendaraan: Bus (30% turis, kapasitas 40), Mobil (50%, kap. 4), Motor (20%, kap. 2)
        df_2024['Est_Bus'] = (df_2024['Total'] * 0.30) / 40
        df_2024['Est_Mobil'] = (df_2024['Total'] * 0.50) / 4
        df_2024['Est_Motor'] = (df_2024['Total'] * 0.20) / 2
        df_2024['Total_Kendaraan'] = df_2024['Est_Bus'] + df_2024['Est_Mobil'] + df_2024['Est_Motor']
        
        # Batas Kritis Daya Tampung Kendaraan Jalan Arteri Kota per Bulan (Simulasi: 150,000 Kendaraan/Bulan)
        kapasitas_jalan_maksimal = 150000 
        df_2024['Indeks_Kemacetan'] = (df_2024['Total_Kendaraan'] / kapasitas_jalan_maksimal) * 100

        # --- TABS PRESENTASI ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 1. Executive Summary", 
            "📈 2. Tourist Forecasting", 
            "💰 3. Economic Simulation", 
            "🚨 4. Infrastructure EWS",
            "🚦 5. Traffic Prediction (Baru)"
        ])

        # TAB 1: EXECUTIVE SUMMARY
        with tab1:
            st.subheader("Ringkasan Kinerja Makro (Tahun Berjalan)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume Wisatawan", f"{total_wisatawan_2024/1e6:.2f} Juta")
            c2.metric("Estimasi Perputaran Uang", f"Rp {(total_wisatawan_2024 * belanja_turis)/1e12:.2f} T")
            c3.metric("Length of Stay (LoS)", f"{los_aktual} Hari")
            c4.metric("Total Kendaraan Wisata", f"{df_2024['Total_Kendaraan'].sum():,.0f} Unit")
            
            st.divider()
            st.markdown("#### Pemetaan Beban Spasial: Malioboro vs Kampung Wisata")
            fig_spatial = go.Figure(data=[go.Scatter(
                x=['Kawasan Malioboro', 'Destinasi Lainnya (Kampung Wisata)'],
                y=[df_2024['Malioboro'].sum(), df_2024['Luar Malioboro'].sum()],
                mode='markers+text',
                marker=dict(size=[df_2024['Malioboro'].sum()/100000, df_2024['Luar Malioboro'].sum()/100000], color=['#e74c3c', '#2ecc71']),
                text=[f"{df_2024['Malioboro'].sum()/1e6:.1f} Juta Turis", f"{df_2024['Luar Malioboro'].sum()/1e6:.1f} Juta Turis"],
                textposition="bottom center"
            )])
            fig_spatial.update_layout(height=400, template="plotly_white", yaxis=dict(range=[0, df_2024['Total'].max() * 1.5]))
            st.plotly_chart(fig_spatial, use_container_width=True)

        # TAB 2: TOURIST FORECASTING
        with tab2:
            st.subheader("Machine Learning: Prediksi Kedatangan Wisatawan")
            X = np.arange(len(df_2024)).reshape(-1, 1)
            y = df_2024['Total'].values
            model = LinearRegression().fit(X, y)
            X_future = np.arange(len(df_2024), len(df_2024)+6).reshape(-1, 1)
            y_future = model.predict(X_future)
            
            fig_pred = go.Figure()
            fig_pred.add_trace(go.Scatter(x=df_2024['Bulan'], y=y, mode='lines+markers', name='Data Aktual', line=dict(color='#3498db', width=3)))
            fig_pred.add_trace(go.Scatter(x=['Bln+1', 'Bln+2', 'Bln+3', 'Bln+4', 'Bln+5', 'Bln+6'], y=y_future, mode='lines+markers', name='Proyeksi AI', line=dict(color='#e67e22', dash='dot', width=3)))
            fig_pred.update_layout(height=450, template="plotly_white")
            st.plotly_chart(fig_pred, use_container_width=True)

        # TAB 3: ECONOMIC SIMULATION
        with tab3:
            st.subheader("Simulasi Kebijakan: Kenaikan Masa Tinggal (LoS)")
            st.sidebar.divider()
            st.sidebar.markdown("### 🎛️ Panel Ekonomi (Tab 3)")
            simulasi_los = st.sidebar.slider("Target Tambahan LoS (Hari)", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
            
            tambahan_belanja = belanja_turis * (simulasi_los / (los_aktual if los_aktual > 0 else 1))
            tambahan_pdrb = (total_wisatawan_2024 * tambahan_belanja) / 1e12
            
            c_eco1, c_eco2, c_eco3 = st.columns(3)
            c_eco1.metric("LoS Baru (Target)", f"{los_aktual + simulasi_los:.2f} Hari", f"+ {simulasi_los} Hari")
            c_eco2.metric("Proyeksi Belanja", f"Rp {(belanja_turis + tambahan_belanja):,.0f}", f"+ Rp {tambahan_belanja:,.0f}")
            c_eco3.metric("Potensi Tambahan Ekonomi", f"+ Rp {tambahan_pdrb:.2f} Triliun")

        # TAB 4: INFRASTRUCTURE EWS
        with tab4:
            st.subheader("Peringatan Dini: Kapasitas Hotel vs Kedatangan")
            fig_cap = go.Figure()
            colors = ['#e74c3c' if val > kapasitas_kota_bulanan else '#3498db' for val in df_2024['Total']]
            fig_cap.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Total'], marker_color=colors))
            fig_cap.add_hline(y=kapasitas_kota_bulanan, line_dash="dash", line_color="black", annotation_text="Kapasitas Maksimal Hotel")
            fig_cap.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig_cap, use_container_width=True)

        # TAB 5: TRAFFIC PREDICTION (BARU)
        with tab5:
            st.subheader("🚦 Analisis & Prediksi Kemacetan Lalu Lintas (Traffic EWS)")
            st.markdown("Mengonversi volume wisatawan menjadi beban kendaraan, lalu mengukur **Indeks Kemacetan** jalan utama menuju Malioboro.")
            
            # Machine Learning untuk memprediksi kemacetan masa depan
            X_traffic = np.arange(len(df_2024)).reshape(-1, 1)
            y_traffic = df_2024['Indeks_Kemacetan'].values
            model_traffic = LinearRegression().fit(X_traffic, y_traffic)
            y_traffic_future = model_traffic.predict(np.arange(len(df_2024), len(df_2024)+6).reshape(-1, 1))

            col_t1, col_t2 = st.columns(2)
            col_t1.metric("Bulan Paling Macet", df_2024.loc[df_2024['Indeks_Kemacetan'].idxmax(), 'Bulan'], f"{df_2024['Indeks_Kemacetan'].max():.1f}% Kapasitas")
            col_t2.metric("Rata-rata Kemacetan Tahunan", f"{df_2024['Indeks_Kemacetan'].mean():.1f}%", "Status: Perlu Rekayasa Lalu Lintas")

            # Grafik Kemacetan
            fig_traffic = go.Figure()
            
            # Zona Warna Kemacetan
            fig_traffic.add_hrect(y0=0, y1=60, fillcolor="#2ecc71", opacity=0.2, line_width=0, annotation_text="Lancar")
            fig_traffic.add_hrect(y0=60, y1=90, fillcolor="#f1c40f", opacity=0.2, line_width=0, annotation_text="Padat Merayap")
            fig_traffic.add_hrect(y0=90, y1=150, fillcolor="#e74c3c", opacity=0.2, line_width=0, annotation_text="Gridlock (Lumpuh)")

            fig_traffic.add_trace(go.Scatter(x=df_2024['Bulan'], y=df_2024['Indeks_Kemacetan'], mode='lines+markers', name='Indeks Aktual (%)', line=dict(color='black', width=3)))
            fig_traffic.add_trace(go.Scatter(x=['Bln+1', 'Bln+2', 'Bln+3', 'Bln+4', 'Bln+5', 'Bln+6'], y=y_traffic_future, mode='lines+markers', name='Prediksi 6 Bln Ke Depan', line=dict(color='red', dash='dot', width=3)))
            
            fig_traffic.add_hline(y=100, line_dash="solid", line_color="darkred", line_width=2, annotation_text="Batas Maksimal Jalan (100%)")
            fig_traffic.update_layout(height=450, template="plotly_white", yaxis_title="Indeks Kemacetan (%)")
            
            st.plotly_chart(fig_traffic, use_container_width=True)
            
            st.error("🚨 **Strategic Briefing untuk Walikota:** Berdasarkan pemodelan di atas, ketika indeks menyentuh zona merah (seperti Desember/Juni), manajemen lalu lintas pasif tidak akan cukup. Diperlukan pembangunan *Park & Ride* (Kantung Parkir) di pinggiran kota, dan pelarangan Bus Besar masuk ke ring 1 Malioboro.")

    except Exception as e:
        st.error(f"Terjadi kesalahan data. Pastikan file sesuai. Log Error: {e}")

else:
    st.info("👈 Selamat Datang di Command Center. Silakan upload KETIGA file Excel di sidebar untuk memulai presentasi.")
