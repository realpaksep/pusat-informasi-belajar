import streamlit as st
import pandas as pd
import datetime
import io

# Konfigurasi Halaman Utama Web
st.set_page_config(page_title="Pusat Informasi Belajar", layout="wide", page_icon="📚")
st.title("📚 Pusat Informasi Belajar - SMK")
st.subheader("Aplikasi Penunjang Guru PAI & Wali Kelas")

# Inisialisasi Database di Server Web
if "db_siswa" not in st.session_state:
    st.session_state.db_siswa = None
if "db_tugas" not in st.session_state:
    st.session_state.db_tugas = []

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
    
    # --- MENU ROMBEL KELAS ---
    rombel_input = st.text_input("Input Rombel Kelas Baru (Contoh: KELAS X TKJ A, KELAS XI AKL B):")
    if "list_rombel" not in st.session_state:
        st.session_state.list_rombel = []
        
    if st.button("Tambah Rombel"):
        if rombel_input and rombel_input not in st.session_state.list_rombel:
            st.session_state.list_rombel.append(rombel_input.upper())
            st.rerun()

    if st.session_state.list_rombel:
        selected_rombel = st.selectbox("Pilih Rombel Kelas:", ["-- Pilih Rombel --"] + st.session_state.list_rombel)
        
        if selected_rombel != "-- Pilih Rombel --":
            st.info(f"Mengelola Kelas: **{selected_rombel}**")
            
            # --- MENU NAVIGASI FITUR ---
            menu = st.sidebar.radio(
                "PILIH MENU APLIKASI",
                ["1. Absensi Siswa", "2. Evaluasi Ibadah", "3. Evaluasi BBQ", "4. Hafalan Surat", "5. Penugasan dan Nilai", "6. Catatan Siswa"]
            )
            
            # --- PROSES IMPORT DATA SISWA ---
            st.sidebar.markdown("---")
            st.sidebar.subheader("Import Master Data Siswa")
            uploaded_file = st.sidebar.file_uploader("Upload Template Excel atau CSV (Kolom: Nomor, Nama Siswa)", type=["xlsx", "csv"])
            
            if uploaded_file:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.db_siswa = pd.read_csv(uploaded_file)
                else:
                    st.session_state.db_siswa = pd.read_excel(uploaded_file)
                st.sidebar.success("Data Siswa Berhasil Dimuat!")

            if st.session_state.db_siswa is None:
                st.warning("Silakan unggah/import daftar nama siswa terlebih dahulu melalui menu di bilah samping (Sidebar) untuk mulai mengisi penilaian.")
            else:
                df_master = st.session_state.db_siswa.copy()
                df_master = df_master.sort_values(by=df_master.columns[1]) # Urut Abjad Nama
                nama_siswa_list = df_master.iloc[:, 1].tolist()
                
                # Fungsi pembantu untuk konversi Excel ke bytes siap download
                def to_excel_bytes(df_to_download):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_to_download.to_excel(writer, index=False, sheet_name='Data')
                    return output.getvalue()
                
                # ==========================================
                # 1. MENU ABSENSI SISWA
                # ==========================================
                if menu == "1. Absensi Siswa":
                    st.header("📋 Absensi Siswa")
                    
                    opsi_tgl = st.radio("Metode Tanggal:", ["Otomatis (Hari Ini)", "Manual"])
                    tgl_absen = datetime.date.today() if opsi_tgl == "Otomatis (Hari Ini)" else st.date_input("Pilih Tanggal")
                    
                    st.write(f"Tanggal Absen: **{tgl_absen}**")
                    
                    data_absen_hari_ini = []
                    poin_map = {"Hadir": 3, "Izin": -2, "Sakit": -1, "Dispen": 2, "Alfa": -3}
                    
                    for idx, row in df_master.iterrows():
                        col1, col2, col3, col4 = st.columns([1, 3, 4, 4])
                        with col1:
                            st.write(f"{row.iloc[0]}")
                        with col2:
                            st.write(f"**{row.iloc[1]}**")
                        with col3:
                            status = st.radio(f"Status ({row.iloc[1]})", ["Hadir", "Izin", "Sakit", "Dispen", "Alfa"], key=f"abs_{idx}", horizontal=True)
                        with col4:
                            ket_detail = st.text_input("Keterangan Detail", key=f"ket_{idx}", placeholder="Alasan izin/sakit")
                        
                        pt = poin_map[status]
                        predikat = "Sangat Baik" if pt >= 2.5 else "Baik" if pt >= 1.5 else "Cukup" if pt >= 0.5 else "Kurang" if pt >= -1 else "Sangat Kurang"
                        
                        data_absen_hari_ini.append({
                            "Nomor": row.iloc[0],
                            "Nama Siswa": row.iloc[1],
                            f"{tgl_absen} (Poin)": pt,
                            "Jumlah Poin": pt,
                            "Predikat": predikat,
                            "Keterangan": ket_detail
                        })
                    
                    df_export_absen = pd.DataFrame(data_absen_hari_ini)
                    
                    st.markdown("---")
                    st.subheader("Ekspor Data Absensi")
                    st.download_button(
                        label="📥 Download File Excel Absensi",
                        data=to_excel_bytes(df_export_absen),
                        file_name=f"Absensi_{selected_rombel}_{tgl_absen}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # ==========================================
                # 2. MENU EVALUASI IBADAH
                # ==========================================
                elif menu == "2. Evaluasi Ibadah":
                    st.header("🧎 Evaluasi Ibadah Shalat Fardu")
                    siswa_pilih = st.selectbox("Pilih Nama Siswa (Abjad):", nama_siswa_list)
                    
                    item_ibadah = [
                        "Niat shalat Isya'", "Niat shalat Subuh", "Niat shalat Dzuhur", "Niat shalat Ashar", "Niat shalat Maghrib",
                        "Do'a iftitah", "Surat Alfatihah", "Do'a Rukuk", "Do'a I'tidal", "Do'a Sujud", "Do'a Duduk Iftirassy",
                        "Do'a Tasyahud Awal", "Do'a Tasyahud Akhir"
                    ]
                    
                    predikat_ibadah_map = {"Sangat Baik": 5, "Baik": 4, "Cukup": 3, "Kurang": 2, "Belum Hafal": 1}
                    skor_total = 0
                    row_data_ibadah = {"Nomor": nama_siswa_list.index(siswa_pilih)+1, "Nama Siswa": siswa_pilih}
                    
                    st.markdown(f"### Lembar Penilaian: **{siswa_pilih}**")
                    for i, item in enumerate(item_ibadah, 1):
                        col_item, col_pred, col_catat = st.columns([3, 4, 5])
                        with col_item:
                            st.write(f"{i}. {item}")
                        with col_pred:
                            pred = st.selectbox(f"Predikat {i}", list(predikat_ibadah_map.keys()), key=f"ibadah_{i}")
                        with col_catat:
                            catatan = st.text_input(f"Catatan {i}", key=f"catat_ibadah_{i}")
                        
                        poin_item = predikat_ibadah_map[pred]
                        skor_total += poin_item
                        row_data_ibadah[f"I-{i}"] = poin_item
                    
                    rata_rata = round(skor_total / 13, 2)
                    predikat_akhir = "Sangat Baik" if rata_rata >= 4.5 else "Baik" if rata_rata >= 3.5 else "Cukup" if rata_rata >= 2.5 else "Kurang" if rata_rata >= 1.5 else "Belum Hafal"
                    
                    row_data_ibadah["Jumlah Nilai"] = skor_total
                    row_data_ibadah["Rata-rata"] = rata_rata
                    row_data_ibadah["Predikat Akhir"] = predikat_akhir
                    
                    df_export_ibadah = pd.DataFrame([row_data_ibadah])
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Rekap Excel Evaluasi Ibadah",
                        data=to_excel_bytes(df_export_ibadah),
                        file_name=f"Evaluasi_Ibadah_{selected_rombel}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                # ==========================================
                # 3. MENU EVALUASI BBQ
                # ==========================================
                elif menu == "3. Evaluasi BBQ":
                    st.header("📖 Evaluasi Bimbingan Baca Al-Qur'an (BBQ)")
                    
                    data_bbq_all = []
                    skor_bbq_map = {"Sangat Lancar": 90, "Lancar": 85, "Kurang Lancar": 75, "Tidak Lancar": 65, "Lupa": 55}
                    
                    for idx, nama in enumerate(nama_siswa_list, 1):
                        col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 3])
                        with col1:
                            st.write(f"{idx}")
                        with col2:
                            st.write(f"**{nama}**")
                        with col3:
                            level = st.selectbox(f"Level", ["Alqur'an", "Iqro' 1", "Iqro' 2", "Iqro' 3", "Iqro' 4", "Iqro' 5", "Iqro' 6"], key=f"lvl_{idx}")
                        with col4:
                            pred_bbq = st.selectbox(f"Predikat", ["Sangat Lancar", "Lancar", "Kurang Lancar", "Tidak Lancar", "Lupa"], key=f"pbbq_{idx}")
                        with col5:
                            catat_bbq = st.text_input("Catatan", key=f"cbbq_{idx}")
                            
                        data_bbq_all.append({
                            "Nomor": idx,
                            "Nama Siswa": nama,
                            "Level": level,
                            "Predikat": pred_bbq,
                            "Nilai": skor_bbq_map[pred_bbq],
                            "Catatan": catat_bbq
                        })
                    
                    df_export_bbq = pd.DataFrame(data_bbq_all)
                    df_export_bbq = df_export_bbq.sort_values(by="Nilai", ascending=False)
                    
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Rekap Urutan Kelancaran BBQ",
                        data=to_excel_bytes(df_export_bbq),
                        file_name=f"Evaluasi_BBQ_{selected_rombel}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                # ==========================================
                # 4. HAFALAN SURAT (JUZ 30)
                # ==========================================
                elif menu == "4. Hafalan Surat":
                    st.header("🕌 Hafalan Surat Pendek (Juz 30)")
                    siswa_pilih = st.selectbox("Pilih Nama Siswa (Abjad):", nama_siswa_list, key="hafalan_siswa")
                    
                    list_surat = [
                        "An-nas", "Al-Falaq", "Al-Ikhlas", "Al-Lahab", "An-Nasr", "Al-Kafirun", "Al-Kautsar", "Al-Ma'un", 
                        "Quraisy", "Al-Fil", "Al-Humazah", "Al-'Asr", "At-Takatsur", "Al-Qari'ah", "Al-'Adiyat", "Al-Zalzalah", 
                        "Al-Bayyinah", "Al-Qadr", "Al-'Alaq", "At-Tin", "Asy-Syarh", "Ad-Duha", "Al-Lail", "As-Syams", 
                        "Al-Balad", "Al-Fajr", "Al-Ghasiyah", "Al-'Ala", "At-Tariq", "Al-Buruj", "Al-Insyiqaq", "Al-Mutaffifin", 
                        "Al-Infitar", "At-Takwir", "'Abasa", "An-Nazi'at", "An-Naba'"
                    ]
                    
                    predikat_surat_map = {"Sangat Baik": 5, "Baik": 4, "Cukup": 3, "Kurang": 2, "Belum Hafal": 1}
                    skor_total_surat = 0
                    row_data_surat = {"Nomor": nama_siswa_list.index(siswa_pilih)+1, "Nama Siswa": siswa_pilih}
                    
                    st.markdown(f"### Setoran Hafalan: **{siswa_pilih}**")
                    for i, surat in enumerate(list_surat, 1):
                        col_s, col_p, col_c = st.columns([3, 4, 5])
                        with col_s:
                            st.write(f"S{i}. Surat {surat}")
                        with col_p:
                            p_surat = st.selectbox(f"Nilai S{i}", list(predikat_surat_map.keys()), key=f"srt_{i}")
                        with col_c:
                            c_surat = st.text_input(f"Catatan S{i}", key=f"csrt_{i}")
                            
                        poin_s = predikat_surat_map[p_surat]
                        skor_total_surat += poin_s
                        row_data_surat[f"S{i}"] = poin_s
                        
                    rata_surat = round(skor_total_surat / 37, 2)
                    pred_akhir_surat = "Sangat Baik" if rata_surat >= 4.5 else "Baik" if rata_surat >= 3.5 else "Cukup" if rata_surat >= 2.5 else "Kurang"
                    
                    row_data_surat["Jumlah Skor"] = skor_total_surat
                    row_data_surat["Rata-rata"] = rata_surat
                    row_data_surat["Predikat"] = pred_akhir_surat
                    
                    df_export_surat = pd.DataFrame([row_data_surat])
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Rekap Excel Hafalan Surat",
                        data=to_excel_bytes(df_export_surat),
                        file_name=f"Hafalan_Surat_{selected_rombel}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                # ==========================================
                # 5. PENUGASAN DAN NILAI
                # ==========================================
                elif menu == "5. Penugasan dan Nilai":
                    st.header("📝 Manajemen Penugasan & Nilai")
                    
                    opsi_tgl_tgs = st.radio("Metode Tanggal Tugas:", ["Otomatis", "Manual"], key="tgs_tgl")
                    tgl_tugas = datetime.date.today() if opsi_tgl_tgs == "Otomatis" else st.date_input("Tanggal Tugas", key="tgs_man")
                    
                    judul_tugas = st.text_input("Judul Tugas")
                    link_tugas = st.text_input("Link Referensi Internet / Berkas Tugas Cloud")
                    
                    st.markdown("---")
                    st.subheader("Daftar Penilaian Siswa")
                    
                    data_tugas_hari_ini = []
                    for idx, nama in enumerate(nama_siswa_list, 1):
                        col1, col2, col3, col4 = st.columns([1, 4, 3, 4])
                        with col1:
                            st.write(f"{idx}")
                        with col2:
                            st.write(f"**{nama}**")
                        with col3:
                            status_kumpul = st.selectbox(f"Keterangan", ["dikumpul", "belum dikumpul"], key=f"kumpul_{idx}")
                        with col4:
                            if status_kumpul == "belum dikumpul":
                                nilai_tgs = st.number_input("Nilai", value=0, disabled=True, key=f"nil_{idx}")
                            else:
                                nilai_tgs = st.number_input("Nilai", min_value=0, max_value=100, value=80, key=f"nil_{idx}")
                                
                        data_tugas_hari_ini.append({
                            "Nomor": idx,
                            "Nama Siswa": nama,
                            "Nilai Tugas 1": nilai_tgs,
                            "Jumlah Nilai": nilai_tgs,
                            "Nilai Rata-rata": nilai_tgs
                        })
                        
                    if st.button("Simpan Informasi Tugas ke Log"):
                        st.session_state.db_tugas.append({
                            "Nomor": len(st.session_state.db_tugas) + 1,
                            "Tanggal Tugas": tgl_tugas,
                            "Judul Tugas": judul_tugas,
                            "Link/File Tugas": link_tugas if link_tugas else "Lokal"
                        })
                        st.success("Log Tugas berhasil dicatat!")
                    
                    # Membuat lembar excel terpadu
                    df_export_tugas = pd.DataFrame(data_tugas_hari_ini)
                    
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download File Excel Penugasan",
                        data=to_excel_bytes(df_export_tugas),
                        file_name=f"Penugasan_{selected_rombel}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                # ==========================================
                # 6. CATATAN SISWA (SIKAP)
                # ==========================================
                elif menu == "6. Catatan Siswa":
                    st.header("✍️ Catatan Khusus Perilaku Siswa")
                    
                    opsi_tgl_ctt = st.radio("Metode Tanggal Catatan:", ["Otomatis", "Manual"], key="ctt_tgl")
                    tgl_ctt = datetime.date.today() if opsi_tgl_ctt == "Otomatis" else st.date_input("Tanggal Catatan", key="ctt_man")
                    
                    data_catatan_all = []
                    poin_sikap_map = {"positif": 5, "standar": 2, "negatif": -3}
                    
                    for idx, nama in enumerate(nama_siswa_list, 1):
                        col1, col2, col3, col4 = st.columns([1, 3, 3, 5])
                        with col1:
                            st.write(f"{idx}")
                        with col2:
                            st.write(f"**{nama}**")
                        with col3:
                            pred_sikap = st.selectbox("Predikat Sikap", ["standar", "positif", "negatif"], key=f"skp_{idx}")
                        with col4:
                            catat_guru = st.text_input("Catatan Guru", key=f"cs__{idx}")
                        
                        poin_s = poin_sikap_map[pred_sikap]
                        pred_akhir = "positif" if poin_s > 2 else "standar" if poin_s == 2 else "negatif"
                        
                        data_catatan_all.append({
                            "Nomor": idx,
                            "Nama Siswa": nama,
                            "Skor Rata-rata Sikap": float(poin_s),
                            "Predikat": pred_akhir
                        })
                        
                    df_export_catatan = pd.DataFrame(data_catatan_all)
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Rekap Jurnal Sikap Siswa",
                        data=to_excel_bytes(df_export_catatan),
                        file_name=f"Catatan_Siswa_{selected_rombel}_{tgl_ctt}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
