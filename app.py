import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import re

# Konfigurasi Halaman
st.set_page_config(page_title="Executive Dashboard Pariwisata", layout="wide", initial_sidebar_state="expanded")

st.title("🏛️ Executive Dashboard Pariwisata Kota Yogyakarta")
st.markdown("**Integrasi Data Statistik Sektoral & Indikator Kinerja Prioritas Daerah**")
st.divider()

# Area Upload File
st.sidebar.header("📁 Upload Dataset")
st.sidebar.markdown("Silakan upload 2 file terbaru:")
file_194 = st.sidebar.file_uploader("1. Data Statistik Sektoral (194..._4.xlsx)", type=["xlsx"])
file_112 = st.sidebar.file_uploader("2. Data Prioritas Dinas (112.xlsx)", type=["xlsx"])

if file_194 and file_112:
    try:
        # --- BACA DATA ---
        df_194 = pd.read_excel(file_194, sheet_name=0)
        df_112 = pd.read_excel(file_112, sheet_name=0)

        # Fungsi Pembersih Data Numerik Khusus (Mencegah Error akibat titik/koma format uang)
        def get_num(df, keyword):
            try:
                # Menggunakan regex=True agar pencarian lebih dinamis
                val = df.loc[df['Nama Data'].str.contains(keyword, case=False, na=False, regex=True), 'Data 2025'].values[0]
                if pd.isna(val) or val == 'SIMONEVA':
                    return 0.0
                if isinstance(val, str):
                    # Hanya ambil angka, koma, dan titik
                    val_clean = re.sub(r'[^\d,\.]', '', val)
                    # Standarisasi pemisah ribuan dan desimal
                    val_clean = val_clean.replace('.', '').replace(',', '.')
                    return float(val_clean) if val_clean else 0.0
                return float(val)
            except:
                return 0.0

        def get_str(df, keyword):
            try:
                val = df.loc[df['Nama Data'].str.contains(keyword, case=False, na=False, regex=True), 'Data 2025'].values[0]
                return str(val) if not pd.isna(val) else "-"
            except:
                return "-"

        # --- EKSTRAKSI DATA FILE 112 (PRIORITAS & EKONOMI) ---
        pdrb_akomodasi = get_num(df_112, 'PDRB Sektor Penyediaan Akomodasi')
        belanja_wisatawan = get_num(df_112, 'Rata-Rata Belanja')
        los_prioritas = get_num(df_112, 'Length of Stay')
        dtw_prima = get_num(df_112, 'Persentase Daya Tarik Wisata.*Prima')
        sdm_meningkat = get_num(df_112, 'Persentase Sumber Daya Manusia yang Meningkat')
        rb_dinas = get_str(df_112, 'Nilai Reformasi Birokrasi')
        sakip_dinas = get_str(df_112, 'Nilai  SAKIP')

        # --- EKSTRAKSI DATA FILE 194 (SEKTORAL & VOLUMETRIK) ---
        bulan_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        
        # Mengekstrak otomatis data bulanan (Januari - Desember)
        n_data = [get_num(df_194, f'Wisatawan Nusantara Bulan {b}') for b in bulan_list]
        m_data = [get_num(df_194, f'Wisatawan Mancanegara Bulan {b}') for b in bulan_list]
        
        df_trend = pd.DataFrame({'Bulan': bulan_list, 'Nusantara': n_data, 'Mancanegara': m_data})
        df_trend['Total'] = df_trend['Nusantara'] + df_trend['Mancanegara']
        
        total_wisatawan = df_trend['Total'].sum()
        
        pokdarwis = get_num(df_194, 'Jumlah Pokdarwis')
        sdm_tersertifikasi = get_num(df_194, 'tersertifikasi')

        # --- TABS NAVIGASI ---
        tab1, tab2, tab3 = st.tabs(["💰 Dampak Ekonomi", "📈 Tren Kedatangan", "🎖️ Kualitas & Tata Kelola"])

        # TAB 1: DAMPAK EKONOMI
        with tab1:
            st.subheader("Dampak Ekonomi Makro Sektor Pariwisata")
            st.markdown("Mengukur kekuatan finansial yang dihasilkan dari pergerakan pariwisata berdasarkan Data Prioritas (112).")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("PDRB Akomodasi & Makan", f"Rp {pdrb_akomodasi:,.0f} M")
            col2.metric("Rata-Rata Belanja Turis", f"Rp {belanja_wisatawan:,.0f}")
            col3.metric("Estimasi Total Pengeluaran", f"Rp {(total_wisatawan * belanja_wisatawan / 1000000000):,.1f} M", "Asumsi Total Turis × Belanja")
            col4.metric("Length of Stay (LoS)", f"{los_prioritas} Hari")
            
            st.divider()
            st.info("💡 **Catatan Eksekutif:** Pendapatan pariwisata berbanding lurus dengan *Length of Stay*. Menambah daya tarik wisata malam hari dapat meningkatkan masa tinggal, yang secara eksponensial akan mendongkrak pengeluaran wisatawan di Kota Yogyakarta.")

        # TAB 2: TREN VOLUMETRIK
        with tab2:
            st.subheader("Analisis Volume Kunjungan Wisatawan per Bulan")
            st.markdown(f"Total Wisatawan Tahun Ini (Berdasarkan Data 194): **{total_wisatawan:,.0f} Orang**")
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=df_trend['Bulan'], y=df_trend['Nusantara'], name="Wisatawan Nusantara", marker_color='#3498db'))
            fig_trend.add_trace(go.Bar(x=df_trend['Bulan'], y=df_trend['Mancanegara'], name="Wisatawan Mancanegara", marker_color='#e74c3c'))
            fig_trend.add_trace(go.Scatter(x=df_trend['Bulan'], y=df_trend['Total'], name="Garis Total Kunjungan", mode='lines+markers', line=dict(color='#2c3e50', width=3)))
            
            fig_trend.update_layout(barmode='stack', height=500, template="plotly_white", 
                                    legend=dict(orientation="h", y=1.1, x=0.3))
            st.plotly_chart(fig_trend, use_container_width=True)

        # TAB 3: KUALITAS & TATA KELOLA
        with tab3:
            st.subheader("Indikator Kualitas Layanan Prima & Reformasi Birokrasi")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Daya Tarik Standar Prima", f"{dtw_prima}%")
            c2.metric("Peningkatan Kompetensi SDM", f"{sdm_meningkat}%")
            c3.metric("SDM Tersertifikasi SKKNI", f"{sdm_tersertifikasi:,.0f} Orang")
            c4.metric("Jumlah Pokdarwis Aktif", f"{pokdarwis:,.0f} Kelompok")
            
            st.divider()
            st.markdown("##### Akuntabilitas & Governance Dinas Pariwisata")
            cg1, cg2 = st.columns(2)
            with cg1:
                st.success(f"🏛️ **Nilai Reformasi Birokrasi:** \n\n ### {rb_dinas.strip()}")
            with cg2:
                st.success(f"🛡️ **Nilai SAKIP Dinas:** \n\n ### {sakip_dinas.strip()}")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data. Log error: {e}")

else:
    st.info("👈 Silakan upload file '194..._4.xlsx' dan '112.xlsx' di menu sidebar sebelah kiri untuk merender dashboard.")
