import streamlit as st

# Import semua sub-file dari folder modules
from modules import modul_1

# Konfigurasi Halaman 
st.set_page_config(page_title="Command Center Gubernur DIY", layout="wide", page_icon="🏛️")

st.sidebar.title("🏛️ Command Center DIY")
st.sidebar.markdown("Decision Support System (DSS)")

# Menu AI Keselamatan sekarang berada di urutan pertama
menu = st.sidebar.radio("Navigasi Modul:", [
    "1. Master Overlay & AI Keselamatan",
    "2. Tata Ruang & Pangan (TAHAP PENGEMBANGAN)",
    "3. Aglomerasi & Transportasi (TAHAP PENGEMBANGAN)",
  
])

# Sistem Routing ke File yang Berbeda
if menu == "1. Master Overlay & AI Keselamatan":
    modul_1.Tampilkan()
else:
    st.info("Modul ini sedang dalam tahap pengembangan struktur (Pindahkan ke file terpisah).")
