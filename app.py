import os
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
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

UPLOAD_DIR = "sidahtra_files"
os.makedirs(os.path.join(UPLOAD_DIR, "qrcode"), exist_ok=True)

st.set_page_config(page_title="SIDAHTRA - Sistem Data Hibah Alsintan Terpadu", layout="wide")

# --- CSS KUSTOM ---
st.markdown("""
    <style>
        .stApp { background-color: #F3F7F4; }
        .main-header {
            background: linear-gradient(rgba(19, 56, 32, 0.9), rgba(42, 111, 55, 0.9)), 
                        url('https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=1200&auto=format&fit=crop');
            background-size: cover; background-position: center;
            padding: 30px; border-radius: 12px; color: white; text-align: center; margin-bottom: 25px;
        }
        .stButton>button { background-color: #2A6F37; color: white; border-radius: 6px; font-weight: bold; width: 100%; }
        .stButton>button:hover { background-color: #133820; color: white; }
    </style>
""", unsafe_allow_html=True)

def fetch_data_supabase():
    if supabase is None:
        return pd.DataFrame()
    try:
        response = supabase.table("hibah").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty and "id" in df.columns:
            df = df.sort_values(by="id", ascending=True)
        return df
    except Exception as e:
        return pd.DataFrame()

def generate_qr_code(data_id, kelompok, jenis, kecamatan):
    qr_data = f"SIDAHTRA ASSET\nID: {data_id}\nKelompok: {kelompok}\nBarang: {jenis}\nKecamatan: {kecamatan}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    qr_path = os.path.join(UPLOAD_DIR, "qrcode", f"qr_asset_{data_id}.png")
    img.save(qr_path)
    return qr_path

def generate_pdf_report(df_filtered):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor('#133820'), alignment=1, spaceAfter=15
    )
    elements.append(Paragraph("LAPORAN REKAPITULASI HIBAH ALSINTAN (SIDAHTRA)", title_style))
    elements.append(Spacer(1, 10))
    
    table_data = [["ID", "Asal Usul", "Tahun", "Jenis Barang", "Kelompok", "Kecamatan", "Jumlah"]]
    for _, row in df_filtered.iterrows():
        table_data.append([
            str(row.get('id', '')),
            str(row.get('asal_usul', '')),
            str(row.get('tahun_hibah', '')),
            str(row.get('jenis_barang', '')),
            str(row.get('kelompok', '')),
            str(row.get('kecamatan', '')),
            str(row.get('jumlah', ''))
        ])
    
    t = Table(table_data, colWidths=[30, 80, 45, 100, 100, 85, 40])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A6F37')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F3F7F4')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# --- HEADER APLIKASI ---
st.markdown("""
    <div class='main-header'>
        <h1 style='margin:0; font-size: 30px;'>🚜 🌱 SIDAHTRA (SUPABASE CONNECTED)</h1>
        <p style='margin:5px 0 0 0; font-size: 15px;'>Sistem Data Hibah Alsintan Terpadu + Barcode & Manajemen Berkas</p>
    </div>
""", unsafe_allow_html=True)

menu = st.tabs(["📊 Dashboard & Filter", "📥 Input Data Baru", "📋 Rekap & Barcode", "🖨️ Laporan & Cetak", "📤 Impor/Ekspor & Hapus"])

df_main = fetch_data_supabase()

# ==================== TAB 0: DASHBOARD & FILTER ====================
with menu[0]:
    st.subheader("Dashboard & Filter Data Hibah")
    
    if not df_main.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_asal = st.selectbox("Filter Asal Usul", ["Semua", "APBD Kabupaten", "APBD Provinsi", "APBN Pusat"])
        with col_f2:
            tahun_list = ["Semua"] + sorted(df_main["tahun_hibah"].dropna().astype(str).unique().tolist())
            filter_tahun = st.selectbox("Filter Tahun", tahun_list)
        with col_f3:
            kec_list = ["Semua"] + sorted(df_main["kecamatan"].dropna().astype(str).unique().tolist())
            filter_kec = st.selectbox("Filter Kecamatan", kec_list)
            
        df_filtered = df_main.copy()
        if filter_asal != "Semua":
            df_filtered = df_filtered[df_filtered["asal_usul"] == filter_asal]
        if filter_tahun != "Semua":
            df_filtered = df_filtered[df_filtered["tahun_hibah"].astype(str) == filter_tahun]
        if filter_kec != "Semua":
            df_filtered = df_filtered[df_filtered["kecamatan"] == filter_kec]
            
        t_data = len(df_filtered)
        t_unit = int(df_filtered["jumlah"].sum()) if "jumlah" in df_filtered else 0
        t_nilai = int((df_filtered["jumlah"] * df_filtered["harga_satuan"]).sum()) if "jumlah" in df_filtered and "harga_satuan" in df_filtered else 0
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Data Terfilter", t_data)
        with m2:
            st.metric("Total Unit Alsintan", t_unit)
        with m3:
            st.metric("Total Estimasi Nilai", f"Rp {t_nilai:,}")
            
        st.markdown("---")
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("Belum ada data tersimpan di Supabase. Silakan input data baru melalui menu di atas.")

# ==================== TAB 1: INPUT DATA BARU ====================
with menu[1]:
    st.subheader("Formulir Input Data Hibah Alsintan")
    
    with st.form("form_input", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            asal_usul = st.selectbox("Asal Usul Hibah", ["APBD Kabupaten", "APBD Provinsi", "APBN Pusat"])
            tahun_hibah = st.text_input("Tahun Hibah", value=str(datetime.now().year))
            jenis_barang = st.text_input("Jenis Barang Alsintan")
            merk_type = st.text_input("Merk / Type")
            no_rangka = st.text_input("Nomor Rangka")
            no_mesin = st.text_input("Nomor Mesin")
            jumlah = st.number_input("Jumlah Barang (Unit)", min_value=1, value=1)
            harga_satuan = st.number_input("Harga Satuan (Rp)", min_value=0, value=0)
        with col2:
            kelompok = st.text_input("Nama Kelompok (Poktan/Gapoktan)")
            nama_ketua = st.text_input("Nama Ketua Kelompok")
            nik = st.text_input("NIK Ketua / Penerima (16 Digit)")
            kecamatan = st.text_input("Kecamatan")
            desa = st.text_input("Desa / Kelurahan")
            alamat = st.text_area("Detail Alamat")
            
        st.markdown("---")
        st.write("📂 **Link Dokumen Google Drive (Salin URL Tautan Di Sini)**")
        foto_gdrive = st.text_input("Link Google Drive - Foto Dokumentasi")
        proposal_gdrive = st.text_input("Link Google Drive - Proposal")
        bast_gdrive = st.text_input("Link Google Drive - BAST (Berita Acara Serah Terima)")
        
        submit_btn = st.form_submit_button("Simpan Data ke Supabase & Buat Barcode")
        
        if submit_btn:
            if kelompok and jenis_barang:
                if supabase:
                    try:
                        data_insert = {
                            "asal_usul": asal_usul,
                            "tahun_hibah": str(tahun_hibah),
                            "jenis_barang": jenis_barang,
                            "merk_type": merk_type,
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
                            "foto_gdrive": foto_gdrive,
                            "proposal_gdrive": proposal_gdrive,
                            "bast_gdrive": bast_gdrive,
                            "qr_path": ""
                        }
                        
                        res = supabase.table("hibah").insert(data_insert).execute()
                        if res.data:
                            new_id = res.data[0]["id"]
                            qr_path = generate_qr_code(new_id, kelompok, jenis_barang, kecamatan)
                            supabase.table("hibah").update({"qr_path": qr_path}).eq("id", new_id).execute()
                            st.success(f"✅ Data berhasil disimpan ke Supabase dengan ID #{new_id}!")
                        else:
                            st.error("Gagal menyimpan data ke database.")
                    except Exception as err:
                        st.error(f"Terjadi kesalahan: {err}")
                else:
                    st.error("Koneksi Supabase tidak aktif.")
            else:
                st.warning("⚠️ Mohon isi minimal 'Nama Kelompok' dan 'Jenis Barang'!")

# ==================== TAB 2: REKAP & BARCODE ====================
with menu[2]:
    st.subheader("📋 Rekap Data & Cetak Barcode Aset")
    if not df_main.empty:
        selected_id = st.selectbox("Pilih ID Data untuk Cetak Barcode:", df_main["id"].tolist())
        row_sel = df_main[df_main["id"] == selected_id].iloc[0]
        
        c_b1, c_b2 = st.columns([1, 2])
        with c_b1:
            q_path = str(row_sel.get("qr_path", ""))
            if q_path and os.path.exists(q_path):
                st.image(q_path, caption=f"Barcode ID #{row_sel['id']}", width=220)
                with open(q_path, "rb") as file:
                    st.download_button("📥 Download Barcode", file, file_name=f"barcode_id_{row_sel['id']}.png", mime="image/png")
            else:
                # Buat ulang qr jika belum ada di direktori lokal
                gen_path = generate_qr_code(row_sel['id'], row_sel['kelompok'], row_sel['jenis_barang'], row_sel['kecamatan'])
                st.image(gen_path, caption=f"Barcode ID #{row_sel['id']}", width=220)
        with c_b2:
            st.markdown(f"**ID Aset:** #{row_sel['id']}")
            st.markdown(f"**Asal Usul:** {row_sel['asal_usul']} ({row_sel['tahun_hibah']})")
            st.markdown(f"**Jenis Barang:** {row_sel['jenis_barang']} - {row_sel['merk_type']}")
            st.markdown(f"**Kelompok Penerima:** {row_sel['kelompok']} (Ketua: {row_sel['nama_ketua']})")
            st.markdown(f"**Lokasi:** Kec. {row_sel['kecamatan']}, Desa {row_sel['desa']}")
            st.markdown(f"**Link Foto GDrive:** [Buka Tautan]({row_sel['foto_gdrive']})" if row_sel['foto_gdrive'] else "**Link Foto:** -")
            st.markdown(f"**Link Proposal GDrive:** [Buka Tautan]({row_sel['proposal_gdrive']})" if row_sel['proposal_gdrive'] else "**Link Proposal:** -")
            st.markdown(f"**Link BAST GDrive:** [Buka Tautan]({row_sel['bast_gdrive']})" if row_sel['bast_gdrive'] else "**Link BAST:** -")
    else:
        st.info("Belum ada data di database.")

# ==================== TAB 3: LAPORAN & CETAK ====================
with menu[3]:
    st.subheader("🖨️ Cetak & Download Laporan (Excel & PDF)")
    if not df_main.empty:
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_main.to_excel(writer, index=False, sheet_name='SIDAHTRA')
            st.download_button("📥 Download Laporan Excel (.xlsx)", output_excel.getvalue(), "laporan_sidahtra.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_dl2:
            pdf_bytes = generate_pdf_report(df_main)
            st.download_button("📥 Download Laporan PDF (.pdf)", pdf_bytes, "laporan_sidahtra.pdf", mime="application/pdf")
    else:
        st.warning("Data kosong.")

# ==================== TAB 4: IMPOR/EKSPOR & HAPUS ====================
with menu[4]:
    st.subheader("📤 Impor / Ekspor Excel & Manajemen Hapus Data")
    
    col_ie1, col_ie2 = st.columns(2)
    with col_ie1:
        st.markdown("### 📥 Download Template Excel")
        template_df = pd.DataFrame(columns=[
            "asal_usul", "tahun_hibah", "jenis_barang", "merk_type", "no_rangka", 
            "no_mesin", "jumlah", "harga_satuan", "kelompok", "nama_ketua", 
            "nik", "kecamatan", "desa", "alamat", "foto_gdrive", "proposal_gdrive", "bast_gdrive"
        ])
        t_excel = io.BytesIO()
        with pd.ExcelWriter(t_excel, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False, sheet_name='Template')
        st.download_button("⬇️ Download Template Excel", t_excel.getvalue(), "template_sidahtra.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.markdown("### 📤 Impor Data Massal dari Excel")
        uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
        if uploaded_file is not None and supabase:
            try:
                df_imp = pd.read_excel(uploaded_file)
                success_count = 0
                for _, row in df_imp.iterrows():
                    data_row = {
                        "asal_usul": str(row.get("asal_usul", "APBD Kabupaten")),
                        "tahun_hibah": str(row.get("tahun_hibah", "2026")),
                        "jenis_barang": str(row.get("jenis_barang", "Alsintan")),
                        "merk_type": str(row.get("merk_type", "")),
                        "no_rangka": str(row.get("no_rangka", "")),
                        "no_mesin": str(row.get("no_mesin", "")),
                        "jumlah": int(row.get("jumlah", 1)),
                        "harga_satuan": float(row.get("harga_satuan", 0)),
                        "kelompok": str(row.get("kelompok", "Kelompok")),
                        "nama_ketua": str(row.get("nama_ketua", "")),
                        "nik": str(row.get("nik", "")),
                        "kecamatan": str(row.get("kecamatan", "")),
                        "desa": str(row.get("desa", "")),
                        "alamat": str(row.get("alamat", "")),
                        "foto_gdrive": str(row.get("foto_gdrive", "")),
                        "proposal_gdrive": str(row.get("proposal_gdrive", "")),
                        "bast_gdrive": str(row.get("bast_gdrive", "")),
                        "qr_path": ""
                    }
                    res = supabase.table("hibah").insert(data_row).execute()
                    if res.data:
                        new_id = res.data[0]["id"]
                        q_p = generate_qr_code(new_id, data_row["kelompok"], data_row["jenis_barang"], data_row["kecamatan"])
                        supabase.table("hibah").update({"qr_path": q_p}).eq("id", new_id).execute()
                        success_count += 1
                st.success(f"✅ Berhasil mengimpor {success_count} data ke Supabase!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal mengimpor: {e}")

    with col_ie2:
        st.markdown("### 🗑️ Hapus Data dari Database")
        if not df_main.empty:
            id_hapus = st.selectbox("Pilih ID Data yang Dihapus:", df_main["id"].tolist(), key="del_select")
            if st.button("Hapus Data Terpilih"):
                try:
                    supabase.table("hibah").delete().eq("id", id_hapus).execute()
                    st.success(f"Data ID #{id_hapus} berhasil dihapus dari Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghapus: {e}")
        else:
            st.info("Tidak ada data untuk dihapus.")
