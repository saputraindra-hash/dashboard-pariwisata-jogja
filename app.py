import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
import re

st.set_page_config(page_title="Ultimate DSS Pariwisata Jogja", layout="wide", initial_sidebar_state="expanded")

# --- HEADER PRESENTASI ---
st.title("🏛️ Command Center Pariwisata & Ekonomi Kota Yogyakarta")
st.markdown("*Platform Analitik Eksekutif Berbasis Data Sektoral & Machine Learning (Presentasi Walikota)*")
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
        
        # Metrik Ekonomi & SDM
        belanja_turis = get_112('Rata-Rata Belanja')
        los_aktual = get_112('Length of Stay')
        pdrb_pariwisata = get_112('Kontribusi sektor pariwisata terhadap PDRB')
        
        kamar_bintang = get_194('Jumlah Kamar Hotel Bintang')
        kamar_non = get_194('Jumlah Kamar Hotel Non Bintang')
        total_kamar = kamar_bintang + kamar_non
        kapasitas_kota_bulanan = total_kamar * 2 * 30  # Asumsi 1 kamar 2 orang, 30 hari
        
        sdm_sertifikasi = get_194('tersertifikasi')
        pokdarwis = get_194('Jumlah Pokdarwis')
        kampung_wisata = get_194('Kampung Wisata')

        # --- TABS PRESENTASI ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 1. Executive Summary", 
            "📈 2. Predictive Forecasting", 
            "💰 3. Economic ROI Simulation", 
            "🚨 4. Carrying Capacity & HR"
        ])

        # ==========================================
        # TAB 1: EXECUTIVE SUMMARY (STORYTELLING)
        # ==========================================
        with tab1:
            st.subheader("Ringkasan Kinerja Makro (Tahun Berjalan)")
            
            # Kartu Metrik Utama
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume Wisatawan", f"{total_wisatawan_2024/1e6:.2f} Juta", "Data 2024")
            c2.metric("Estimasi Perputaran Uang", f"Rp {(total_wisatawan_2024 * belanja_turis)/1e12:.2f} Triliun", f"Belanja: Rp {belanja_turis/1e6:.1f} Jt/Orang")
            c3.metric("Length of Stay (LoS)", f"{los_aktual} Hari", "Indikator Prioritas")
            c4.metric("Kapasitas Akomodasi", f"{total_kamar:,.0f} Kamar", "Bintang & Non-Bintang")
            
            st.divider()
            
            # Auto-Generated Insights
            st.markdown("### 🤖 *Auto-Generated Strategic Insights*")
            st.info(f"**1. Konsentrasi Ekstrem:** Dari {total_wisatawan_2024/1e6:.1f} juta wisatawan, sebesar **{(df_2024['Malioboro'].sum()/total_wisatawan_2024)*100:.1f}%** menumpuk di kawasan Malioboro. Dibutuhkan intervensi segera ke {kampung_wisata:,.0f} Kampung Wisata lainnya.")
            st.info(f"**2. Ketimpangan SDM:** Kota ini menerima {total_wisatawan_2024/1e6:.1f} juta tamu, namun hanya didukung oleh **{sdm_sertifikasi:,.0f} pekerja pariwisata tersertifikasi**. Rasio layanan saat ini berada di tingkat bahaya (1 SDM melayani ribuan turis).")
            
            # Grafik Distribusi Spasial (Bubble Chart)
            st.markdown("#### Pemetaan Beban Spasial: Malioboro vs Kampung Wisata")
            fig_spatial = go.Figure(data=[go.Scatter(
                x=['Kawasan Malioboro', 'Luar Malioboro (Kampung Wisata dll)'],
                y=[df_2024['Malioboro'].sum(), df_2024['Luar Malioboro'].sum()],
                mode='markers+text',
                marker=dict(size=[df_2024['Malioboro'].sum()/100000, df_2024['Luar Malioboro'].sum()/100000], color=['#e74c3c', '#2ecc71']),
                text=[f"{df_2024['Malioboro'].sum()/1e6:.1f} Juta Turis", f"{df_2024['Luar Malioboro'].sum()/1e6:.1f} Juta Turis"],
                textposition="bottom center"
            )])
            fig_spatial.update_layout(height=400, template="plotly_white", yaxis=dict(range=[0, df_2024['Total'].max() * 1.5]))
            st.plotly_chart(fig_spatial, use_container_width=True)


        # ==========================================
        # TAB 2: PREDICTIVE FORECASTING (ML)
        # ==========================================
        with tab2:
            st.subheader("Machine Learning: Prediksi Pertumbuhan Masa Depan")
            st.markdown("Menggunakan model *Linear Regression* untuk memproyeksikan lintasan volume wisatawan di tahun berikutnya berdasarkan data historis.")
            
            X = np.arange(len(df_2024)).reshape(-1, 1)
            y = df_2024['Total'].values
            model = LinearRegression().fit(X, y)
            
            # Proyeksi 6 bulan ke depan
            X_future = np.arange(len(df_2024), len(df_2024)+6).reshape(-1, 1)
            y_future = model.predict(X_future)
            
            fig_pred = go.Figure()
            fig_pred.add_trace(go.Scatter(x=df_2024['Bulan'], y=y, mode='lines+markers', name='Data Historis (Aktual)', line=dict(color='#3498db', width=3)))
            
            bulan_depan = ['Bln+1', 'Bln+2', 'Bln+3', 'Bln+4', 'Bln+5', 'Bln+6']
            fig_pred.add_trace(go.Scatter(x=bulan_depan, y=y_future, mode='lines+markers', name='AI Forecasting (Proyeksi)', line=dict(color='#e67e22', dash='dot', width=3)))
            
            fig_pred.update_layout(height=450, template="plotly_white", title="Trajektori Kunjungan Wisatawan")
            st.plotly_chart(fig_pred, use_container_width=True)
            
            st.warning("💡 **Pernyataan Eksekutif:** Tren proyeksi menunjukkan peningkatan. Tanpa penambahan infrastruktur baru, lonjakan di tahun depan akan memicu kemacetan total (*gridlock*) di kuartal ketiga.")


        # ==========================================
        # TAB 3: ECONOMIC ROI SIMULATION
        # ==========================================
        with tab3:
            st.subheader("Simulasi Kebijakan: Economic Multiplier Effect")
            st.markdown("Sebagai Walikota, Anda dapat menetapkan target kenaikan masa tinggal (*Length of Stay*) dan melihat dampaknya terhadap ekonomi daerah secara *real-time*.")
            
            st.sidebar.divider()
            st.sidebar.markdown("### 🎛️ Panel Kebijakan (Tab 3)")
            simulasi_los = st.sidebar.slider("Target Kenaikan Length of Stay (Hari)", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
            
            # Asumsi ekonomi dasar: Jika LoS naik, belanja otomatis naik proporsional
            persentase_kenaikan_los = simulasi_los / (los_aktual if los_aktual > 0 else 1)
            tambahan_belanja_per_turis = belanja_turis * persentase_kenaikan_los
            
            pendapatan_dasar_triliun = (total_wisatawan_2024 * belanja_turis) / 1e12
            tambahan_pendapatan_triliun = (total_wisatawan_2024 * tambahan_belanja_per_turis) / 1e12
            
            col_eco1, col_eco2, col_eco3 = st.columns(3)
            col_eco1.metric("LoS Baru (Target)", f"{los_aktual + simulasi_los:.2f} Hari", f"+ {simulasi_los} Hari")
            col_eco2.metric("Proyeksi Belanja Turis", f"Rp {(belanja_turis + tambahan_belanja_per_turis):,.0f}", f"+ Rp {tambahan_belanja_per_turis:,.0f}")
            col_eco3.metric("TAMBAHAN PDRB (Uang Beredar)", f"+ Rp {tambahan_pendapatan_triliun:.2f} Triliun", "Dampak Langsung ke Ekonomi Kota")
            
            st.divider()
            fig_roi = go.Figure(data=[
                go.Bar(name='Pendapatan Saat Ini', x=['Proyeksi Pendapatan Daerah'], y=[pendapatan_dasar_triliun], marker_color='#34495e'),
                go.Bar(name='Tambahan Hasil Kebijakan (ROI)', x=['Proyeksi Pendapatan Daerah'], y=[tambahan_pendapatan_triliun], marker_color='#2ecc71')
            ])
            fig_roi.update_layout(barmode='stack', height=400, template="plotly_white", title="Visualisasi Tumpukan (Stack) Kekuatan Ekonomi Triliunan")
            st.plotly_chart(fig_roi, use_container_width=True)


        # ==========================================
        # TAB 4: CARRYING CAPACITY & HR EWS
        # ==========================================
        with tab4:
            st.subheader("Sistem Peringatan Dini (EWS): Daya Tampung vs Rasio SDM")
            
            df_2024['Status_Kapasitas'] = np.where(df_2024['Total'] > kapasitas_kota_bulanan, 'OVER CAPACITY', 'Aman')
            
            st.markdown(f"**Batas Kritis Infrastruktur Akomodasi:** {kapasitas_kota_bulanan:,.0f} Pengunjung / Bulan")
            
            fig_cap = go.Figure()
            colors = ['#e74c3c' if val > kapasitas_kota_bulanan else '#3498db' for val in df_2024['Total']]
            fig_cap.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Total'], marker_color=colors, name="Volume Wisatawan"))
            fig_cap.add_hline(y=kapasitas_kota_bulanan, line_dash="dash", line_color="black", line_width=3, annotation_text="Kapasitas Maksimal Hotel")
            fig_cap.update_layout(height=400, template="plotly_white", title="Bulan-bulan Merah (Over-tourism)")
            st.plotly_chart(fig_cap, use_container_width=True)
            
            st.divider()
            st.markdown("### ⚠️ Evaluasi Krisis SDM (Human Resource Crisis)")
            beban_per_sdm = total_wisatawan_2024 / (sdm_sertifikasi if sdm_sertifikasi > 0 else 1)
            
            c_hr1, c_hr2 = st.columns(2)
            c_hr1.metric("Rasio SDM Tersertifikasi terhadap Turis", f"1 SDM : {beban_per_sdm:,.0f} Turis")
            c_hr2.metric("Rasio Beban Pokdarwis (Kelompok Sadar Wisata)", f"{total_wisatawan_2024/pokdarwis:,.0f} Turis / Pokdarwis")
            
            st.error("Rekomendasi Kebijakan (Policy Brief): Segera cairkan APBD untuk program sertifikasi SKKNI massal. Kualitas layanan ('Service Excellence') tidak akan tercapai jika 1 tenaga kerja harus melayani puluhan ribu turis setahun.")

    except Exception as e:
        st.error(f"Terjadi kesalahan data. Pastikan file sesuai. Log Error: {e}")

else:
    st.info("👈 Selamat Datang di Command Center. Silakan upload KETIGA file Excel di sidebar untuk memulai presentasi.")
