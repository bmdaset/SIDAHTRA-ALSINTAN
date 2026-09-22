import os
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import qrcode
from supabase import create_client, Client

# --- KREDENSIAL SUPABASE (Sila pastikan SUPABASE_KEY disalin lengkap dari Dashboard Supabase Anda) ---
SUPABASE_URL = "https://kfbsbhsztfruhdqjydqs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtmYnNiaHN6dGZydWhkcWp5ZHFzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk2NTM0NzIsImV4cCI6MjEwNTIyOTQ3Mn0.jEvSj_2gKTEmhRyR1IzjXCNPXOMIqafs_M4tq82QNUE"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase: Client = init_supabase()

# Konfigurasi Direktori Penyimpanan Lokal Berkas Sementara
UPLOAD_DIR = "sidahtra_files"
os.makedirs(os.path.join(UPLOAD_DIR, "foto"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "proposal"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "bast"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "qrcode"), exist_ok=True)

# Konfigurasi Halaman (Wide Layout)
st.set_page_config(page_title="SIDAHTRA - Sistem Data Hibah Alsintan Terpadu", layout="wide")

# CSS Kustom: Tema Hijau Tanaman & Responsif untuk HP (Mobile-Friendly)
st.markdown("""
    <style>
        .stApp {
            background-color: #F3F7F4;
        }
        .main-header {
            background: linear-gradient(rgba(19, 56, 32, 0.85), rgba(42, 111, 55, 0.85)), 
                        url('https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=1200&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            padding: 35px 20px;
            border-radius: 14px;
            color: white;
            box-shadow: 0 4px 15px rgba(19, 56, 32, 0.2);
            margin-bottom: 25px;
            text-align: center;
        }
        .metric-card-1 {
            background: linear-gradient(135deg, #133820 0%, #1E4D2B 100%);
            color: white; padding: 18px; border-radius: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .metric-card-2 {
            background: linear-gradient(135deg, #2A6F37 0%, #388E3C 100%);
            color: white; padding: 18px; border-radius: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .metric-card-3 {
            background: linear-gradient(135deg, #43A047 0%, #66BB6A 100%);
            color: white; padding: 18px; border-radius: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .metric-card-4 {
            background: linear-gradient(135deg, #2E7D32 0%, #81C784 100%);
            color: white; padding: 18px; border-radius: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .stButton>button {
            background-color: #2A6F37; color: white; border-radius: 8px; border: none; font-weight: 600; padding: 0.5rem 1rem; width: 100%;
        }
        .stButton>button:hover {
            background-color: #133820; color: white;
        }
        @media screen and (max-width: 768px) {
            .main-header h1 { font-size: 22px !important; }
            .main-header p { font-size: 13px !important; }
        }
    </style>
""", unsafe_allow_html=True)

# Fungsi Generate QR Code Otomatis
def generate_qr_code(data_id, kelompok, jenis, kecamatan):
    qr_data = f"SIDAHTRA ASSET\nID: {data_id}\nKelompok: {kelompok}\nBarang: {jenis}\nKecamatan: {kecamatan}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    qr_path = os.path.join(UPLOAD_DIR, "qrcode", f"qr_asset_{data_id}.png")
    img.save(qr_path)
    return qr_path

# Fungsi Otomatis Mencari Gambar Berdasarkan Jenis Barang
def get_gambar_alsintan(jenis_barang):
    jenis = str(jenis_barang).lower()
    if "traktor r4" in jenis or "roda 4" in jenis or "r4" in jenis:
        return "https://images.unsplash.com/photo-1595974482597-4f6c4f2c224e?q=80&w=300&auto=format&fit=crop"
    elif "traktor" in jenis or "hand traktor" in jenis or "cultivator" in jenis or "rotari" in jenis:
        return "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?q=80&w=300&auto=format&fit=crop"
    elif "pompa" in jenis or "air" in jenis:
        return "https://images.unsplash.com/photo-1563514227147-6d2ff665a6a0?q=80&w=300&auto=format&fit=crop"
    elif "combine" in jenis or "panen" in jenis or "harvester" in jenis:
        return "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?q=80&w=300&auto=format&fit=crop"
    elif "sprayer" in jenis or "siram" in jenis or "semprot" in jenis:
        return "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?q=80&w=300&auto=format&fit=crop"
    elif "rice" in jenis or "milling" in jenis or "penggiling" in jenis:
        return "https://images.unsplash.com/photo-1574943320219-553eb213f72d?q=80&w=300&auto=format&fit=crop"
    else:
        return "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=300&auto=format&fit=crop"

# Ambil data global dari Supabase untuk ringkasan
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
menu = st.tabs([
    "📊 Dashboard", 
    "📥 Input Baru", 
    "📋 Rekap & Galeri", 
    "🖨️ Cetak", 
    "✏️ Edit", 
    "📤 Impor/Hapus"
])

# ==================== TAB 0: DASHBOARD ====================
with menu[0]:
    st.subheader("Ringkasan Data SIDAHTRA")
    st.markdown("<p style='color: #4A6B52;'>Statistik cepat data hibah alsintan beserta ilustrasi otomatis per jenis barang.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
            <div class='metric-card-1'>
                <p style='margin: 0; font-size: 13px; opacity: 0.8;'>Total Data Masuk</p>
                <h2 style='margin: 5px 0 0 0;'>{total_data}</h2>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <div class='metric-card-3'>
                <p style='margin: 0; font-size: 13px; opacity: 0.8;'>Kategori Asal Usul</p>
                <h2 style='margin: 5px 0 0 0;'>{total_kategori}</h2>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class='metric-card-2'>
                <p style='margin: 0; font-size: 13px; opacity: 0.8;'>Total Unit Alsintan</p>
                <h2 style='margin: 5px 0 0 0;'>{total_unit}</h2>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <div class='metric-card-4'>
                <p style='margin: 0; font-size: 13px; opacity: 0.8;'>Total Estimasi Nilai</p>
                <h2 style='margin: 5px 0 0 0; font-size: 20px;'>Rp {total_nilai:,}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>### 🌾 5 Data Hibah Terbaru", unsafe_allow_html=True)
    if not df_global.empty:
        df_latest = df_global.tail(5).copy()
        for idx, row in df_latest.iterrows():
            col_img, col_txt = st.columns([1, 3])
            with col_img:
                if row.get('foto_path') and os.path.exists(row['foto_path']):
                    st.image(row['foto_path'], width=130, caption="Foto Asli Unit")
                else:
                    auto_img_url = get_gambar_alsintan(row.get('jenis_barang', ''))
                    st.image(auto_img_url, width=130, caption=f"Ilustrasi: {row.get('jenis_barang', '')}")
            with col_txt:
                st.markdown(f"**Kelompok:** {row.get('kelompok', '-')}")
                st.markdown(f"**Jenis Alsintan:** {row.get('jenis_barang', '-')} (**{row.get('jumlah', 0)} Unit**)")
                st.markdown(f"**Lokasi:** Desa {row.get('desa', '-')}, Kec. {row.get('kecamatan', '-')}")
                st.markdown(f"**Asal Usul:** {row.get('asal_usul', '-')} ({row.get('tahun_hibah', '-')})")
            st.markdown("---")
    else:
        st.info("Belum ada data hibah tersimpan atau koneksi Supabase belum dikonfigurasi.")

# ==================== TAB 1: INPUT DATA BARU ====================
with menu[1]:
    st.subheader("Formulir Input Data Hibah Alsintan + QR Code")
    st.markdown("<p style='font-size: 13px; color: #666;'>Data akan otomatis tersimpan ke Supabase dan dibuatkan QR Code aset.</p>", unsafe_allow_html=True)
    
    with st.form("form_sidahtra", clear_on_submit=True):
        asal_usul = st.selectbox("Asal Usul Hibah", ["APBD Kabupaten", "APBD Provinsi", "APBN Pusat", "Lainnya"])
        tahun_hibah = st.text_input("Tahun Hibah", value=str(datetime.now().year))
        jenis_barang = st.text_input("Nama/Jenis Alsintan (Contoh: Traktor R4, Pompa Air, Cultivator)")
        no_rangka = st.text_input("Nomor Rangka Alsintan")
        no_mesin = st.text_input("Nomor Mesin Alsintan")
        jumlah = st.number_input("Jumlah Barang (Unit)", min_value=1, value=1)
        harga_satuan_input = st.text_input("Harga Satuan (Rp) *Opsional*", value="")
        
        st.markdown("---")
        kelompok = st.text_input("Kelompok Penerima Hibah (Poktan/Gapoktan)")
        nama_ketua = st.text_input("Nama Ketua Kelompok")
        nik = st.text_input("NIK Ketua / Penerima (16 Digit)")
        kecamatan = st.text_input("Kecamatan")
        desa = st.text_input("Desa / Kelurahan")
        alamat = st.text_area("Detail Alamat / Lokasi")
        titik_gps = st.text_input("Titik Lokasi GPS (Contoh: -2.3456, 112.4567)")
        
        st.markdown("---")
        foto_file = st.file_uploader("Upload Foto Barang / Lokasi (Opsional)", type=["jpg", "png", "jpeg"])
        proposal_file = st.file_uploader("Upload Proposal Usulan (PDF/Word)", type=["pdf", "docx", "doc"])
        bast_file = st.file_uploader("Upload Bukti BAST (PDF/Word/Scan)", type=["pdf", "docx", "doc", "jpg", "png"])
            
        submit = st.form_submit_button("Simpan Data ke Supabase & Buat QR")
        
        if submit:
            if kelompok and jenis_barang:
                try:
                    harga_satuan = float(harga_satuan_input) if harga_satuan_input.strip() != "" else 0.0
                except ValueError:
                    harga_satuan = 0.0

                foto_path = ""
                if foto_file is not None:
                    foto_path = os.path.join(UPLOAD_DIR, "foto", foto_file.name)
                    with open(foto_path, "wb") as f: f.write(foto_file.getbuffer())
                
                proposal_path = ""
                if proposal_file is not None:
                    proposal_path = os.path.join(UPLOAD_DIR, "proposal", proposal_file.name)
                    with open(proposal_path, "wb") as f: f.write(proposal_file.getbuffer())
                
                path_bast = ""
                if bast_file is not None:
                    path_bast = os.path.join(UPLOAD_DIR, "bast", bast_file.name)
                    with open(path_bast, "wb") as f: f.write(bast_file.getbuffer())
                
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
                            "nik": nik,
                            "kecamatan": kecamatan,
                            "desa": desa,
                            "alamat": alamat,
                            "titik_gps": titik_gps,
                            "foto_path": foto_path,
                            "proposal_path": proposal_path,
                            "bast_path": path_bast,
                            "qr_path": ""
                        }
                        res = supabase.table("hibah").insert(insert_data).execute()
                        
                        if res.data:
                            new_id = res.data[0]['id']
                            qr_path = generate_qr_code(new_id, kelompok, jenis_barang, kecamatan)
                            supabase.table("hibah").update({"qr_path": qr_path}).eq("id", new_id).execute()
                            st.success(f"Data berhasil disimpan ke Supabase & QR Code ID #{new_id} berhasil dibuat!")
                        else:
                            st.error("Gagal menyimpan data ke Supabase.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan koneksi Supabase: {e}")
                else:
                    st.error("Koneksi Supabase belum diatur dengan benar.")
            else:
                st.error("Mohon lengkapi Nama Kelompok dan Jenis Barang!")

# ==================== TAB 2: REKAPITULASI & GALERI ====================
with menu[2]:
    st.subheader("📋 Rekapitulasi, Galeri & QR Code Asset")
    
    col_btn, col_search = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    with col_search:
        search_query = st.text_input("🔍 Cari Data (Kelompok, Jenis, Kecamatan, atau Desa):", "")
            
    df = fetch_data_supabase()
    
    if not df.empty:
        if search_query.strip() != "":
            mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
            df = df[mask]
        
        st.info(f"💡 Menampilkan {len(df)} data bantuan alsintan dari Supabase.")
        st.markdown("---")
        
        if df.empty:
            st.warning("Tidak ditemukan data yang sesuai.")
        else:
            for idx, row in df.iterrows():
                col_img, col_qr, col_info = st.columns([1, 1, 2])
                with col_img:
                    if row.get('foto_path') and os.path.exists(row['foto_path']):
                        st.image(row['foto_path'], width=120, caption=f"ID: {row.get('id')}")
                    else:
                        auto_img_url = get_gambar_alsintan(row.get('jenis_barang', ''))
                        st.image(auto_img_url, width=120, caption=f"Ilustrasi")
                with col_qr:
                    qr_file = row.get('qr_path', '')
                    if qr_file and os.path.exists(qr_file):
                        st.image(qr_file, width=120, caption=f"QR Code Asset")
                        with open(qr_file, "rb") as file:
                            st.download_button(
                                label="📥 Download QR",
                                data=file,
                                file_name=f"qr_asset_{row.get('id')}.png",
                                mime="image/png",
                                key=f"dl_qr_{row.get('id')}"
                            )
                    else:
                        st.warning("QR belum ada")
                with col_info:
                    st.markdown(f"### {row.get('kelompok', '-')}")
                    st.markdown(f"**Jenis Alsintan:** {row.get('jenis_barang', '-')} (**{row.get('jumlah', 0)} Unit**)")
                    st.markdown(f"**Asal Usul:** {row.get('asal_usul', '-')} ({row.get('tahun_hibah', '-')})")
                    st.markdown(f"**Ketua / NIK:** {row.get('nama_ketua', '-')} / {row.get('nik', '-')}")
                    st.markdown(f"**Lokasi:** Desa {row.get('desa', '-')}, Kec. {row.get('kecamatan', '-')}")
                st.markdown("---")
    else:
        st.warning("Belum ada data di Supabase.")

# ==================== TAB 3: CETAK & DOWNLOAD ====================
with menu[3]:
    st.subheader("🖨️ Cetak & Download Laporan")
    df = fetch_data_supabase()
    
    if not df.empty:
        df["Total Harga (Rp)"] = df["jumlah"] * df["harga_satuan"]
        opsi_asal = df["asal_usul"].dropna().unique().tolist() if "asal_usul" in df else []
        
        if opsi_asal:
            kategori_pilih = st.selectbox("Pilih Kategori Asal Usul Hibah:", opsi_asal)
            st.markdown("---")
            df_filtered = df[df["asal_usul"] == kategori_pilih].copy()
            
            if not df_filtered.empty:
                df_filtered.index = range(1, len(df_filtered) + 1)
                df_filtered.index.name = "No"
                
                st.dataframe(df_filtered.drop(columns=['foto_path', 'proposal_path', 'bast_path', 'qr_path'], errors='ignore'), use_container_width=True)
                
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_filtered.to_excel(writer, index=True, sheet_name='SIDAHTRA')
                st.download_button("📥 Download Laporan Excel", output_excel.getvalue(), f"sidahtra_{kategori_pilih.lower()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.warning("Tidak ada data pada kategori ini.")
    else:
        st.warning("Belum ada data.")

# ==================== TAB 4: EDIT & UPLOAD BERKAS ====================
with menu[4]:
    st.subheader("✏️ Edit Data & Berkas")
    df_db = fetch_data_supabase()
    
    if not df_db.empty:
        id_pilih = st.selectbox("Pilih ID Data yang Ingin Diedit:", df_db["id"].tolist())
        
        if id_pilih:
            data_row = df_db[df_db["id"] == id_pilih].iloc[0]
            
            with st.form("form_edit_berkas"):
                st.markdown(f"### Edit Data ID: **{id_pilih}**")
                edit_asal = st.selectbox("Asal Usul Hibah", ["APBD Kabupaten", "APBD Provinsi", "APBN Pusat", "Lainnya"], index=0)
                edit_tahun = st.text_input("Tahun Hibah", value=str(data_row.get('tahun_hibah', '')))
                edit_barang = st.text_input("Nama/Jenis Alsintan", value=str(data_row.get('jenis_barang', '')))
                edit_jumlah = st.number_input("Jumlah Barang", min_value=1, value=int(data_row.get('jumlah', 1)))
                edit_harga = st.text_input("Harga Satuan", value=str(data_row.get('harga_satuan', '')))
                edit_kelompok = st.text_input("Kelompok Penerima", value=str(data_row.get('kelompok', '')))
                edit_ketua = st.text_input("Nama Ketua", value=str(data_row.get('nama_ketua', '')))
                edit_kec = st.text_input("Kecamatan", value=str(data_row.get('kecamatan', '')))
                edit_desa = st.text_input("Desa", value=str(data_row.get('desa', '')))
                
                submit_update = st.form_submit_button("Simpan Perubahan ke Supabase")
                if submit_update:
                    harga_val = float(edit_harga) if edit_harga.strip() != "" else 0.0
                    update_data = {
                        "asal_usul": edit_asal,
                        "tahun_hibah": edit_tahun,
                        "jenis_barang": edit_barang,
                        "jumlah": int(edit_jumlah),
                        "harga_satuan": harga_val,
                        "kelompok": edit_kelompok,
                        "nama_ketua": edit_ketua,
                        "kecamatan": edit_kec,
                        "desa": edit_desa
                    }
                    supabase.table("hibah").update(update_data).eq("id", id_pilih).execute()
                    
                    new_qr = generate_qr_code(id_pilih, edit_kelompok, edit_barang, edit_kec)
                    supabase.table("hibah").update({"qr_path": new_qr}).eq("id", id_pilih).execute()
                    
                    st.success("Data berhasil diperbarui di Supabase!")
                    st.rerun()
    else:
        st.info("Belum ada data untuk diedit.")

# ==================== TAB 5: IMPOR / HAPUS ====================
with menu[5]:
    st.subheader("📤 Impor & Hapus Data")
    
    st.markdown("### 1. Download Template Kosong")
    template_df = pd.DataFrame(columns=["asal_usul", "tahun_hibah", "jenis_barang", "no_rangka", "no_mesin", "jumlah", "harga_satuan", "kelompok", "nama_ketua", "nik", "kecamatan", "desa", "alamat", "titik_gps"])
    output_template = io.BytesIO()
    with pd.ExcelWriter(output_template, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Template SIDAHTRA')
    st.download_button("📥 Download Template Excel", output_template.getvalue(), "template_sidahtra.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    
    st.markdown("---")
    st.subheader("2. Hapus Data dari Supabase")
    df_db = fetch_data_supabase()
    if not df_db.empty:
        st.dataframe(df_db[['id', 'kelompok', 'jenis_barang', 'kecamatan']], use_container_width=True)
        id_dihapus = st.selectbox("Pilih ID untuk dihapus:", df_db["id"].tolist())
        if st.button("🗑️ Hapus Data Terpilih", type="primary"):
            supabase.table("hibah").delete().eq("id", id_dihapus).execute()
            st.success("Data berhasil dihapus dari Supabase!")
            st.rerun()
    else:
        st.info("Tidak ada data untuk dihapus.")
