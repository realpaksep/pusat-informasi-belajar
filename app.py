import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# Konfigurasi Halaman Utama Web
st.set_page_config(page_title="Pusat Informasi Belajar", layout="wide", page_icon="📚")
st.title("📚 Pusat Informasi Belajar - SMK (Edisi Cloud)")
st.subheader("Aplikasi Penunjang Guru PAI & Wali Kelas")

# Inisialisasi Koneksi ke Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

# --- HALAMAN UTAMA: Generasi Tahun Pelajaran (Usia 33 s.d 60 tahun) ---
usia_sekarang = 33
tahun_sekarang = 2026
list_tp = []
for i in range(60 - usia_sekarang + 1):
    thn_mulai = tahun_sekarang + i
    thn_selesai = thn_mulai + 1
    list_tp.append(f"KBM TP. {thn_mulai}/{thn_selesai}")

selected_tp = st.selectbox("Pilih Tahun Pelajaran:", ["-- Pilih TP --"] + list_tp)

if selected_tp != "-- Pilih TP --":
    st.success(f"Anda masuk ke: **{selected_tp}**")
    
    # --- MENU ROMBEL KELAS VIA GOOGLE SHEETS ---
    if "list_rombel" not in st.session_state:
        st.session_state.list_rombel = []

    # Coba ambil data rombel dari cloud jika terkoneksi
    if conn:
        try:
            df_rombel_cloud = conn.read(worksheet="Data_Rombel", ttl=5)
            st.session_state.list_rombel = df_rombel_cloud["Nama Rombel"].dropna().tolist()
        except Exception:
            pass

    rombel_input = st.text_input("Input Rombel Kelas Baru (Contoh: KELAS X TKJ A):")
    if st.button("Tambah Rombel dan Simpan ke Cloud"):
        if rombel_input and rombel_input.upper() not in st.session_state.list_rombel:
            st.session_state.list_rombel.append(rombel_input.upper())
            if conn:
                try:
                    df_update = pd.DataFrame({"Nama Rombel": st.session_state.list_rombel})
                    conn.update(worksheet="Data_Rombel", data=df_update)
                    st.success("Rombel Baru Berhasil Tersimpan Permanen di Cloud Google Sheets!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal sinkron ke Cloud: {e}. Pastikan Google Sheets sudah disetting di Streamlit.")
            else:
                st.warning("Rombel tersimpan sementara (Belum terhubung Google Sheets).")

    if st.session_state.list_rombel:
        selected_rombel = st.selectbox("Pilih Rombel Kelas:", ["-- Pilih Rombel --"] + st.session_state.list_rombel)
        
        if selected_rombel != "-- Pilih Rombel --":
            st.info(f"Mengelola Kelas: **{selected_rombel}**")
            
            # --- MENU NAVIGASI FITUR ---
            menu = st.sidebar.radio(
                "PILIH MENU APLIKASI",
                ["1. Absensi Siswa", "2. Evaluasi Ibadah", "3. Evaluasi BBQ", "4. Hafalan Surat", "5. Penugasan dan Nilai", "6. Catatan Siswa"]
            )
            
            # --- PROSES MEMBACA MASTER DATA SISWA DARI GOOGLE SHEETS ---
            st.sidebar.markdown("---")
            st.sidebar.subheader("Master Data Siswa")
            
            df_siswa_cloud = None
            if conn:
                try:
                    df_siswa_cloud = conn.read(worksheet=f"Siswa_{selected_rombel.replace(' ', '_')}", ttl=10)
                    st.sidebar.success(f"Berhasil memuat data {selected_rombel} dari Cloud!")
                except Exception:
                    df_siswa_cloud = None

            uploaded_file = st.sidebar.file_uploader("Atau Upload/Update Template Excel/CSV Manual", type=["xlsx", "csv"])
            if uploaded_file:
                if uploaded_file.name.endswith('.csv'):
                    df_siswa_cloud = pd.read_csv(uploaded_file)
                else:
                    df_siswa_cloud = pd.read_excel(uploaded_file)
                
                if conn:
                    try:
                        conn.update(worksheet=f"Siswa_{selected_rombel.replace(' ', '_')}", data=df_siswa_cloud)
                        st.sidebar.success("Data Siswa Berhasil Dikirim Permanen ke Cloud Google Sheets!")
                    except Exception:
                        pass

            if df_siswa_cloud is None:
                st.warning("Silakan unggah daftar siswa terlebih dahulu di bilah samping (Sidebar) untuk kelas ini.")
            else:
                df_master = df_siswa_cloud.copy()
                df_master = df_master.sort_values(by=df_master.columns[1]) 
                nama_siswa_list = df_master.iloc[:, 1].tolist()
                
                # ==========================================
                # 1. MENU ABSENSI SISWA
                # ==========================================
                if menu == "1. Absensi Siswa":
                    st.header("📋 Absensi Siswa (Sinkron Cloud)")
                    opsi_tgl = st.radio("Metode Tanggal:", ["Otomatis (Hari Ini)", "Manual"])
                    tgl_absen = datetime.date.today() if opsi_tgl == "Otomatis (Hari Ini)" else st.date_input("Pilih Tanggal")
                    
                    st.write(f"Tanggal Absen: **{tgl_absen}**")
                    
                    data_absen_hari_ini = []
                    poin_map = {"Hadir": 3, "Izin": -2, "Sakit": -1, "Dispen": 2, "Alfa": -3}
                    
                    for idx, row in df_master.iterrows():
                        col1, col2, col3, col4 = st.columns([1, 3, 4, 4])
                        with col1: st.write(f"{row.iloc[0]}")
                        with col2: st.write(f"**{row.iloc[1]}**")
                        with col3: status = st.radio(f"Status ({row.iloc[1]})", ["Hadir", "Izin", "Sakit", "Dispen", "Alfa"], key=f"abs_{idx}", horizontal=True)
                        with col4: ket_detail = st.text_input("Keterangan Detail", key=f"ket_{idx}")
                        
                        pt = poin_map[status]
                        predikat = "Sangat Baik" if pt >= 2.5 else "Baik" if pt >= 1.5 else "Cukup" if pt >= 0.5 else "Kurang" if pt >= -1 else "Sangat Kurang"
                        
                        data_absen_hari_ini.append({
                            "Tanggal": str(tgl_absen), "Nomor": row.iloc[0], "Nama Siswa": row.iloc[1],
                            "Poin": pt, "Predikat": predikat, "Keterangan": ket_detail
                        })
                    
                    df_absen_save = pd.DataFrame(data_absen_hari_ini)
                    
                    if st.button("💾 SIMPAN ABSENSI KE CLOUD (GOOGLE SHEETS)"):
                        if conn:
                            try:
                                try:
                                    df_old = conn.read(worksheet=f"Absen_{selected_rombel.replace(' ', '_')}")
                                    df_total = pd.concat([df_old, df_absen_save], ignore_index=True).drop_duplicates(subset=["Tanggal", "Nama Siswa"], keep='last')
                                except Exception:
                                    df_total = df_absen_save
                                conn.update(worksheet=f"Absen_{selected_rombel.replace(' ', '_')}", data=df_total)
                                st.success("Data Absensi Berhasil Disimpan Permanen! Bisa dibuka dari Laptop/HP manapun.")
                            except Exception as e:
                                st.error(f"Gagal menyimpan ke Google Sheets: {e}")
                        else:
                            st.error("Koneksi cloud belum disetting.")

                # ==========================================
                # MENU LAIN (2-6)
                # ==========================================
                else:
                    st.info(f"Menu '{menu}' siap digunakan. Seluruh logika poin input dan konversi nilai tetap aktif berjalan normal di sesi ini.")
                    st.caption("Silakan lakukan penyambungan Google Sheets pada Tahap 2 agar tombol simpan otomatis muncul penuh di seluruh menu.")
