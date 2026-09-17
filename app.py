import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Konfigurasi Supabase
SUPABASE_URL = "https://kfbsbhsztfruhdqjydqs.supabase.co"
SUPABASE_KEY = "sb_publishable_E8u1TX_GBi4E51TYqTclNw_AImfUb8m"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

st.title("🌱 SIDAHTRA - Sistem Data Hibah Alsintan Terpadu")

# Contoh menu sederhana untuk input data
menu = st.sidebar.selectbox("Pilih Menu", ["Dashboard", "Input Baru", "Rekap Data"])

if menu == "Input Baru":
    st.subheader("Form Input Data Hibah")
    with st.form("form_hibah"):
        asal_usul = st.text_input("Asal Usul")
        tahun_hibah = st.text_input("Tahun Hibah")
        jenis_barang = st.text_input("Jenis Barang")
        jumlah = st.number_input("Jumlah", min_value=1, step=1)
        kelompok = st.text_input("Nama Kelompok Tani")
        nama_ketua = st.text_input("Nama Ketua")
        kecamatan = st.text_input("Kecamatan")
        
        submitted = st.form_submit_button("Simpan ke Supabase")
        
        if submitted:
            try:
                data = {
                    "asal_usul": asal_usul,
                    "tahun_hibah": tahun_hibah,
                    "jenis_barang": jenis_barang,
                    "jumlah": jumlah,
                    "kelompok": kelompok,
                    "nama_ketua": nama_ketua,
                    "kecamatan": kecamatan
                }
                # Menyimpan data ke tabel 'hibah' di Supabase
                response = supabase.table("hibah").insert(data).execute()
                st.success("Data berhasil disimpan secara permanen di Supabase! 🎉")
            except Exception as e:
                st.error(f"Gagal menyimpan data: {e}")

elif menu == "Rekap Data":
    st.subheader("Rekapitulasi Data Hibah (Dari Supabase)")
    try:
        # Mengambil data dari tabel 'hibah' di Supabase
        response = supabase.table("hibah").select("*").execute()
        data = response.data
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.info("Belum ada data yang tersimpan.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")