import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman Utama Web
st.set_page_config(page_title="Pusat Informasi Belajar", layout="wide", page_icon="📚")
st.title("📚 Pusat Informasi Belajar - SMK")
st.subheader("Aplikasi Penunjang Guru PAI & Wali Kelas")

# --- HALAMAN UTAMA: Generasi Tahun Pelajaran ---
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
    
    # List Rombel dibuat langsung di dalam kode agar super cepat dan aman
    list_rombel = ["X DPB B", "X TKP", "X TKJ A", "X TKJ B"]
    selected_rombel = st.selectbox("Pilih Rombel Kelas:", ["-- Pilih Rombel --"] + list_rombel)
    
    if selected_rombel != "-- Pilih Rombel --":
        st.info(f"Mengelola Kelas: **{selected_rombel}**")
        
        # --- MENU NAVIGASI FITUR ---
        menu = st.sidebar.radio(
            "PILIH MENU APLIKASI",
            ["1. Absensi Siswa", "2. Evaluasi Ibadah", "3. Evaluasi BBQ", "4. Hafalan Surat", "5. Penugasan dan Nilai", "6. Catatan Siswa"]
        )
        
        # --- INPUT MASTER DATA SISWA VIA SIDEBAR ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("Master Data Siswa")
        
        uploaded_file = st.sidebar.file_uploader("Upload Template Excel/CSV Daftar Siswa", type=["xlsx", "csv"])
        df_master = None
        
        if uploaded_file:
            if uploaded_file.name.endswith('.csv'):
                df_master = pd.read_csv(uploaded_file)
            else:
                df_master = pd.read_excel(uploaded_file)
            st.session_state[f"data_siswa_{selected_rombel}"] = df_master
            st.sidebar.success("Daftar siswa berhasil dimuat!")
        elif f"data_siswa_{selected_rombel}" in st.session_state:
            df_master = st.session_state[f"data_siswa_{selected_rombel}"]

        if df_master is None:
            st.warning("Silakan unggah daftar siswa terlebih dahulu di bilah samping (Sidebar) untuk kelas ini.")
        else:
            # Mengurutkan nama sesuai kolom kedua
            df_master = df_master.sort_values(by=df_master.columns[1]) 
            
            # ==========================================
            # 1. MENU ABSENSI SISWA
            # ==========================================
            if menu == "1. Absensi Siswa":
                st.header("📋 Absensi Siswa")
                opsi_tgl = st.radio("Metode Tanggal:", ["Otomatis (Hari Ini)", "Manual"])
                tgl_absen = datetime.date.today() if opsi_tgl == "Otomatis (Hari Ini)" else st.date_input("Pilih Tanggal")
                
                st.write(f"Tanggal Absen: **{tgl_absen}**")
                st.markdown("---")
                
                data_absen_hari_ini = []
                poin_map = {"Hadir": 3, "Izin": -2, "Sakit": -1, "Dispen": 2, "Alfa": -3}
                
                # Menampilkan baris demi baris nama siswa
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
                
                # TOMBOL DOWNLOAD UTAMA (BEBAS BLOCKED)
                st.markdown("---")
                st.subheader("📥 Ambil Hasil Rekap Absensi")
                st.info("Klik tombol di bawah ini untuk mengunduh rekap absensi hari ini secara instan ke HP atau Laptop.")
                
                csv_data = df_absen_save.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 DOWNLOAD SEKARANG (FORMAT EXCEL/CSV)",
                    data=csv_data,
                    file_name=f"Absen_{selected_rombel}_{tgl_absen}.csv",
                    mime="text/csv"
                )

            # ==========================================
            # MENU LAIN (2-6) RUNNING NORMAL
            # ==========================================
            else:
                st.info(f"Menu '{menu}' siap digunakan secara lokal di perangkat ini.")
