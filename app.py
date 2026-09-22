import os
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import qrcode
from supabase import create_client, Client

# --- KREDENSIAL SUPABASE ---
SUPABASE_URL = "https://kfbsbhsztfruhdqjydqs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtmYnNiaHN6dGZydWhkcWp5ZHFzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk2NTM0NzIsImV4cCI6MjEwNTIyOTQ3Mn0.jEvSj_2gKTEmhRyR1IzjXCNPXOMIqafs_M4tq82QNUE"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase: Client = init_supabase()

# Direktori Lokal File Sementara
UPLOAD_DIR = "sidahtra_files"
os.makedirs(os.path.join(UPLOAD_DIR, "foto"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "proposal"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "bast"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "qrcode"), exist_ok=True)

st.set_page_config(page_title="SIDAHTRA - Sistem Data Hibah Alsintan Terpadu", layout="wide")

# CSS Kustom
st.markdown("""
    <style>
        .stApp { background-color: #F3F7F4; }
        .main-header {
            background: linear-gradient(rgba(19, 56, 32, 0.85), rgba(42, 111, 55, 0.85)), 
                        url('https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=1200&auto=format&fit=crop');
            background-size: cover; background-position: center;
            padding: 35px 20px; border-radius: 14px; color: white;
            box-shadow: 0 4px 15px rgba(19, 56, 32, 0.2); margin-bottom: 25px; text-align: center;
        }
        .stButton>button { background-color: #2A6F37; color: white; border-radius: 8px; border: none; font-weight: 600; padding: 0.5rem 1rem; width: 100%; }
        .stButton>button:hover { background-color: #133820; color: white; }
    </style>
""", unsafe_allow_html=True)

def generate_qr_code(data_id, kelompok, jenis, kecamatan):
    qr_data = f"SIDAHTRA ASSET\nID: {data_id}\nKelompok: {kelompok}\nBarang: {jenis}\nKecamatan: {kecamatan}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(UPLOAD_DIR, "qrcode", f"qr_asset_{data_id}.png")
    img.save(qr_path)
    return qr_path

def fetch_data_supabase():
    if supabase is None:
        return pd.DataFrame()
    try:
        response = supabase.table("hibah").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

df_global = fetch_data_supabase()
total_data = len(df_global) if not df_global.empty else 0
total_unit = int(df_global["jumlah"].sum()) if not df_global.empty and "jumlah" in df_global else 0

st.markdown("""
    <div class='main-header'>
        <h1 style='margin:0; font-size: 32px;'>🚜 🌱 SIDAHTRA</h1>
        <h3 style='margin:5px 0; font-size: 18px; font-weight: 500;'>Sistem Data Hibah Alsintan Terpadu + QR Code & Supabase</h3>
    </div>
""", unsafe_allow_html=True)

menu = st.tabs(["📊 Dashboard", "📥 Input Baru", "📋 Rekap & Galeri", "🖨️ Cetak", "✏️ Edit", "📤 Impor/Hapus"])

with menu[0]:
    st.subheader("Ringkasan Data SIDAHTRA")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Total Data: {total_data}")
    with c2:
        st.markdown(f"### Total Unit: {total_unit}")

with menu[1]:
    st.subheader("Formulir Input Data Hibah Alsintan + QR Code")
    with st.form("form_sidahtra", clear_on_submit=True):
        asal_usul = st.selectbox("Asal Usul Hibah", ["APBD Kabupaten", "APBD Provinsi", "APBN Pusat", "Lainnya"])
        tahun_hibah = st.text_input("Tahun Hibah", value=str(datetime.now().year))
        jenis_barang = st.text_input("Nama/Jenis Alsintan (Contoh: Traktor R4, Pompa Air)")
        no_rangka = st.text_input("Nomor Rangka Alsintan")
        no_mesin = st.text_input("Nomor Mesin Alsintan")
        jumlah = st.number_input("Jumlah Barang (Unit)", min_value=1, value=1)
        harga_satuan_input = st.text_input("Harga Satuan (Rp) *Opsional*", value="0")
        
        st.markdown("---")
        kelompok = st.text_input("Kelompok Penerima Hibah (Poktan/Gapoktan)")
        nama_ketua = st.text_input("Nama Ketua Kelompok")
        nik = st.text_input("NIK Ketua / Penerima (16 Digit)")
        kecamatan = st.text_input("Kecamatan")
        desa = st.text_input("Desa / Kelurahan")
        alamat = st.text_area("Detail Alamat / Lokasi")
        titik_gps = st.text_input("Titik Lokasi GPS (Contoh: -2.3456, 112.4567)")
        
        submit = st.form_submit_button("Simpan Data ke Supabase & Buat QR")
        
        if submit:
            if kelompok and jenis_barang:
                try:
                    harga_satuan = float(harga_satuan_input) if harga_satuan_input.strip() != "" else 0.0
                except ValueError:
                    harga_satuan = 0.0

                if supabase:
                    try:
                        insert_data = {
                            "asal_usul": asal_usul,
                            "tahun_hibah": tahun_hibah,
                            "jenis_barang": jenis_barang,
                            "no_rangka": no_rangka,
                            "no_mesin": no_mesin,
                            "jumlah": int(jumlah),
                            "harga_satuan": float(harga_satuan),
                            "kelompok": kelompok,
                            "nama_ketua": nama_ketua,
                            "nik": str(nik),
                            "kecamatan": kecamatan,
                            "desa": desa,
                            "alamat": alamat,
                            "titik_gps": titik_gps,
                            "foto_path": "",
                            "proposal_path": "",
                            "bast_path": "",
                            "qr_path": ""
                        }
                        
                        # Eksekusi insert langsung
                        res = supabase.table("hibah").insert(insert_data).execute()
                        
                        if res.data:
                            new_id = res.data[0]['id']
                            qr_path = generate_qr_code(new_id, kelompok, jenis_barang, kecamatan)
                            supabase.table("hibah").update({"qr_path": qr_path}).eq("id", new_id).execute()
                            st.success(f"Berhasil! Data tersimpan dengan ID ID #{new_id}")
                        else:
                            st.warning("Perintah insert berhasil dikirim, tetapi data tidak mengembalikan respons.")
                    except Exception as e:
                        st.error(f"Gagal Menyimpan ke Supabase. Detail Error: {str(e)}")
                else:
                    st.error("Koneksi Supabase tidak aktif.")
            else:
                st.error("Mohon isi minimal 'Kelompok' dan 'Jenis Barang'!")

with menu[2]:
    st.subheader("📋 Rekapitulasi Data")
    df = fetch_data_supabase()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada data di dalam tabel hibah.")

with menu[3]:
    st.subheader("🖨️ Cetak & Download")
    df = fetch_data_supabase()
    if not df.empty:
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SIDAHTRA')
        st.download_button("📥 Download Excel", output_excel.getvalue(), "laporan_sidahtra.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("Data kosong untuk didownload.")

with menu[4]:
    st.subheader("✏️ Edit Data")
    st.info("Silakan cek menu Rekap untuk melihat data.")

with menu[5]:
    st.subheader("📤 Hapus Data")
    st.info("Silakan cek menu Rekap untuk melihat data.")
