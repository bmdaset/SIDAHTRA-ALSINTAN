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

# Header Utama Aplikasi
st.markdown("""
    <div style='background: linear-gradient(90deg, #1b5e20, #2e7d32); padding: 25px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;'>
        <h1>🚜 SIDAHTRA (SUPABASE CONNECTED)</h1>
        <p style='font-size: 1.1rem; margin: 0;'>Sistem Data Hibah Alsintan Terpadu + Barcode & Manajemen Berkas</p>
    </div>
""", unsafe_allow_html=True)

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
    st.subheader("Cetak & Lihat Barcode / QR Code Unit")
    df_data = fetch_data_supabase()
    
    if df_data.empty:
        st.info("Belum ada data untuk dibuatkan Barcode.")
    else:
        selected_id = st.selectbox("Pilih ID / Data Barang", df_data['id'].tolist())
        selected_row = df_data[df_data['id'] == selected_id].iloc[0]
        
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            st.markdown("### Detail Informasi")
            st.write(f"**ID Data:** #{selected_row.get('id')}")
            st.write(f"**Jenis Barang:** {selected_row.get('jenis_barang')}")
            st.write(f"**Merk/Type:** {selected_row.get('merk_type')}")
            st.write(f"**Kelompok:** {selected_row.get('kelompok')}")
            st.write(f"**Ketua:** {selected_row.get('nama_ketua')}")
            st.write(f"**Kecamatan:** {selected_row.get('kecamatan')}")
            st.write(f"**Tahun:** {selected_row.get('tahun_hibah')}")
            
        with col_b2:
            st.markdown("### QR Code Aset")
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
    st.subheader("Cetak Laporan PDF / Rekapitulasi")
    df_data = fetch_data_supabase()
    
    if df_data.empty:
        st.info("Tidak ada data untuk dicetak.")
    else:
        st.write("Klik tombol di bawah untuk mengunduh laporan rekapitulasi data hibah dalam bentuk berkas PDF.")
        
        if st.button("Generate Laporan PDF"):
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
    st.subheader("Manajemen Data (Ekspor, Impor & Hapus)")
    df_data = fetch_data_supabase()
    
    if not df_data.empty:
        st.markdown("### Ekspor Data ke CSV")
        csv_data = df_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh Seluruh Data (CSV)",
            data=csv_data,
            file_name="data_hibah_alsintan.csv",
            mime="text/csv"
        )
    
    st.divider()
    st.markdown("### Hapus Data Berdasarkan ID")
    del_id = st.number_input("Masukkan ID Data yang akan dihapus", min_value=1, step=1)
    if st.button("Hapus Data"):
        if supabase:
            try:
                supabase.table("hibah").delete().eq("id", del_id).execute()
                st.success(f"Data dengan ID #{del_id} berhasil dihapus dari Supabase!")
            except Exception as e:
                st.error(f"Gagal menghapus data: {e}")
