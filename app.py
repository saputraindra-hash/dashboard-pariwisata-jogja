import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Pariwisata Yogyakarta", layout="wide")

st.title("📊 Dashboard Analitik Pariwisata Yogyakarta")
st.markdown("**Tema:** Kesiapan Kualitas Layanan (SDM) vs Beban Volume Wisatawan")
st.divider()

# Area Upload File
st.sidebar.header("📁 Upload Dataset")
st.sidebar.markdown("Silakan upload 2 file Excel berikut:")
file_2024 = st.sidebar.file_uploader("1. Data Pengunjung 2024", type=["xlsx"])
file_2025 = st.sidebar.file_uploader("2. Data Statistik Sektoral 2025", type=["xlsx"])

if file_2024 and file_2025:
    try:
        # --- PROSES BACA DATA ---
        df_2024 = pd.read_excel(file_2024, sheet_name='Sheet1')
        df_2025 = pd.read_excel(file_2025, sheet_name='Sheet1')

        if 'Pengunjung Nusantara' not in df_2024.columns:
            st.error("⚠️ Sepertinya file tertukar! Pastikan Anda mengunggah 'Data Pengunjung 2024' di kotak PERTAMA.")
        elif 'Nama Data' not in df_2025.columns:
            st.error("⚠️ Sepertinya file tertukar! Pastikan Anda mengunggah 'Data Statistik 2025' di kotak KEDUA.")
        else:
            # --- DATA PREPARATION ---
            df_2024['Total Pengunjung'] = df_2024['Pengunjung Mancanegara'] + df_2024['Pengunjung Nusantara']
            df_2024['Luar Malioboro'] = df_2024['Total Pengunjung'] - df_2024['Malioboro']
            total_wisatawan = df_2024['Total Pengunjung'].sum()

            def get_metric(df, keyword):
                val = df.loc[df['Nama Data'].str.contains(keyword, case=False, na=False), 'Data 2025']
                return val.values[0] if not val.empty else 0

            sdm_tersertifikasi = get_metric(df_2025, 'tersertifikasi')
            jumlah_pokdarwis = get_metric(df_2025, 'Jumlah Pokdarwis')
            kampung_wisata = get_metric(df_2025, 'Kampung Wisata')

            # --- MACHINE LEARNING ALGORITHMS ---
            # 1. K-Means Clustering (Deteksi Musiman)
            X_cluster = df_2024[['Total Pengunjung']].values
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df_2024['Cluster_ID'] = kmeans.fit_predict(X_cluster)
            
            # Mengurutkan klaster dari terkecil ke terbesar
            cluster_centers = kmeans.cluster_centers_.flatten()
            sorted_idx = np.argsort(cluster_centers)
            cluster_map = {sorted_idx[0]: 'Low Season', sorted_idx[1]: 'Normal Season', sorted_idx[2]: 'Peak Season'}
            color_map = {'Low Season': '#2ecc71', 'Normal Season': '#f1c40f', 'Peak Season': '#e74c3c'}
            df_2024['Seasonality'] = df_2024['Cluster_ID'].map(cluster_map)

            # 2. Linear Regression (Analisis Tren)
            X_trend = np.arange(len(df_2024)).reshape(-1, 1)
            y_trend = df_2024['Total Pengunjung'].values
            lin_reg = LinearRegression()
            lin_reg.fit(X_trend, y_trend)
            df_2024['Trend_Line'] = lin_reg.predict(X_trend)

            # --- METRIK UTAMA (KPI) ---
            st.subheader("Ringkasan Eksekutif")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Wisatawan (2024)", f"{total_wisatawan:,.0f}")
            col2.metric("Pengunjung Malioboro", f"{df_2024['Malioboro'].sum():,.0f}")
            col3.metric("SDM Tersertifikasi", f"{sdm_tersertifikasi:,.0f} Orang")
            col4.metric("Pokdarwis Aktif", f"{jumlah_pokdarwis:,.0f} Kelompok")
            st.divider()

            # --- VISUALISASI DATA DASAR ---
            st.subheader("Visualisasi Beban Wisatawan vs Kesiapan Layanan")
            fig = make_subplots(rows=1, cols=2, specs=[[{"type": "xy"}, {"type": "domain"}]], subplot_titles=("Tren Demografi Pengunjung (2024)", "Keterpusatan Beban Malioboro"))
            fig.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Pengunjung Nusantara'], name="Nusantara", marker_color='#3498db'), row=1, col=1)
            fig.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Pengunjung Mancanegara'], name="Mancanegara", marker_color='#e74c3c'), row=1, col=1)
            fig.add_trace(go.Pie(labels=['Malioboro', 'Destinasi Lainnya'], values=[df_2024['Malioboro'].sum(), df_2024['Luar Malioboro'].sum()], hole=0.4, marker_colors=['#f1c40f', '#2ecc71']), row=1, col=2)
            fig.update_layout(barmode='stack', height=400, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.divider()

            # --- PANEL ALGORITMA ---
            st.subheader("🤖 Analisis Kecerdasan Buatan (Machine Learning)")
            col_alg1, col_alg2 = st.columns(2)

            with col_alg1:
                st.markdown("**1. K-Means Clustering (Segmentasi Musim Otomatis)**")
                fig_cluster = go.Figure()
                for season in ['Low Season', 'Normal Season', 'Peak Season']:
                    df_season = df_2024[df_2024['Seasonality'] == season]
                    fig_cluster.add_trace(go.Bar(x=df_season['Bulan'], y=df_season['Total Pengunjung'], name=season, marker_color=color_map[season]))
                fig_cluster.update_layout(height=400, template="plotly_white", barmode='group', legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_cluster, use_container_width=True)

            with col_alg2:
                st.markdown("**2. Linear Regression (Proyeksi Tren Kunjungan)**")
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=df_2024['Bulan'], y=df_2024['Total Pengunjung'], mode='lines+markers', name='Data Aktual', line=dict(color='#3498db', width=2)))
                fig_trend.add_trace(go.Scatter(x=df_2024['Bulan'], y=df_2024['Trend_Line'], mode='lines', name='Garis Tren (Regresi)', line=dict(color='#e74c3c', dash='dash', width=3)))
                fig_trend.update_layout(height=400, template="plotly_white", legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_trend, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: Pastikan format file Excel sudah benar. Log: {e}")

else:
    st.info("👈 Silakan upload file Excel 2024 dan 2025 di menu samping (sidebar) untuk melihat dashboard analitik berbasis AI.")
