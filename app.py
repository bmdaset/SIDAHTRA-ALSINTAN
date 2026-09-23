import streamlit as st
import pandas as pd
import datetime
import qrcode
from io import BytesIO
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SIDAHTRA - Sistem Data Hibah Alsintan Terpadu",
    page_icon="🚜",
    layout="wide"
)

# Custom CSS agar tabel preview bergaris rapi, elegan, & ramah mobile (HP)
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 1.6rem;
        margin-bottom: 5px;
    }
    .main-header p {
        font-size: 0.95rem;
        margin: 0;
    }
    /* Style Tabel Detail Bergaris */
    .detail-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 15px;
        font-size: 0.95rem;
        background-color: #ffffff;
        color: #333333;
    }
    .detail-table th, .detail-table td {
        border: 1px solid #dcdcdc;
        padding: 10px 12px;
        text-align: left;
    }
    .detail-table th {
        background-color: #f1f8e9;
        color: #1b5e20;
        width: 35%;
        font-weight: bold;
    }
    .detail-table td {
        width: 65%;
    }
    @media (max-width: 768px) {
        .stButton button {
            width: 100%;
            margin-bottom: 10px;
        }
        .detail-table {
            font-size: 0.85rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Gagal terhubung ke Supabase: {e}")

# Fungsi untuk mengambil data dari Supabase
def fetch_data_supabase():
    if supabase is None:
        return pd.DataFrame()
    try:
        response = supabase.table("hibah").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            if not df.empty and "id" in df.columns:
                df = df.sort_values(by="id", ascending=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal memuat data dari Supabase: {e}")
        return pd.DataFrame()

# Header Utama Aplikasi (Tanpa tulisan Supabase Connected)
st.markdown("""
    <div class='main-header'>
        <h1>🚜 SIDAHTRA</h1>
        <p>Sistem Data Hibah Alsintan Terpadu</p>
    </div>
""", unsafe_allow_html=True)

# Tombol Refresh Data
col_rf1, col_rf2 = st.columns([5, 1])
with col_rf2:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# Navigasi Tab (Diringkas menjadi 4 Tab)
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "📥 Input Data", 
    "📋 Rekap, Barcode & Laporan", 
    "📁 Impor / Kelola"
])

# ================= TAB 1: DASHBOARD & FILTER =================
with tab1:
    st.subheader("Dashboard & Filter Data Hibah")
    df_data = fetch_data_supabase()

    if df_data.empty:
        st.info("Belum ada data tersimpan di Supabase.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Unit", int(df_data['jumlah'].sum()) if 'jumlah' in df_data.columns else len(df_data))
            st.metric("Total Jenis", df_data['jenis_barang'].nunique() if 'jenis_barang' in df_data.columns else 0)
        with col2:
            st.metric("Total Kelompok", df_data['nama_ketua'].nunique() if 'nama_ketua' in df_data.columns else 0)
            st.metric("Total Kecamatan", df_data['kecamatan'].nunique() if 'kecamatan' in df_data.columns else 0)

        st.divider()

        st.markdown("### 🔍 Filter Data")
        asal_list = ["Semua"] + list(df_data['asal_usul'].dropna().unique()) if 'asal_usul' in df_data.columns else ["Semua"]
        p_asal = st.selectbox("Asal Usul", asal_list)
        
        tahun_list = ["Semua"] + list(df_data['tahun_hibah'].dropna().unique()) if 'tahun_hibah' in df_data.columns else ["Semua"]
        p_tahun = st.selectbox("Tahun Hibah", tahun_list)
        
        kec_list = ["Semua"] + list(df_data['kecamatan'].dropna().unique()) if 'kecamatan' in df_data.columns else ["Semua"]
        p_kec = st.selectbox("Kecamatan", kec_list)

        filtered_df = df_data.copy()
        if p_asal != "Semua":
            filtered_df = filtered_df[filtered_df['asal_usul'] == p_asal]
        if p_tahun != "Semua":
            filtered_df = filtered_df[filtered_df['tahun_hibah'] == str(p_tahun)]
        if p_kec != "Semua":
            filtered_df = filtered_df[filtered_df['kecamatan'] == p_kec]

        st.markdown(f"Menampilkan **{len(filtered_df)}** data.")
        st.dataframe(filtered_df, use_container_width=True)

# ================= TAB 2: INPUT DATA BARU =================
with tab2:
    st.subheader("Formulir Input Data Hibah")
    
    with st.form("form_input_hibah"):
        asal_usul = st.selectbox("Asal Usul Bantuan", ["APBD Kabupaten", "APBD Provinsi", "APBN", "Pokir", "Lainnya"])
        tahun_hibah = st.text_input("Tahun Hibah", str(datetime.datetime.now().year))
        jenis_barang = st.text_input("Jenis Barang / Alsintan")
        merk_type = st.text_input("Merk / Type")
        no_rangka = st.text_input("Nomor Rangka")
        no_mesin = st.text_input("Nomor Mesin")
        jumlah = st.number_input("Jumlah Unit", min_value=1, value=1, step=1)
        harga_satuan = st.number_input("Harga Satuan (Rp)", min_value=0.0, value=0.0, step=1000.0)
        kelompok = st.text_input("Nama Kelompok Tani / P3A")
        nama_ketua = st.text_input("Nama Ketua")
        nik = st.text_input("NIK Ketua")
        kecamatan = st.text_input("Kecamatan")
        desa = st.text_input("Desa / Kelurahan")
        alamat = st.text_area("Alamat Lengkap")
        foto_gdrive = st.text_input("Link GDrive Foto Penyerahan")
        proposal_gdrive = st.text_input("Link GDrive Proposal")
        bast_gdrive = st.text_input("Link GDrive BAST")

        submitted = st.form_submit_button("💾 Simpan Data")
        
        if submitted:
            if not jenis_barang or not kelompok:
                st.warning("Mohon lengkapi minimal Jenis Barang dan Nama Kelompok!")
            elif supabase is None:
                st.error("Koneksi Supabase belum terkonfigurasi.")
            else:
                data_dict = {
                    "asal_usul": asal_usul, "tahun_hibah": tahun_hibah,
                    "jenis_barang": jenis_barang, "merk_type": merk_type,
                    "no_rangka": no_rangka, "no_mesin": no_mesin,
                    "jumlah": int(jumlah), "harga_satuan": float(harga_satuan),
                    "kelompok": kelompok, "nama_ketua": nama_ketua,
                    "nik": nik, "kecamatan": kecamatan, "desa": desa,
                    "alamat": alamat, "foto_gdrive": foto_gdrive,
                    "proposal_gdrive": proposal_gdrive, "bast_gdrive": bast_gdrive,
                    "qr_path": ""
                }
                try:
                    res = supabase.table("hibah").insert(data_dict).execute()
                    if res.data:
                        st.success("Data berhasil disimpan!")
                        st.balloons()
                    else:
                        st.error("Gagal menyimpan data.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ================= TAB 3: REKAP, BARCODE & LAPORAN (DIGABUNG) =================
with tab3:
    st.subheader("📋 Rekap, Preview Detail & Barcode")
    df_data = fetch_data_supabase()
    
    if df_data.empty:
        st.info("Belum ada data untuk ditampilkan.")
    else:
        # Fitur Pencarian Data
        keyword = st.text_input("🔍 Cari Data (Jenis Barang / Kelompok / No Rangka)", "")
        
        search_df = df_data.copy()
        if keyword:
            mask = search_df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)
            search_df = search_df[mask]
            
        if not search_df.empty:
            selected_id = st.selectbox(
                "Pilih Item untuk Melihat Preview Detail Lengkap & QR Code", 
                search_df['id'].tolist(),
                format_func=lambda x: f"ID #{x} - {search_df[search_df['id'] == x]['jenis_barang'].values[0]} ({search_df[search_df['id'] == x]['kelompok'].values[0]})"
            )
            
            selected_row = search_df[search_df['id'] == selected_id].iloc[0]
            
            with st.container():
                st.markdown("---")
                st.markdown("#### 👁️ Preview Detail Lengkap Barang & QR Code")
                
                # Fungsi Helper untuk membaca nilai kolom dengan aman
                def val(key):
                    v = selected_row.get(key)
                    return "-" if pd.isna(v) or str(v).strip() == "" else str(v)

                # Format Harga Rupiah
                try:
                    harga_val = float(selected_row.get('harga_satuan', 0))
                    harga_str = f"Rp {harga_val:,.2f}"
                except:
                    harga_str = str(selected_row.get('harga_satuan', '-'))

                # Render Preview Sedetail-detainya dalam Tabel Bergaris HTML yang Rapi
                html_detail = f"""
                <table class="detail-table">
                    <tr><th>ID Data</th><td>#{val('id')}</td></tr>
                    <tr><th>Asal Usul Bantuan</th><td>{val('asal_usul')}</td></tr>
                    <tr><th>Tahun Hibah</th><td>{val('tahun_hibah')}</td></tr>
                    <tr><th>Jenis Barang / Alsintan</th><td>{val('jenis_barang')}</td></tr>
                    <tr><th>Merk / Type</th><td>{val('merk_type')}</td></tr>
                    <tr><th>Nomor Rangka</th><td>{val('no_rangka')}</td></tr>
                    <tr><th>Nomor Mesin</th><td>{val('no_mesin')}</td></tr>
                    <tr><th>Jumlah Unit</th><td>{val('jumlah')} Unit</td></tr>
                    <tr><th>Harga Satuan</th><td>{harga_str}</td></tr>
                    <tr><th>Nama Kelompok Tani / P3A</th><td>{val('kelompok')}</td></tr>
                    <tr><th>Nama Ketua / Penanggung Jawab</th><td>{val('nama_ketua')}</td></tr>
                    <tr><th>NIK Ketua</th><td>{val('nik')}</td></tr>
                    <tr><th>Kecamatan</th><td>{val('kecamatan')}</td></tr>
                    <tr><th>Desa / Kelurahan</th><td>{val('desa')}</td></tr>
                    <tr><th>Alamat Lengkap</th><td>{val('alamat')}</td></tr>
                    <tr><th>Link Foto Penyerahan (GDrive)</th><td>{val('foto_gdrive')}</td></tr>
                    <tr><th>Link Proposal (GDrive)</th><td>{val('proposal_gdrive')}</td></tr>
                    <tr><th>Link BAST (GDrive)</th><td>{val('bast_gdrive')}</td></tr>
                </table>
                """
                st.markdown(html_detail, unsafe_allow_html=True)
                
                # Generate & Tampilkan QR Code
                qr_content = f"ID: {val('id')}\nAlsintan: {val('jenis_barang')}\nKelompok: {val('kelompok')}\nNo. Rangka: {val('no_rangka')}"
                qr = qrcode.QRCode(box_size=6, border=2)
                qr.add_data(qr_content)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                col_img1, col_img2 = st.columns([1, 2])
                with col_img1:
                    st.image(byte_im, caption=f"QR Code ID #{val('id')}", width=160)
                with col_img2:
                    st.download_button(
                        label="📥 Unduh Gambar QR Code",
                        data=byte_im,
                        file_name=f"QR_Alsintan_ID_{val('id')}.png",
                        mime="image/png"
                    )
        
        st.divider()
        
        # Bagian Laporan Keseluruhan (Excel & PDF)
        st.markdown("#### 🖨️ Cetak & Unduh Laporan Keseluruhan")
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_data.to_excel(writer, index=False, sheet_name="Rekap_Hibah")
            excel_buffer.seek(0)
            
            st.download_button(
                label="📥 Unduh Rekap (Excel)",
                data=excel_buffer,
                file_name="Rekap_Laporan_Hibah_Alsintan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with col_dl2:
            if st.button("📄 Buat & Unduh Laporan PDF"):
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                
                p.drawString(40, height - 40, "LAPORAN REKAPITULASI HIBAH ALSINTAN")
                p.drawString(40, height - 60, f"Dicetak: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                y = height - 90
                for idx, row in df_data.iterrows():
                    if y < 40:
                        p.showPage()
                        y = height - 40
                    text_line = f"ID:{row.get('id')} | {row.get('jenis_barang')} | Kel: {row.get('kelompok')}"
                    p.drawString(40, y, text_line)
                    y -= 18
                    
                p.save()
                buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Download File PDF",
                    data=buffer,
                    file_name="Laporan_Hibah_Alsintan.pdf",
                    mime="application/pdf"
                )

# ================= TAB 4: IMPOR/EKSPOR & HAPUS =================
with tab4:
    st.subheader("📁 Manajemen Data (Impor, Ekspor & Hapus)")
    
    st.markdown("### 📥 Unduh Template & Impor Excel")
    template_columns = [
        "asal_usul", "tahun_hibah", "jenis_barang", "merk_type", "no_rangka", 
        "no_mesin", "jumlah", "harga_satuan", "kelompok", "nama_ketua", 
        "nik", "kecamatan", "desa", "alamat", "foto_gdrive", "proposal_gdrive", "bast_gdrive"
    ]
    df_template = pd.DataFrame(columns=template_columns)
    
    tmpl_buffer = BytesIO()
    with pd.ExcelWriter(tmpl_buffer, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name="Template")
    tmpl_buffer.seek(0)
    
    st.download_button(
        label="⬇️ Unduh Template Excel",
        data=tmpl_buffer,
        file_name="template_input_hibah.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.markdown("---")
    uploaded_file = st.file_uploader("Unggah File Excel/CSV", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_import = pd.read_csv(uploaded_file)
            else:
                df_import = pd.read_excel(uploaded_file)
                
            st.dataframe(df_import.head())
            
            if st.button("🚀 Proses Impor ke Database"):
                if supabase:
                    success_count = 0
                    for _, row in df_import.iterrows():
                        row_dict = row.dropna().to_dict()
                        if "jenis_barang" in row_dict:
                            row_dict["qr_path"] = ""
                            try:
                                supabase.table("hibah").insert(row_dict).execute()
                                success_count += 1
                            except Exception:
                                pass
                    st.success(f"Berhasil mengimpor {success_count} data!")
        except Exception as e:
            st.error(f"Error membaca file: {e}")

    st.divider()
    st.markdown("### 🗑️ Hapus Data Berdasarkan ID")
    del_id = st.number_input("Masukkan ID Data yang akan dihapus", min_value=1, step=1)
    if st.button("❌ Hapus Data"):
        if supabase:
            try:
                supabase.table("hibah").delete().eq("id", del_id).execute()
                st.success(f"Data ID #{del_id} berhasil dihapus!")
            except Exception as e:
                st.error(f"Gagal menghapus: {e}")
