import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression

# Konfigurasi Halaman
st.set_page_config(page_title="DSS Pariwisata Yogyakarta", layout="wide")

st.title("📊 Sistem Pendukung Keputusan (DSS) Pariwisata Yogyakarta - Versi 2.0")
st.markdown("**Tema:** Kesiapan Layanan (SDM), Distribusi Spasial, dan Peringatan Dini Overcrowding")
st.divider()

# Area Upload File
st.sidebar.header("📁 Upload Dataset")
file_2024 = st.sidebar.file_uploader("1. Data Pengunjung 2024 (Wajib)", type=["xlsx"])
file_2025 = st.sidebar.file_uploader("2. Data Statistik Sektoral 2025 (Wajib)", type=["xlsx"])
file_opsional = st.sidebar.file_uploader("3. Data Sektoral Tambahan (Opsional)", type=["xlsx"])

if file_2024 and file_2025:
    try:
        # --- PROSES BACA DATA ---
        df_2024 = pd.read_excel(file_2024, sheet_name='Sheet1')
        df_2025 = pd.read_excel(file_2025, sheet_name='Sheet1')

        if 'Pengunjung Nusantara' not in df_2024.columns:
            st.error("⚠️ File tertukar! Pastikan 'Data Pengunjung 2024' di kotak PERTAMA.")
        elif 'Nama Data' not in df_2025.columns:
            st.error("⚠️ File tertukar! Pastikan 'Data Statistik 2025' di kotak KEDUA.")
        else:
            # --- DATA PREPARATION ---
            df_2024['Total Pengunjung'] = df_2024['Pengunjung Mancanegara'] + df_2024['Pengunjung Nusantara']
            df_2024['Luar Malioboro'] = df_2024['Total Pengunjung'] - df_2024['Malioboro']
            total_wisatawan = df_2024['Total Pengunjung'].sum()
            total_malioboro_aktual = df_2024['Malioboro'].sum()
            total_luar_aktual = df_2024['Luar Malioboro'].sum()

            def get_metric(df, keyword):
                val = df.loc[df['Nama Data'].str.contains(keyword, case=False, na=False), 'Data 2025']
                return val.values[0] if not val.empty else 0

            sdm_tersertifikasi = get_metric(df_2025, 'tersertifikasi')
            jumlah_pokdarwis = get_metric(df_2025, 'Jumlah Pokdarwis')
            kampung_wisata = get_metric(df_2025, 'Kampung Wisata')

            # --- FITUR DSS (WHAT-IF ANALYSIS) ---
            st.sidebar.divider()
            st.sidebar.subheader("🎛️ Simulasi Kebijakan (What-If)")
            st.sidebar.markdown("Target Pengurangan Beban Malioboro:")
            target_distribusi = st.sidebar.slider("Pindahkan ke Destinasi Lain (%)", min_value=0, max_value=50, value=15, step=5)
            
            pengurangan_malioboro = (total_malioboro_aktual * target_distribusi) / 100
            malioboro_simulasi = total_malioboro_aktual - pengurangan_malioboro
            luar_simulasi = total_luar_aktual + pengurangan_malioboro

            # --- MACHINE LEARNING (K-Means & Regresi) ---
            X_cluster = df_2024[['Total Pengunjung']].values
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df_2024['Cluster_ID'] = kmeans.fit_predict(X_cluster)
            cluster_centers = kmeans.cluster_centers_.flatten()
            sorted_idx = np.argsort(cluster_centers)
            cluster_map = {sorted_idx[0]: 'Low Season', sorted_idx[1]: 'Normal Season', sorted_idx[2]: 'Peak Season'}
            df_2024['Seasonality'] = df_2024['Cluster_ID'].map(cluster_map)

            X_trend = np.arange(len(df_2024)).reshape(-1, 1)
            lin_reg = LinearRegression().fit(X_trend, df_2024['Total Pengunjung'].values)
            df_2024['Trend_Line'] = lin_reg.predict(X_trend)

            # --- TABS NAVIGASI ---
            tab1, tab2, tab3 = st.tabs(["📊 Ringkasan & Simulasi", "📍 Peta Spasial (Heatmap)", "🚨 Early Warning System"])

            with tab1:
                st.subheader("Ringkasan Eksekutif & Simulasi Distribusi")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Wisatawan", f"{total_wisatawan:,.0f}")
                col2.metric("Proyeksi Malioboro", f"{malioboro_simulasi:,.0f}", f"-{pengurangan_malioboro:,.0f} (-{target_distribusi}%)")
                col3.metric("SDM Tersertifikasi", f"{sdm_tersertifikasi:,.0f} Orang")
                col4.metric("Beban per Pokdarwis", f"{(luar_simulasi/jumlah_pokdarwis if jumlah_pokdarwis > 0 else 0):,.0f} Turis")
                
                fig = make_subplots(rows=1, cols=2, specs=[[{"type": "xy"}, {"type": "domain"}]], subplot_titles=("Tren Demografi", "Simulasi Keterpusatan Beban"))
                fig.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Pengunjung Nusantara'], name="Nusantara", marker_color='#3498db'), row=1, col=1)
                fig.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Pengunjung Mancanegara'], name="Mancanegara", marker_color='#e74c3c'), row=1, col=1)
                fig.add_trace(go.Pie(labels=['Malioboro', 'Destinasi Lainnya (Kampung Wisata)'], values=[malioboro_simulasi, luar_simulasi], hole=0.4, marker_colors=['#f1c40f', '#2ecc71']), row=1, col=2)
                fig.update_layout(barmode='stack', height=400, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("📍 Simulasi Pemetaan Spasial Kepadatan")
                st.markdown("Peta ini memvisualisasikan bagaimana kepadatan bergeser jika Anda menerapkan kebijakan pengurangan beban Malioboro.")
                
                # Membuat Data Dummy Koordinat untuk Visualisasi
                data_peta = pd.DataFrame({
                    'Lokasi': ['Malioboro', 'Kampung Wisata Taman Sari', 'Kampung Wisata Kotagede', 'Kampung Wisata Purbayan'],
                    'Lat': [-7.7926, -7.8100, -7.8280, -7.8250],
                    'Lon': [110.3658, 110.3580, 110.3950, 110.4000],
                    'Pengunjung': [malioboro_simulasi, luar_simulasi*0.4, luar_simulasi*0.3, luar_simulasi*0.3]
                })
                
                fig_map = px.scatter_mapbox(data_peta, lat="Lat", lon="Lon", size="Pengunjung", color="Pengunjung",
                                            color_continuous_scale=px.colors.sequential.YlOrRd, size_max=40, zoom=12,
                                            hover_name="Lokasi", mapbox_style="carto-positron")
                fig_map.update_layout(height=500, margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)

            with tab3:
                st.subheader("🚨 Sistem Peringatan Dini (Early Warning System)")
                batas_kritis = 1000000 # Contoh threshold 1 Juta
                
                bulan_kritis = df_2024[df_2024['Total Pengunjung'] > batas_kritis]
                if not bulan_kritis.empty:
                    st.error(f"⚠️ PERINGATAN: Terdeteksi {len(bulan_kritis)} bulan dengan proyeksi volume di atas daya tampung infrastruktur kritis (>1 Juta turis)!")
                    for idx, row in bulan_kritis.iterrows():
                        st.warning(f"Bulan **{row['Bulan']}**: {row['Total Pengunjung']:,.0f} Pengunjung. Tindakan: Aktifkan manajemen rekayasa lalu lintas & siagakan posko CHSE.")
                else:
                    st.success("✅ Kapasitas lalu lintas diproyeksikan aman sepanjang tahun.")
                
                # Grafik clustering musiman
                fig_cluster = go.Figure()
                color_map = {'Low Season': '#2ecc71', 'Normal Season': '#f1c40f', 'Peak Season': '#e74c3c'}
                for season in ['Low Season', 'Normal Season', 'Peak Season']:
                    df_season = df_2024[df_2024['Seasonality'] == season]
                    fig_cluster.add_trace(go.Bar(x=df_season['Bulan'], y=df_season['Total Pengunjung'], name=season, marker_color=color_map[season]))
                fig_cluster.add_hline(y=batas_kritis, line_dash="dash", line_color="red", annotation_text="Batas Kritis Infrastruktur")
                fig_cluster.update_layout(height=400, template="plotly_white")
                st.plotly_chart(fig_cluster, use_container_width=True)

            # Jika file ke-3 diupload
            if file_opsional:
                st.divider()
                st.subheader("📂 Analisis Data Sektoral Tambahan")
                df_opsional = pd.read_excel(file_opsional, sheet_name=0)
                st.dataframe(df_opsional.head(10), use_container_width=True)
                st.success("File tambahan berhasil diintegrasikan. Siap untuk diekstrak menjadi model analitik lanjutan.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data. Log: {e}")

else:
    st.info("👈 Silakan upload file Excel 2024 dan 2025 di menu samping (sidebar) untuk melihat dashboard analitik berbasis AI.")
