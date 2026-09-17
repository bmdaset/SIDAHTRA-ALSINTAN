import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import io

# Library tambahan untuk export Word & PDF
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Konfigurasi Direktori Penyimpanan Lokal Berkas
UPLOAD_DIR = "sidahtra_files"
os.makedirs(os.path.join(UPLOAD_DIR, "foto"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "proposal"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "bast"), exist_ok=True)

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

# Inisialisasi Database
def init_db():
    conn = sqlite3.connect("sidahtra_pertanian.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hibah (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asal_usul TEXT,
            tahun_hibah TEXT,
            jenis_barang TEXT,
            no_rangka TEXT,
            no_mesin TEXT,
            jumlah INTEGER,
            harga_satuan REAL,
            kelompok TEXT,
            nama_ketua TEXT,
            nik TEXT,
            kecamatan TEXT,
            desa TEXT,
            alamat TEXT,
            titik_gps TEXT,
            foto_path TEXT,
            proposal_path TEXT,
            bast_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Ambil data global untuk ringkasan
conn = sqlite3.connect("sidahtra_pertanian.db")
df_global = pd.read_sql_query("SELECT * FROM hibah", conn)
conn.close()

total_data = len(df_global)
total_unit = int(df_global["jumlah"].sum()) if not df_global.empty else 0
total_kategori = df_global['asal_usul'].nunique() if not df_global.empty else 0
total_nilai = int((df_global["jumlah"] * df_global["harga_satuan"]).sum()) if not df_global.empty else 0

# --- HEADER APLIKASI ---
st.markdown("""
    <div class='main-header'>
        <h1 style='margin:0; font-size: 32px;'>🚜 🌱 SIDAHTRA</h1>
        <h3 style='margin:5px 0 5px 0; font-size: 18px; font-weight: 500;'>Sistem Data Hibah Alsintan Terpadu</h3>
        <p style='margin:0; opacity: 0.9; font-size: 14px;'>Pendataan, Monitoring, dan Pengelolaan Bantuan Alat & Mesin Pertanian</p>
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
                if row['foto_path'] and os.path.exists(row['foto_path']):
                    st.image(row['foto_path'], width=130, caption="Foto Asli Unit")
                else:
                    auto_img_url = get_gambar_alsintan(row['jenis_barang'])
                    st.image(auto_img_url, width=130, caption=f"Ilustrasi: {row['jenis_barang']}")
            with col_txt:
                st.markdown(f"**Kelompok:** {row['kelompok']}")
                st.markdown(f"**Jenis Alsintan:** {row['jenis_barang']} (**{row['jumlah']} Unit**)")
                st.markdown(f"**Lokasi:** Desa {row['desa']}, Kec. {row['kecamatan']}")
                st.markdown(f"**Asal Usul:** {row['asal_usul']} ({row['tahun_hibah']})")
            st.markdown("---")
    else:
        st.info("Belum ada data hibah tersimpan. Gunakan menu **Input Baru** untuk menambah data.")

# ==================== TAB 1: INPUT DATA BARU ====================
with menu[1]:
    st.subheader("Formulir Input Data Hibah Alsintan")
    st.markdown("<p style='font-size: 13px; color: #666;'>Formulir ini dirancang responsif agar mudah diisi baik melalui HP maupun komputer.</p>", unsafe_allow_html=True)
    
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
            
        submit = st.form_submit_button("Simpan Data SIDAHTRA")
        
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
                
                conn = sqlite3.connect("sidahtra_pertanian.db")
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO hibah (asal_usul, tahun_hibah, jenis_barang, no_rangka, no_mesin, jumlah, harga_satuan, kelompok, nama_ketua, nik, kecamatan, desa, alamat, titik_gps, foto_path, proposal_path, bast_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (asal_usul, tahun_hibah, jenis_barang, no_rangka, no_mesin, jumlah, harga_satuan, kelompok, nama_ketua, nik, kecamatan, desa, alamat, titik_gps, foto_path, proposal_path, path_bast))
                conn.commit()
                conn.close()
                
                st.success("Data hibah berhasil disimpan ke dalam sistem SIDAHTRA!")
            else:
                st.error("Mohon lengkapi Nama Kelompok dan Jenis Barang!")

# ==================== TAB 2: REKAPITULASI & GALERI ====================
with menu[2]:
    st.subheader("📋 Rekapitulasi & Galeri Foto Alsintan")
    
    col_btn, col_search = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    with col_search:
        search_query = st.text_input("🔍 Cari Data (Kelompok, Jenis, Kecamatan, atau Desa):", "")
            
    conn = sqlite3.connect("sidahtra_pertanian.db")
    df = pd.read_sql_query("SELECT * FROM hibah", conn)
    conn.close()
    
    if not df.empty:
        # Filter pencarian teks jika diisi
        if search_query.strip() != "":
            mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
            df = df[mask]
        
        st.info(f"💡 Menampilkan {len(df)} data bantuan alsintan beserta foto/ilustrasi dokumentasi.")
        st.markdown("---")
        
        if df.empty:
            st.warning("Tidak ditemukan data yang sesuai dengan kata kunci pencarian.")
        else:
            for idx, row in df.iterrows():
                col_img, col_info = st.columns([1, 3])
                with col_img:
                    if row['foto_path'] and os.path.exists(row['foto_path']):
                        st.image(row['foto_path'], width=140, caption=f"ID: {row['id']}")
                    else:
                        auto_img_url = get_gambar_alsintan(row['jenis_barang'])
                        st.image(auto_img_url, width=140, caption=f"Otomatis: {row['jenis_barang']}")
                with col_info:
                    st.markdown(f"### {row['kelompok']}")
                    st.markdown(f"**Jenis Alsintan:** {row['jenis_barang']} (**{row['jumlah']} Unit**)")
                    st.markdown(f"**Asal Usul:** {row['asal_usul']} ({row['tahun_hibah']})")
                    st.markdown(f"**Ketua / NIK:** {row['nama_ketua']} / {row['nik']}")
                    st.markdown(f"**Lokasi:** Desa {row['desa']}, Kec. {row['kecamatan']}")
                    st.markdown(f"**No. Rangka / Mesin:** {row['no_rangka'] or '-'} / {row['no_mesin'] or '-'}")
                st.markdown("---")
    else:
        st.warning("Belum ada data hibah yang tersimpan di dalam database.")

# ==================== TAB 3: CETAK & DOWNLOAD ====================
with menu[3]:
    st.subheader("🖨️ Cetak & Download Laporan")
    
    conn = sqlite3.connect("sidahtra_pertanian.db")
    df = pd.read_sql_query("SELECT * FROM hibah", conn)
    conn.close()
    
    if not df.empty:
        df["Total Harga (Rp)"] = df["jumlah"] * df["harga_satuan"]
        opsi_asal = df["asal_usul"].dropna().unique().tolist()
        
        kategori_pilih = st.selectbox("Pilih Kategori Asal Usul Hibah:", opsi_asal)
        st.markdown("---")
        
        df_filtered = df[df["asal_usul"] == kategori_pilih].copy()
        
        if not df_filtered.empty:
            df_filtered.index = range(1, len(df_filtered) + 1)
            df_filtered.index.name = "No"
            
            st.markdown(f"**Preview Laporan Kategori: {kategori_pilih.upper()}**")
            st.dataframe(df_filtered.drop(columns=['foto_path', 'proposal_path', 'bast_path']), use_container_width=True, height=350)
            
            st.markdown("#### 📥 Tombol Download Berkas")
            
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=True, sheet_name='SIDAHTRA')
            st.download_button("📥 Download Laporan Excel", output_excel.getvalue(), f"sidahtra_{kategori_pilih.lower()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
            doc = Document()
            doc.add_heading(f'Laporan SIDAHTRA - {kategori_pilih}', 0)
            for index, row in df_filtered.iterrows():
                doc.add_heading(f"No. {index} - Kelompok: {row['kelompok']}", level=2)
                doc.add_paragraph(f"Jenis: {row['jenis_barang']} (Jumlah: {row['jumlah']})\nKetua: {row['nama_ketua']}\nLokasi: Desa {row['desa']}, Kec. {row['kecamatan']}")
            output_word = io.BytesIO()
            doc.save(output_word)
            st.download_button("📥 Download Laporan Word", output_word.getvalue(), f"sidahtra_{kategori_pilih.lower()}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

            output_pdf = io.BytesIO()
            doc_pdf = SimpleDocTemplate(output_pdf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = [Paragraph(f"Laporan SIDAHTRA - {kategori_pilih}", styles['Heading1']), Spacer(1, 12)]
            table_data = [["No", "Kelompok", "Jenis Barang", "Kecamatan", "Jumlah"]]
            for idx, row in df_filtered.reset_index().iterrows():
                table_data.append([str(row['No']), str(row['kelompok']), str(row['jenis_barang']), str(row['kecamatan']), str(row['jumlah'])])
            t = Table(table_data, colWidths=[30, 150, 120, 100, 50])
            t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A6F37')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
            elements.append(t)
            doc_pdf.build(elements)
            st.download_button("📥 Download Laporan PDF", output_pdf.getvalue(), f"sidahtra_{kategori_pilih.lower()}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.warning("Tidak ada data ditemukan pada kategori ini.")
    else:
        st.warning("Belum ada data hibah yang tersimpan.")

# ==================== TAB 4: EDIT & UPLOAD BERKAS ====================
with menu[4]:
    st.subheader("✏️ Edit Data & Foto")
    
    conn = sqlite3.connect("sidahtra_pertanian.db")
    df_db = pd.read_sql_query("SELECT id, kelompok, jenis_barang, kecamatan, foto_path FROM hibah", conn)
    conn.close()
    
    if not df_db.empty:
        id_pilih = st.selectbox("Pilih ID Data yang Ingin Diedit:", df_db["id"].tolist())
        
        if id_pilih:
            conn = sqlite3.connect("sidahtra_pertanian.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hibah WHERE id = ?", (id_pilih,))
            data_row = cursor.fetchone()
            conn.close()
            
            if data_row:
                if data_row['foto_path'] and os.path.exists(data_row['foto_path']):
                    st.image(data_row['foto_path'], width=200, caption="Foto Saat Ini")
                
                with st.form("form_edit_berkas"):
                    st.markdown(f"### Edit Data ID: **{id_pilih}**")
                    asal_list = ["APBD Kabupaten", "APBD Provinsi", "APBN Pusat", "Lainnya"]
                    default_asal_idx = asal_list.index(data_row['asal_usul']) if data_row['asal_usul'] in asal_list else 0
                    edit_asal = st.selectbox("Asal Usul Hibah", asal_list, index=default_asal_idx)
                    edit_tahun = st.text_input("Tahun Hibah", value=str(data_row['tahun_hibah'] or ""))
                    edit_barang = st.text_input("Nama/Jenis Alsintan", value=str(data_row['jenis_barang'] or ""))
                    edit_jumlah = st.number_input("Jumlah Barang", min_value=1, value=int(data_row['jumlah'] or 1))
                    edit_harga = st.text_input("Harga Satuan", value=str(data_row['harga_satuan'] or ""))
                    edit_kelompok = st.text_input("Kelompok Penerima", value=str(data_row['kelompok'] or ""))
                    edit_ketua = st.text_input("Nama Ketua", value=str(data_row['nama_ketua'] or ""))
                    edit_kec = st.text_input("Kecamatan", value=str(data_row['kecamatan'] or ""))
                    edit_desa = st.text_input("Desa", value=str(data_row['desa'] or ""))
                    
                    st.markdown("---")
                    new_foto = st.file_uploader("Ganti Foto Alsintan Baru", type=["jpg", "png", "jpeg"])
                    new_proposal = st.file_uploader("Ganti Proposal Baru", type=["pdf", "docx", "doc"])
                    new_bast = st.file_uploader("Ganti BAST Baru", type=["pdf", "docx", "doc", "jpg", "png"])
                    
                    submit_update = st.form_submit_button("Simpan Perubahan")
                    if submit_update:
                        harga_val = float(edit_harga) if edit_harga.strip() != "" else 0.0
                        path_foto_final = data_row['foto_path']
                        if new_foto is not None:
                            path_foto_final = os.path.join(UPLOAD_DIR, "foto", new_foto.name)
                            with open(path_foto_final, "wb") as f: f.write(new_foto.getbuffer())
                        path_prop_final = data_row['proposal_path']
                        if new_proposal is not None:
                            path_prop_final = os.path.join(UPLOAD_DIR, "proposal", new_proposal.name)
                            with open(path_prop_final, "wb") as f: f.write(new_proposal.getbuffer())
                        path_bast_final = data_row['bast_path']
                        if new_bast is not None:
                            path_bast_final = os.path.join(UPLOAD_DIR, "bast", new_bast.name)
                            with open(path_bast_final, "wb") as f: f.write(new_bast.getbuffer())
                            
                        conn = sqlite3.connect("sidahtra_pertanian.db")
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE hibah SET asal_usul=?, tahun_hibah=?, jenis_barang=?, jumlah=?, harga_satuan=?, kelompok=?, nama_ketua=?, kecamatan=?, desa=?, foto_path=?, proposal_path=?, bast_path=? WHERE id=?
                        ''', (edit_asal, edit_tahun, edit_barang, edit_jumlah, harga_val, edit_kelompok, edit_ketua, edit_kec, edit_desa, path_foto_final, path_prop_final, path_bast_final, id_pilih))
                        conn.commit()
                        conn.close()
                        st.success("Data berhasil diperbarui!")
                        st.rerun()
    else:
        st.info("Belum ada data untuk diedit.")

# ==================== TAB 5: IMPOR / EKSPOR & HAPUS ====================
with menu[5]:
    st.subheader("📤 Impor Excel & Hapus Data")
    
    st.markdown("### 1. Download Template Kosong")
    template_df = pd.DataFrame(columns=["asal_usul", "tahun_hibah", "jenis_barang", "no_rangka", "no_mesin", "jumlah", "harga_satuan", "kelompok", "nama_ketua", "nik", "kecamatan", "desa", "alamat", "titik_gps"])
    output_template = io.BytesIO()
    with pd.ExcelWriter(output_template, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Template SIDAHTRA')
    st.download_button("📥 Download Template Excel", output_template.getvalue(), "template_sidahtra.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    
    st.markdown("---")
    st.subheader("2. Import Data dari Excel")
    uploaded_template = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
    if uploaded_template is not None:
        try:
            imported_df = pd.read_excel(uploaded_template)
            st.dataframe(imported_df, use_container_width=True)
            if st.button("Proses Impor Data"):
                conn = sqlite3.connect("sidahtra_pertanian.db")
                cursor = conn.cursor()
                for _, row in imported_df.iterrows():
                    cursor.execute('''
                        INSERT INTO hibah (asal_usul, tahun_hibah, jenis_barang, no_rangka, no_mesin, jumlah, harga_satuan, kelompok, nama_ketua, nik, kecamatan, desa, alamat, titik_gps, foto_path, proposal_path, bast_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '')
                    ''', (str(row.get('asal_usul','')), str(row.get('tahun_hibah','')), str(row.get('jenis_barang','')), str(row.get('no_rangka','')), str(row.get('no_mesin','')), int(row.get('jumlah',1)), float(row.get('harga_satuan',0)), str(row.get('kelompok','')), str(row.get('nama_ketua','')), str(row.get('nik','')), str(row.get('kecamatan','')), str(row.get('desa','')), str(row.get('alamat','')), str(row.get('titik_gps',''))))
                conn.commit()
                conn.close()
                st.success("Impor data berhasil!")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("3. Hapus Data")
    conn = sqlite3.connect("sidahtra_pertanian.db")
    df_db = pd.read_sql_query("SELECT id, kelompok, jenis_barang FROM hibah", conn)
    conn.close()
    if not df_db.empty:
        st.dataframe(df_db, use_container_width=True)
        id_dihapus = st.selectbox("Pilih ID untuk dihapus:", df_db["id"].tolist())
        if st.button("🗑️ Hapus Data Terpilih", type="primary"):
            conn = sqlite3.connect("sidahtra_pertanian.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hibah WHERE id = ?", (id_dihapus,))
            conn.commit()
            conn.close()
            st.success("Data berhasil dihapus!")
            st.rerun()
    else:
        st.info("Tidak ada data untuk dihapus.")