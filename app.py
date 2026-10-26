import streamlit as st

# Import semua sub-file dari folder modules
from modules import modul_1, modul_2, modul_6 

# Konfigurasi Halaman 
st.set_page_config(page_title="Command Center Gubernur DIY", layout="wide", page_icon="🏛️")

st.sidebar.title("🏛️ Command Center DIY")
st.sidebar.markdown("Decision Support System (DSS)")

# Menu AI Keselamatan sekarang berada di urutan pertama
menu = st.sidebar.radio("Navigasi Modul:", [
    "1. Master Overlay & AI Keselamatan",
    "2. Tata Ruang & Pangan",
    "3. Aglomerasi & Transportasi",
  
])

# Sistem Routing ke File yang Berbeda
if menu == "1. Master Overlay & AI Keselamatan":
    modul_1.Tampilkan()
elif menu == "2. Tata Ruang & Pangan":
    modul_2.Tampilkan()
elif menu == "3. Aglomerasi & Transportasi":
    modul_3.Tampilkan()
else:
    st.info("Modul ini sedang dalam tahap pengembangan struktur (Pindahkan ke file terpisah).")
