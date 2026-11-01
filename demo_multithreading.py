"""
Demo Multithreading dalam Praktik
Mata Kuliah Sistem Operasi - Kelompok 6

Program ini membandingkan eksekusi single-thread dan multi-thread
pada dua jenis pekerjaan:
  1. I/O-bound  : banyak menunggu (unduh file, baca disk, query database)
  2. CPU-bound  : banyak menghitung (mencari bilangan prima)

Cara menjalankan:
  python demo_multithreading.py          -> menu interaktif
  python demo_multithreading.py --semua  -> jalankan semua demo berurutan

Hanya memakai library bawaan Python (tidak perlu pip install).
"""

import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# ---------------------------------------------------------------------------
# Pengaturan demo
# ---------------------------------------------------------------------------
JUMLAH_FILE = 8          # banyaknya "file" yang diunduh di demo I/O
DETIK_PER_FILE = 1.0     # lama menunggu tiap file (simulasi jaringan)
JUMLAH_WORKER = 4        # banyaknya thread / proses
BATAS_PRIMA = 2_000_000  # cari bilangan prima dari 2 sampai angka ini

LEBAR_BAR = 50           # lebar diagram timeline di terminal


# ---------------------------------------------------------------------------
# Utilitas tampilan
# ---------------------------------------------------------------------------
def judul(teks):
    print("\n" + "=" * 64)
    print(f"  {teks}")
    print("=" * 64)


def gambar_timeline(catatan, total_waktu):
    """Menggambar diagram Gantt sederhana: kapan tiap tugas jalan, di thread mana."""
    if total_waktu <= 0:
        return
    print(f"\n  Timeline (1 kolom = {total_waktu / LEBAR_BAR:.2f} detik)")
    for nama_tugas, nama_thread, mulai, selesai in catatan:
        kiri = int(mulai / total_waktu * LEBAR_BAR)
        panjang = max(1, int((selesai - mulai) / total_waktu * LEBAR_BAR))
        bar = " " * kiri + "#" * panjang
        print(f"  {nama_tugas:<8} {nama_thread:<10} |{bar:<{LEBAR_BAR}}|")


def info_sistem():
    print(f"  Python      : {sys.version.split()[0]}")
    print(f"  Core CPU    : {os.cpu_count()} (logical)")
    print(f"  PID program : {os.getpid()}")
    # sys._is_gil_enabled() baru ada di Python 3.13+; versi lama selalu memakai GIL
    gil_aktif = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"  GIL Python  : {'AKTIF' if gil_aktif else 'NONAKTIF (free-threaded)'}")


# ---------------------------------------------------------------------------
# DEMO 1: Pekerjaan I/O-bound (banyak menunggu)
# ---------------------------------------------------------------------------
def unduh_file(nomor, titik_nol, catatan, kunci):
    """Simulasi mengunduh satu file. time.sleep() = menunggu jaringan.
    Saat menunggu, thread melepas CPU sehingga thread lain bisa jalan."""
    mulai = time.perf_counter() - titik_nol
    time.sleep(DETIK_PER_FILE)
    selesai = time.perf_counter() - titik_nol
    with kunci:  # kunci agar list tidak ditulis dua thread bersamaan
        catatan.append((f"file-{nomor}", threading.current_thread().name, mulai, selesai))
    return nomor


def demo_io_single():
    print("\n  [SINGLE-THREAD] Mengunduh file satu per satu...")
    catatan, kunci = [], threading.Lock()
    titik_nol = time.perf_counter()
    for i in range(1, JUMLAH_FILE + 1):
        unduh_file(i, titik_nol, catatan, kunci)
    total = time.perf_counter() - titik_nol
    gambar_timeline(catatan, total)
    print(f"\n  Total waktu: {total:.2f} detik")
    return total


def demo_io_multi():
    print(f"\n  [MULTI-THREAD] Mengunduh file dengan {JUMLAH_WORKER} thread...")
    catatan, kunci = [], threading.Lock()
    titik_nol = time.perf_counter()
    with ThreadPoolExecutor(max_workers=JUMLAH_WORKER, thread_name_prefix="thread") as pool:
        for i in range(1, JUMLAH_FILE + 1):
            pool.submit(unduh_file, i, titik_nol, catatan, kunci)
    total = time.perf_counter() - titik_nol
    catatan.sort(key=lambda c: c[2])
    gambar_timeline(catatan, total)
    print(f"\n  Total waktu: {total:.2f} detik")
    return total


def demo_io():
    judul("DEMO 1 - Pekerjaan I/O-bound (simulasi unduh file)")
    print(f"  {JUMLAH_FILE} file, masing-masing butuh {DETIK_PER_FILE:.1f} detik menunggu jaringan.")
    t_single = demo_io_single()
    t_multi = demo_io_multi()
    print("\n  Ringkasan:")
    print(f"    Single-thread : {t_single:6.2f} detik")
    print(f"    Multi-thread  : {t_multi:6.2f} detik")
    print(f"    Speedup       : {t_single / t_multi:6.2f}x lebih cepat")
    return {"single": t_single, "multi": t_multi}


# ---------------------------------------------------------------------------
# DEMO 2: Pekerjaan CPU-bound (banyak menghitung)
# ---------------------------------------------------------------------------
def hitung_prima(rentang):
    """Menghitung banyaknya bilangan prima di rentang [awal, akhir).
    Murni kerja CPU, tidak ada menunggu."""
    awal, akhir = rentang
    jumlah = 0
    for n in range(max(awal, 2), akhir):
        if n % 2 == 0:
            jumlah += n == 2
            continue
        i = 3
        prima = True
        while i * i <= n:
            if n % i == 0:
                prima = False
                break
            i += 2
        jumlah += prima
    return jumlah


def bagi_rentang(batas, bagian):
    langkah = batas // bagian
    rentang = [(i * langkah, (i + 1) * langkah) for i in range(bagian)]
    rentang[-1] = (rentang[-1][0], batas)
    return rentang


def demo_cpu():
    judul("DEMO 2 - Pekerjaan CPU-bound (menghitung bilangan prima)")
    print(f"  Menghitung bilangan prima dari 2 sampai {BATAS_PRIMA:,}".replace(",", "."))
    rentang = bagi_rentang(BATAS_PRIMA, JUMLAH_WORKER)

    print("\n  [SINGLE-THREAD] satu thread menghitung semuanya...")
    t0 = time.perf_counter()
    hasil_single = hitung_prima((0, BATAS_PRIMA))
    t_single = time.perf_counter() - t0
    print(f"    Ditemukan {hasil_single:,} prima dalam {t_single:.2f} detik".replace(",", "."))

    print(f"\n  [MULTI-THREAD] {JUMLAH_WORKER} thread, rentang dibagi rata...")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=JUMLAH_WORKER) as pool:
        hasil_thread = sum(pool.map(hitung_prima, rentang))
    t_thread = time.perf_counter() - t0
    print(f"    Ditemukan {hasil_thread:,} prima dalam {t_thread:.2f} detik".replace(",", "."))

    print(f"\n  [MULTI-PROCESS] {JUMLAH_WORKER} proses, rentang dibagi rata...")
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=JUMLAH_WORKER) as pool:
        hasil_proses = sum(pool.map(hitung_prima, rentang))
    t_proses = time.perf_counter() - t0
    print(f"    Ditemukan {hasil_proses:,} prima dalam {t_proses:.2f} detik".replace(",", "."))

    assert hasil_single == hasil_thread == hasil_proses, "Hasil hitungan berbeda!"

    print("\n  Ringkasan:")
    print(f"    Single-thread : {t_single:6.2f} detik")
    print(f"    Multi-thread  : {t_thread:6.2f} detik  ({t_single / t_thread:.2f}x)")
    print(f"    Multi-process : {t_proses:6.2f} detik  ({t_single / t_proses:.2f}x)")
    print("\n  Catatan: di Python standar, GIL membuat hanya satu thread yang boleh")
    print("  mengeksekusi bytecode pada satu waktu. Jadi thread tidak mempercepat")
    print("  kerja CPU. Proses terpisah punya GIL sendiri-sendiri, sehingga bisa")
    print("  benar-benar paralel di beberapa core.")
    return {"single": t_single, "thread": t_thread, "proses": t_proses}


# ---------------------------------------------------------------------------
# DEMO 3: Melihat thread langsung di sistem operasi
# ---------------------------------------------------------------------------
def pekerja_diam(detik):
    time.sleep(detik)


def demo_lihat_thread(detik=30):
    judul("DEMO 3 - Melihat thread di sistem operasi")
    jumlah_awal = threading.active_count()
    daftar = []
    for i in range(JUMLAH_WORKER):
        t = threading.Thread(target=pekerja_diam, args=(detik,), name=f"pekerja-{i + 1}")
        t.start()
        daftar.append(t)

    print(f"  PID program  : {os.getpid()}")
    print(f"  Thread aktif : {jumlah_awal} -> {threading.active_count()}")
    print("\n  Daftar thread (ID dari OS):")
    for t in threading.enumerate():
        print(f"    {t.name:<12} native id = {t.native_id}")

    pid = os.getpid()
    print(f"\n  Selama {detik} detik ke depan, cek di terminal lain:")
    print(f"    Linux  : ps -T -p {pid}      atau   top -H -p {pid}")
    print(f"    macOS  : ps -M {pid}")
    print( "    Windows: Task Manager > Details > klik kanan kolom > Select columns > Threads")
    print("\n  Semua thread di atas berada di SATU proses (PID sama), berbagi memori yang sama.")
    for t in daftar:
        t.join()
    print("  Thread pekerja selesai.")


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
def menu():
    while True:
        judul("DEMO MULTITHREADING - KELOMPOK 6")
        info_sistem()
        print("\n  1. Demo I/O-bound   (single vs multi-thread)")
        print("  2. Demo CPU-bound   (single vs multi-thread vs multi-process)")
        print("  3. Lihat thread di sistem operasi")
        print("  4. Jalankan semua")
        print("  0. Keluar")
        pilihan = input("\n  Pilih: ").strip()
        if pilihan == "1":
            demo_io()
        elif pilihan == "2":
            demo_cpu()
        elif pilihan == "3":
            demo_lihat_thread()
        elif pilihan == "4":
            jalankan_semua()
        elif pilihan == "0":
            break
        input("\n  Tekan Enter untuk kembali ke menu...")


def jalankan_semua(detik_lihat=10):
    judul("DEMO MULTITHREADING - KELOMPOK 6")
    info_sistem()
    demo_io()
    demo_cpu()
    demo_lihat_thread(detik_lihat)


if __name__ == "__main__":
    if "--semua" in sys.argv:
        jalankan_semua()
    else:
        menu()
