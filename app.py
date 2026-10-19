import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots 
import make_subplots
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Pariwisata Yogyakarta", layout="wide")

# Judul Aplikasi
st.title("📊 Dashboard Analitik Pariwisata Yogyakarta")
st.markdown("**Tema:** Kesiapan Kualitas Layanan (SDM) vs Beban Volume Wisatawan")
st.divider()

# Area Upload File
st.sidebar.header("📁 Upload Dataset")
st.sidebar.markdown("Silakan upload 2 file Excel berikut:")
file_2024 = st.sidebar.file_uploader("1. Data Pengunjung 2024", type=["xlsx"])
file_2025 = st.sidebar.file_uploader("2. Data Statistik Sektoral 2025", type=["xlsx"])

if file_2024 and file_2025:
    # --- PROSES BACA DATA ---
    df_2024 = pd.read_excel(file_2024, sheet_name='Sheet1')
    df_2025 = pd.read_excel(file_2025, sheet_name='Sheet1')

    # --- DATA PREPARATION ---
    df_2024['Total Pengunjung'] = df_2024['Pengunjung Mancanegara'] + df_2024['Pengunjung Nusantara']
    df_2024['Luar Malioboro'] = df_2024['Total Pengunjung'] - df_2024['Malioboro']
    total_wisatawan = df_2024['Total Pengunjung'].sum()

    sdm_tersertifikasi = df_2025.loc[df_2025['Nama Data'].str.contains('tersertifikasi', case=False, na=False), 'Data 2025'].values[0]
    jumlah_pokdarwis = df_2025.loc[df_2025['Nama Data'].str.contains('Jumlah Pokdarwis', case=False, na=False), 'Data 2025'].values[0]
    kampung_wisata = df_2025.loc[df_2025['Nama Data'].str.contains('Kampung Wisata', case=False, na=False), 'Data 2025'].values[0]

    # --- METRIK UTAMA (KPI) ---
    st.subheader("Ringkasan Eksekutif")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Wisatawan (2024)", f"{total_wisatawan:,.0f}")
    col2.metric("Pengunjung Malioboro", f"{df_2024['Malioboro'].sum():,.0f}")
    col3.metric("SDM Tersertifikasi", f"{sdm_tersertifikasi:,.0f} Orang")
    col4.metric("Pokdarwis Aktif", f"{jumlah_pokdarwis:,.0f} Kelompok")
    
    st.divider()

    # --- VISUALISASI PLOTLY ---
    st.subheader("Visualisasi Data Interaktif")
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "xy"}, {"type": "domain"}],
               [{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=(
            "Tren Kunjungan Wisatawan per Bulan (2024)", 
            "Distribusi Beban: Malioboro vs Lainnya", 
            "Krisis SDM: Rasio Pekerja Tersertifikasi", 
            "Kapasitas Komunitas (Pokdarwis)"
        ),
        row_heights=[0.6, 0.4]
    )

    # Panel 1: Bar & Line Chart
    fig.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Pengunjung Nusantara'], name="Nusantara", marker_color='#3498db'), row=1, col=1)
    fig.add_trace(go.Bar(x=df_2024['Bulan'], y=df_2024['Pengunjung Mancanegara'], name="Mancanegara", marker_color='#e74c3c'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_2024['Bulan'], y=df_2024['Total Pengunjung'], name="Total Kunjungan", mode='lines+markers', line=dict(color='black', width=2)), row=1, col=1)
    fig.update_layout(barmode='stack')

    # Panel 2: Donut Chart
    fig.add_trace(go.Pie(labels=['Malioboro', 'Destinasi Lainnya'], 
                         values=[df_2024['Malioboro'].sum(), df_2024['Luar Malioboro'].sum()],
                         hole=0.4, marker_colors=['#f1c40f', '#2ecc71']), row=1, col=2)

    # Panel 3: KPI Indicator SDM
    fig.add_trace(go.Indicator(
        mode="number+gauge",
        value=sdm_tersertifikasi,
        title={"text": f"SDM Tersertifikasi<br><span style='font-size:0.8em;color:gray'>Melayani {total_wisatawan/1000000:.1f} Juta Turis</span>"},
        gauge={'axis': {'range': [0, 1000]}, 'bar': {'color': "#e74c3c"}}
    ), row=2, col=1)

    # Panel 4: KPI Indicator Pokdarwis
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=jumlah_pokdarwis,
        title={"text": "Jumlah Pokdarwis Aktif"},
        delta={'reference': kampung_wisata, 'position': "bottom"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=2, col=2)

    fig.update_layout(height=750, template="plotly_white", margin=dict(t=50, b=50, l=50, r=50))
    
    # Render di Streamlit
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Silakan upload file Excel 2024 dan 2025 di menu samping (sidebar) untuk melihat dashboard.")
