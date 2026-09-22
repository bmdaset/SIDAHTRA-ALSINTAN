import streamlit as st
import pandas as pd
import qrcode
import os
from supabase import create_client, Client

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SIDAHTRA - Sistem Data Hibah Alsintan Terpadu",
    page_icon="🚜",
    layout="wide"
)

# --- KONEKSI SUPABASE (DISEMATKAN LANGSUNG) ---
SUPABASE_URL = "https://kfbsbhsztfruhdqjydqs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtmYnNiaHN6dGZydWhkcWp5ZHFzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk2NTM0NzIsImV4cCI6MjEwNTIyOTQ3Mn0.jEvSj_2gKTEmhRyR1IzjXCNPXOMIqafs_M4tq82QNUE"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

# Direktori penyimpanan QR Code
UPLOAD_DIR = "assets"
os.makedirs(os.path.join(UPLOAD_DIR, "qrcode"), exist_ok=True)

# --- STYLING CSS ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1E4620 0%, #2E7D32 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    @media screen and (max-width: 768px) {
        .main-header h1 { font-size: 22px !important; }
        .main-header p { font-size: 13px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI GENERATE QR CODE ---
def generate_qr_code(identifier, kelompok, jenis, kecamatan):
    qr_data = f"SIDAHTRA ASSET\nIdentitas/No: {identifier}\nKelompok: {kelompok}\nBarang: {jenis}\nKecamatan: {kecamatan}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    safe_name = str(identifier).replace("/", "_")
    qr_path = os.path.join(UPLOAD_DIR, "qrcode", f"qr_asset_{safe_name}.png")
    img.save(qr_path)
    return qr_path

# --- AMBIL DATA DARI SUPABASE ---
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
total_kategori = df_global['asal_usul'].nunique() if not df_global.empty and "asal_usul" in df_global else 0
total_nilai = int((df_global["jumlah"] * df_global["harga_satuan"]).sum()) if not df_global.empty and "jumlah" in df_global and "harga_satuan" in df_global else 0

# --- HEADER APLIKASI ---
st.markdown("""
<div class='main-header'>
    <h1 style='margin:0; font-size: 32px;'>🚜 🌱 SIDAHTRA</h1>
    <h3 style='margin:5px 0 5px 0; font-size: 18px; font-weight: 500;'>Sistem Data Hibah Alsintan Terpadu + QR Code & Supabase</h3>
    <p style='margin:0; opacity: 0.9; font-size: 14px;'>Pendataan, Monitoring, dan Pelabelan QR Code Alsintan Berbasis Cloud</p>
</div>
""", unsafe_allow_html=True)

# --- NAVIGASI TAB ---
menu = st.tabs(["📊 Dashboard", "📥 Input Baru", "📋 Rekap & Galeri", "🖨️ Cetak", "✏️ Edit", "📤 Impor/Hapus"])

# ==================== TAB 0: DASHBOARD ====================
with menu[0]:
    st.subheader("Ringkasan Data SIDAHTRA")
    st.markdown("<p style='color: #4A6B52;'>Statistik cepat data hibah alsintan terpadu.</p>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Data", total_data)
    c2.metric("Total Unit", total_unit)
    c3.metric("Asal Usul", total_kategori)
    c4.metric("Estimasi Nilai", f"Rp {total_nilai:,.0f}")

# ==================== TAB 1: INPUT BARU ====================
with menu[1]:
    st.subheader("Input Data Bantuan Alsintan Baru")
    with st.form("form_input_alsintan"):
        col_1, col_2 = st.columns(2)
        with col_1:
            nama_kelompok = st.text_input("Nama Kelompok Tani / P3A / UPJA")
            nama_ketua = st.text_input("Nama Ketua Kelompok")
            nik_ketua = st.text_input("NIK Ketua Kelompok", placeholder="16 digit NIK")
            no_hp = st.text_input("Nomor HP / WhatsApp")
            jenis_alsintan = st.text_input("Jenis Alsintan", placeholder="Contoh: Traktor Roda 4 / Pompa Air")
            no_rangka = st.text_input("Nomor Rangka", placeholder="Masukkan Nomor Rangka")
            no_mesin = st.text_input("Nomor Mesin", placeholder="Masukkan Nomor Mesin")
        with col_2:
            jumlah = st.number_input("Jumlah Unit", min_value=1, value=1)
            harga_satuan = st.number_input("Harga Satuan (Rp)", min_value=0, value=0, step=100000)
            asal_usul = st.selectbox("Asal Usul / Sumber Anggaran", ["APBN", "APBD Prov", "APBD Kab", "Hibah Lainnya"])
            kecamatan = st.text_input("Kecamatan")
            tahun = st.selectbox("Tahun Anggaran", [2026, 2025, 2024, 2023, 2022])
            link_proposal = st.text_input("Link Proposal (Google Drive)", placeholder="https://drive.google.com/...")
            link_bast = st.text_input("Link BAST (Google Drive)", placeholder="https://drive.google.com/...")
        
        submitted = st.form_submit_button("Simpan Data ke Supabase & Buat QR")
        if submitted:
            if not nama_kelompok or not jenis_alsintan:
                st.warning("Mohon lengkapi Nama Kelompok dan Jenis Alsintan!")
            elif supabase is None:
                st.error("Koneksi Supabase belum terinisialisasi.")
            else:
                try:
                    # Menggunakan no_rangka atau nama kelompok sebagai acuan QR jika id_bantuan tidak ada
                    qr_identifier = no_rangka if no_rangka else nama_kelompok
                    qr_path = generate_qr_code(qr_identifier, nama_kelompok, jenis_alsintan, kecamatan)
                    
                    data_to_insert = {
                        "nama_kelompok": nama_kelompok,
                        "nama_ketua": nama_ketua,
                        "nik_ketua": nik_ketua,
                        "no_hp": no_hp,
                        "jenis_alsintan": jenis_alsintan,
                        "no_rangka": no_rangka,
                        "no_mesin": no_mesin,
                        "jumlah": int(jumlah),
                        "harga_satuan": float(harga_satuan),
                        "asal_usul": asal_usul,
                        "kecamatan": kecamatan,
                        "tahun": int(tahun),
                        "link_proposal": link_proposal,
                        "link_bast": link_bast,
                        "qr_path": qr_path
                    }
                    supabase.table("hibah").insert(data_to_insert).execute()
                    st.success("Data berhasil disimpan ke Supabase dan QR Code berhasil dibuat!")
                    st.balloons()
                except Exception as ex:
                    st.error(f"Terjadi kesalahan saat menyimpan ke Supabase: {ex}")

# ==================== TAB 2: REKAP & GALERI ====================
with menu[2]:
    st.subheader("Rekapitulasi dan Galeri Alsintan")
    if df_global.empty:
        st.info("Belum ada data tersimpan di database Supabase.")
    else:
        st.dataframe(df_global, use_container_width=True)

# ==================== TAB 3: CETAK ====================
with menu[3]:
    st.subheader("Cetak Label & QR Code")
    if df_global.empty:
        st.info("Data belum tersedia untuk dicetak.")
    else:
        # Menggunakan kolom no_rangka atau indeks baris sebagai pilihan cetak
        display_col = "no_rangka" if "no_rangka" in df_global.columns and df_global["no_rangka"].notna().any() else df_global.columns[0]
        selected_item = st.selectbox("Pilih Berdasarkan No. Rangka / Data", df_global[display_col].tolist())
        row_data = df_global[df_global[display_col] == selected_item].iloc[0]
        
        st.write(f"**Kelompok:** {row_data.get('nama_kelompok')}")
        st.write(f"**Ketua:** {row_data.get('nama_ketua', '-')}")
        st.write(f"**Jenis:** {row_data.get('jenis_alsintan')}")
        st.write(f"**No. Rangka:** {row_data.get('no_rangka', '-')}")
        st.write(f"**No. Mesin:** {row_data.get('no_mesin', '-')}")
        
        if row_data.get('link_proposal'):
            st.markdown(f"📄 [Buka Proposal di Google Drive]({row_data.get('link_proposal')})")
        if row_data.get('link_bast'):
            st.markdown(f"📋 [Buka Berita Acara (BAST) di Google Drive]({row_data.get('link_bast')})")
            
        qr_file = row_data.get('qr_path')
        if qr_file and os.path.exists(qr_file):
            st.image(qr_file, width=200, caption=f"QR Code: {selected_item}")
        else:
            st.warning("File QR Code belum tergenerate untuk data ini.")

# ==================== TAB 4: EDIT ====================
with menu[4]:
    st.subheader("Edit Data Bantuan")
    if df_global.empty:
        st.info("Tidak ada data untuk diedit.")
    else:
        display_col = "no_rangka" if "no_rangka" in df_global.columns and df_global["no_rangka"].notna().any() else df_global.columns[0]
        edit_val = st.selectbox("Pilih Data yang ingin diedit", df_global[display_col].tolist(), key="edit_select")
        target_row = df_global[df_global[display_col] == edit_val].iloc[0]
        with st.form("form_edit"):
            new_kelompok = st.text_input("Nama Kelompok", value=str(target_row.get("nama_kelompok", "")))
            new_ketua = st.text_input("Nama Ketua", value=str(target_row.get("nama_ketua", "")))
            new_proposal = st.text_input("Link Proposal", value=str(target_row.get("link_proposal", "")))
            new_bast = st.text_input("Link BAST", value=str(target_row.get("link_bast", "")))
            update_btn = st.form_submit_button("Perbarui Data")
            if update_btn:
                try:
                    supabase.table("hibah").update({
                        "nama_kelompok": new_kelompok,
                        "nama_ketua": new_ketua,
                        "link_proposal": new_proposal,
                        "link_bast": new_bast
                    }).eq(display_col, edit_val).execute()
                    st.success("Data berhasil diperbarui!")
                except Exception as ex:
                    st.error(f"Gagal memperbarui: {ex}")

# ==================== TAB 5: IMPOR/HAPUS ====================
with menu[5]:
    st.subheader("Manajemen Data & Hapus")
    if df_global.empty:
        st.info("Database kosong.")
    else:
        display_col = "no_rangka" if "no_rangka" in df_global.columns and df_global["no_rangka"].notna().any() else df_global.columns[0]
        del_val = st.selectbox("Pilih Data yang akan Dihapus", df_global[display_col].tolist(), key="del_select")
        if st.button("Hapus Data Terpilih", type="primary"):
            try:
                supabase.table("hibah").delete().eq(display_col, del_val).execute()
                st.success("Data berhasil dihapus!")
            except Exception as ex:
                st.error(f"Gagal menghapus: {ex}")
