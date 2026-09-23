import streamlit as st
import pandas as pd
import datetime
import qrcode
from io import BytesIO
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SIDAHTRA - Sistem Data Hibah Alsintan Terpadu",
    page_icon="🚜",
    layout="wide"
)

# Inisialisasi Koneksi Supabase dari st.secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Gagal terhubung ke Supabase: {e}")

# Fungsi untuk mengambil data dari Supabase (dengan dukungan Clear Cache / Refresh)
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

# Header Utama Aplikasi
st.markdown("""
    <div style='background: linear-gradient(90deg, #1b5e20, #2e7d32); padding: 25px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;'>
        <h1>🚜 SIDAHTRA (SUPABASE CONNECTED)</h1>
        <p style='font-size: 1.1rem; margin: 0;'>Sistem Data Hibah Alsintan Terpadu + Barcode & Manajemen Berkas</p>
    </div>
""", unsafe_allow_html=True)

# Tombol Global Refresh Data di Sidebar / Bagian Atas
col_rf1, col_rf2 = st.columns([6, 1])
with col_rf2:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Navigasi Tab
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard & Filter", 
    "📥 Input Data Baru", 
    "📋 Rekap & Barcode", 
    "🖨️ Laporan & Cetak", 
    "📁 Impor/Ekspor & Hapus"
])

# ================= TAB 1: DASHBOARD & FILTER =================
with tab1:
    st.subheader("Dashboard & Filter Data Hibah")
    df_data = fetch_data_supabase()

    if df_data.empty:
        st.info("Belum ada data tersimpan di Supabase. Silakan input data baru melalui menu di atas.")
    else:
        # Ringkasan Metrik Utama
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Unit Alsintan", int(df_data['jumlah'].sum()) if 'jumlah' in df_data.columns else len(df_data))
        with col2:
            st.metric("Total Jenis Bantuan", df_data['jenis_barang'].nunique() if 'jenis_barang' in df_data.columns else 0)
        with col3:
            st.metric("Total Kelompok Penerima", df_data['nama_ketua'].nunique() if 'nama_ketua' in df_data.columns else 0)
        with col4:
            st.metric("Total Kecamatan", df_data['kecamatan'].nunique() if 'kecamatan' in df_data.columns else 0)

        st.divider()

        # Fitur Filter
        st.markdown("### 🔍 Filter Data")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            asal_list = ["Semua"] + list(df_data['asal_usul'].dropna().unique()) if 'asal_usul' in df_data.columns else ["Semua"]
            p_asal = st.selectbox("Asal Usul", asal_list)
        with f_col2:
            tahun_list = ["Semua"] + list(df_data['tahun_hibah'].dropna().unique()) if 'tahun_hibah' in df_data.columns else ["Semua"]
            p_tahun = st.selectbox("Tahun Hibah", tahun_list)
        with f_col3:
            kec_list = ["Semua"] + list(df_data['kecamatan'].dropna().unique()) if 'kecamatan' in df_data.columns else ["Semua"]
            p_kec = st.selectbox("Kecamatan", kec_list)

        filtered_df = df_data.copy()
        if p_asal != "Semua":
            filtered_df = filtered_df[filtered_df['asal_usul'] == p_asal]
        if p_tahun != "Semua":
            filtered_df = filtered_df[filtered_df['tahun_hibah'] == str(p_tahun)]
        if p_kec != "Semua":
            filtered_df = filtered_df[filtered_df['kecamatan'] == p_kec]

        st.markdown(f"Menampilkan **{len(filtered_df)}** data dari total **{len(df_data)}** data.")
        st.dataframe(filtered_df, use_container_width=True)

# ================= TAB 2: INPUT DATA BARU =================
with tab2:
    st.subheader("Formulir Input Data Hibah Alsintan")
    
    with st.form("form_input_hibah"):
        col_i1, col_i2 = st.columns(2)
        
        with col_i1:
            asal_usul = st.selectbox("Asal Usul Bantuan", ["APBD Kabupaten", "APBD Provinsi", "APBN", "Pokir", "Lainnya"])
            tahun_hibah = st.text_input("Tahun Hibah", str(datetime.datetime.now().year))
            jenis_barang = st.text_input("Jenis Barang / Alsintan (Contoh: Traktor Roda 4)")
            merk_type = st.text_input("Merk / Type")
            no_rangka = st.text_input("Nomor Rangka")
            no_mesin = st.text_input("Nomor Mesin")
            jumlah = st.number_input("Jumlah Unit", min_value=1, value=1, step=1)
            harga_satuan = st.number_input("Harga Satuan (Rp)", min_value=0.0, value=0.0, step=1000.0)
            
        with col_i2:
            kelompok = st.text_input("Nama Kelompok Tani / P3A")
            nama_ketua = st.text_input("Nama Ketua / Penanggung Jawab")
            nik = st.text_input("NIK Ketua")
            kecamatan = st.text_input("Kecamatan")
            desa = st.text_input("Desa / Kelurahan")
            alamat = st.text_area("Alamat Lengkap")
            foto_gdrive = st.text_input("Link GDrive Foto Penyerahan")
            proposal_gdrive = st.text_input("Link GDrive Proposal")
            bast_gdrive = st.text_input("Link GDrive BAST")

        submitted = st.form_submit_button("Simpan Data ke Supabase & Buat Barcode")
        
        if submitted:
            if not jenis_barang or not kelompok:
                st.warning("Mohon lengkapi minimal Jenis Barang dan Nama Kelompok!")
            elif supabase is None:
                st.error("Koneksi Supabase belum dikonfigurasi dengan benar.")
            else:
                data_dict = {
                    "asal_usul": asal_usul,
                    "tahun_hibah": tahun_hibah,
                    "jenis_barang": jenis_barang,
                    "merk_type": merk_type,
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
                    "foto_gdrive": foto_gdrive,
                    "proposal_gdrive": proposal_gdrive,
                    "bast_gdrive": bast_gdrive,
                    "qr_path": ""
                }
                try:
                    res = supabase.table("hibah").insert(data_dict).execute()
                    if res.data:
                        new_id = res.data[0]['id']
                        st.success(f"Data berhasil disimpan ke Supabase dengan ID #{new_id}!")
                        st.balloons()
                    else:
                        st.error("Gagal menyimpan data ke database.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

# ================= TAB 3: REKAP & BARCODE =================
with tab3:
    st.subheader("Pencarian, Preview Barang & Cetak Barcode/QR Code")
    df_data = fetch_data_supabase()
    
    if df_data.empty:
        st.info("Belum ada data untuk ditampilkan.")
    else:
        # Fitur Search Barang
        keyword = st.text_input("🔍 Cari Barang (Ketik Jenis Barang, Kelompok, atau No. Rangka)", "")
        
        search_df = df_data.copy()
        if keyword:
            mask = search_df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)
            search_df = search_df[mask]
            
        st.markdown(f"Ditemukan **{len(search_df)}** data yang sesuai.")
        
        if not search_df.empty:
            # Pilihan berdasarkan hasil pencarian
            selected_id = st.selectbox(
                "Pilih ID & Detail Barang untuk Preview", 
                search_df['id'].tolist(),
                format_func=lambda x: f"ID #{x} - {search_df[search_df['id'] == x]['jenis_barang'].values[0]} ({search_df[search_df['id'] == x]['kelompok'].values[0]})"
            )
            
            selected_row = search_df[search_df['id'] == selected_id].iloc[0]
            
            st.divider()
            st.markdown("### 👁️ Preview Detail Barang & QR Code")
            col_b1, col_b2 = st.columns([1, 1])
            
            with col_b1:
                st.write(f"**ID Data:** #{selected_row.get('id')}")
                st.write(f"**Asal Usul:** {selected_row.get('asal_usul')}")
                st.write(f"**Tahun Hibah:** {selected_row.get('tahun_hibah')}")
                st.write(f"**Jenis Barang:** {selected_row.get('jenis_barang')}")
                st.write(f"**Merk/Type:** {selected_row.get('merk_type')}")
                st.write(f"**Nomor Rangka:** {selected_row.get('no_rangka')}")
                st.write(f"**Nomor Mesin:** {selected_row.get('no_mesin')}")
                st.write(f"**Jumlah Unit:** {selected_row.get('jumlah')}")
                st.write(f"**Kelompok Tani:** {selected_row.get('kelompok')}")
                st.write(f"**Nama Ketua:** {selected_row.get('nama_ketua')}")
                st.write(f"**Kecamatan/Desa:** {selected_row.get('kecamatan')} / {selected_row.get('desa')}")
                
            with col_b2:
                qr_content = f"ID: {selected_row.get('id')}\nAlsintan: {selected_row.get('jenis_barang')}\nKelompok: {selected_row.get('kelompok')}\nNo. Rangka: {selected_row.get('no_rangka')}"
                
                qr = qrcode.QRCode(box_size=8, border=2)
                qr.add_data(qr_content)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.image(byte_im, caption=f"QR Code - {selected_row.get('jenis_barang')}", width=220)
                st.download_button(
                    label="Unduh Gambar QR Code",
                    data=byte_im,
                    file_name=f"QR_Alsintan_ID_{selected_row.get('id')}.png",
                    mime="image/png"
                )

# ================= TAB 4: LAPORAN & CETAK =================
with tab4:
    st.subheader("Cetak Laporan PDF / Rekapitulasi & Unduh Excel")
    df_data = fetch_data_supabase()
    
    if df_data.empty:
        st.info("Tidak ada data untuk dicetak.")
    else:
        st.write("Pilih format dokumen laporan rekapitulasi data hibah yang ingin diunduh:")
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            # Tombol Download Excel dari Data Rekap
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
            if st.button("📄 Generate & Unduh Laporan PDF"):
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                
                p.drawString(50, height - 50, "LAPORAN REKAPITULASI HIBAH ALSINTAN")
                p.drawString(50, height - 70, f"Dicetak pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                y = height - 110
                for idx, row in df_data.iterrows():
                    if y < 50:
                        p.showPage()
                        y = height - 50
                    text_line = f"ID: {row.get('id')} | {row.get('jenis_barang')} | Kelompok: {row.get('kelompok')} | Kec: {row.get('kecamatan')}"
                    p.drawString(50, y, text_line)
                    y -= 20
                    
                p.save()
                buffer.seek(0)
                
                st.download_button(
                    label="Unduh Berkas PDF",
                    data=buffer,
                    file_name="Laporan_Hibah_Alsintan.pdf",
                    mime="application/pdf"
                )

# ================= TAB 5: IMPOR/EKSPOR & HAPUS =================
with tab5:
    st.subheader("Manajemen Data (Ekspor, Impor Template & Hapus)")
    
    st.markdown("### 📥 Unduh Template & Impor Data Excel")
    
    # Membuat Template Excel Kosong Berdasarkan Kolom Database
    template_columns = [
        "asal_usul", "tahun_hibah", "jenis_barang", "merk_type", "no_rangka", 
        "no_mesin", "jumlah", "harga_satuan", "kelompok", "nama_ketua", 
        "nik", "kecamatan", "desa", "alamat", "foto_gdrive", "proposal_gdrive", "bast_gdrive"
    ]
    df_template = pd.DataFrame(columns=template_columns)
    
    tmpl_buffer = BytesIO()
    with pd.ExcelWriter(tmpl_buffer, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False, sheet_name="Template_Input")
    tmpl_buffer.seek(0)
    
    st.download_button(
        label="⬇️ Unduh Template Excel",
        data=tmpl_buffer,
        file_name="template_input_hibah.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.markdown("---")
    
    # Upload File Excel/CSV untuk Impor
    uploaded_file = st.file_uploader("Unggah Berkas Excel/CSV yang Telah Diisi", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_import = pd.read_csv(uploaded_file)
            else:
                df_import = pd.read_excel(uploaded_file)
                
            st.write("Preview Data yang Akan Diimpor:")
            st.dataframe(df_import.head())
            
            if st.button("🚀 Proses Impor ke Supabase"):
                if supabase is None:
                    st.error("Koneksi Supabase belum terhubung.")
                else:
                    success_count = 0
                    for _, row in df_import.iterrows():
                        row_dict = row.dropna().to_dict()
                        if "jenis_barang" in row_dict and "kelompok" in row_dict:
                            row_dict["qr_path"] = ""
                            try:
                                supabase.table("hibah").insert(row_dict).execute()
                                success_count += 1
                            except Exception:
                                pass
                    st.success(f"Berhasil mengimpor {success_count} data ke Supabase!")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")

    st.divider()
    
    df_data = fetch_data_supabase()
    if not df_data.empty:
        st.markdown("### 📤 Ekspor Seluruh Data")
        csv_data = df_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh Seluruh Data (CSV)",
            data=csv_data,
            file_name="data_hibah_alsintan.csv",
            mime="text/csv"
        )
    
    st.divider()
    st.markdown("### 🗑️ Hapus Data Berdasarkan ID")
    del_id = st.number_input("Masukkan ID Data yang akan dihapus", min_value=1, step=1)
    if st.button("Hapus Data"):
        if supabase:
            try:
                supabase.table("hibah").delete().eq("id", del_id).execute()
                st.success(f"Data dengan ID #{del_id} berhasil dihapus dari Supabase!")
            except Exception as e:
                st.error(f"Gagal menghapus data: {e}")
