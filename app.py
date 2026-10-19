import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

st.set_page_config(page_title="Advanced DSS Pariwisata", layout="wide")

st.title("🧠 Advanced Decision Support System (DSS)")
st.markdown("**Analisis Carrying Capacity (Daya Tampung) & Economic Multiplier Pariwisata Yogyakarta**")
st.divider()

st.sidebar.header("📁 Upload Dataset")
file_2024 = st.sidebar.file_uploader("1. Data Pengunjung (2024)", type=["xlsx"])
file_194 = st.sidebar.file_uploader("2. Data Sektoral (194..._4.xlsx)", type=["xlsx"])
file_112 = st.sidebar.file_uploader("3. Data Prioritas (112.xlsx)", type=["xlsx"])

if file_2024 and file_194 and file_112:
    try:
        # BACA DATA
        df_2024 = pd.read_excel(file_2024, sheet_name=0)
        df_194 = pd.read_excel(file_194, sheet_name=0)
        df_112 = pd.read_excel(file_112, sheet_name=0)

        # FUNGSI EKSTRAKSI DATA
        def get_194(keyword):
            val = df_194.loc[df_194['Nama Data'].str.contains(keyword, case=False, na=False, regex=True), 'Data 2025']
            return float(val.values[0]) if not val.empty else 0.0

        def get_112(keyword):
            val = df_112.loc[df_112['Nama Data'].str.contains(keyword, case=False, na=False, regex=True), 'Data 2025']
            if val.empty or val.values[0] == 'SIMONEVA': return 0.0
            v_str = str(val.values[0])
            v_clean = re.sub(r'[^\d,\.]', '', v_str).replace('.', '').replace(',', '.')
            return float(v_clean) if v_clean else 0.0

        # PEMROSESAN DATA 
        df_2024['Total'] = df_2024['Pengunjung Mancanegara'] + df_2024['Pengunjung Nusantara']
        
        # Metrik Ekonomi & Infrastruktur
        belanja_turis = get_112('Rata-Rata Belanja')
        kamar_bintang = get_194('Jumlah Kamar Hotel Bintang')
        kamar_non = get_194('Jumlah Kamar Hotel Non Bintang')
        total_kamar = kamar_bintang + kamar_non
        
        # Kalkulasi Daya Tampung (Kamar x 2 Orang x 30 Hari)
        kapasitas_maksimal_bulanan = total_kamar * 2 * 30
        
        df_2024['Rasio_Okupansi'] = (df_2024['Total'] / kapasitas_maksimal_bulanan) * 100
        df_2024['Pendapatan_Miliar'] = (df_2024['Total'] * belanja_turis) / 1000000000

        # TABS ANALISIS KOMPLEKS
        tab1, tab2 = st.tabs(["🏨 Carrying Capacity (Daya Tampung)", "📈 Economic Multiplier (Dampak Ekonomi)"])

        with tab1:
            st.subheader("Analisis Daya Tampung Akomodasi vs Lonjakan Wisatawan")
            st.markdown(f"**Total Kapasitas Kamar Yogyakarta:** {total_kamar:,.0f} kamar (Maksimal tampung ~{kapasitas_maksimal_bulanan:,.0f} turis/bulan)")
            
            # Deteksi Over-tourism
            over_tourism = df_2024[df_2024['Rasio_Okupansi'] > 100]
            if not over_tourism.empty:
                st.error(f"🚨 KRITIS: Ditemukan {len(over_tourism)} bulan di mana jumlah wisatawan MELEBIHI kapasitas maksimal hotel di Yogyakarta!")
            
            fig_cap = go.Figure()
            fig_cap.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Total'], name="Total Wisatawan", marker_color='#3498db'))
            fig_cap.add_hline(y=kapasitas_maksimal_bulanan, line_dash
