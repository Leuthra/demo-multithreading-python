# Demo Multithreading dalam Praktik

Tugas kelompok Sistem Operasi, Kelompok 6: membandingkan single-thread dan multi-thread.

## Cara menjalankan

Butuh Python 3.8 atau lebih baru. Tidak perlu install library apa pun.

```bash
python demo_multithreading.py          # menu interaktif
python demo_multithreading.py --semua  # jalankan semua demo berurutan
```

## Isi demo

| Menu | Demo | Yang ditunjukkan |
| --- | --- | --- |
| 1 | I/O-bound | 8 "unduhan" @1 detik: single-thread ~8 detik, 4 thread ~2 detik, lengkap dengan timeline |
| 2 | CPU-bound | Hitung bilangan prima sampai 2 juta: thread tidak lebih cepat (GIL), proses lebih cepat |
| 3 | Thread di OS | Membuat 4 thread dan menampilkan ID-nya agar bisa dicek dengan `ps -T`, `top -H` atau Task Manager |

Angka di bagian atas file (`JUMLAH_FILE`, `JUMLAH_WORKER`, `BATAS_PRIMA`) boleh diubah untuk mencoba skenario lain saat presentasi.

## Backup demo

Dipakai hanya jika demo langsung terkendala teknis.

- [`shots/video_demo.mp4`](shots/video_demo.mp4): rekaman layar saat `--semua` dijalankan (±1 menit), termasuk `top` saat Demo 2 dan `ps -T` saat Demo 3.
- `shots/*.png` dan `hasil_demo.txt`: screenshot dan output lengkap program.

## Catatan

- **Speedup multi-process tidak sampai 4x.** `hasil_demo.txt` dibuat di mesin dengan 8 core (Python 3.14), dan multi-process hasilnya 2,72x, bukan 4x. Ada dua penyebab. Pertama, jumlah core: di mesin dengan core lebih sedikit dari `JUMLAH_WORKER`, speedup paling banyak sama dengan jumlah core. Kedua, pembagian kerja tidak seimbang: `bagi_rentang()` membagi rentang angka sama rata, padahal mengecek angka besar lebih mahal. Rentang terakhir (1,5 juta–2 juta) memikul sekitar 35% total kerja, jadi speedup maksimalnya sekitar 2,8x. Ini terlihat di `shots/top_proses.txt`: 3 worker masih di sekitar 99% CPU, sedangkan worker dengan rentang paling ringan sudah turun ke 56%. Totalnya sekitar 350% (hampir 4 core). Bandingkan dengan `shots/top_thread.txt`: 4 thread totalnya hanya sekitar 100% (1 core) karena GIL.
- **Proses tambahan di `top_proses.txt`.** Di Python 3.14, Linux memakai metode *forkserver* untuk `ProcessPoolExecutor`. Akibatnya, selain 4 worker, ada juga proses forkserver dan resource tracker dengan %CPU 0.
- **Error di Demo 1 multi-thread tidak ditampilkan.** Hasil `pool.submit()` tidak disimpan, jadi kalau `unduh_file` gagal, error-nya hilang tanpa pesan. Untuk demo ini aman karena `time.sleep()` tidak pernah gagal. Pada program sungguhan, simpan future-nya lalu panggil `.result()`.
- **Python free-threaded.** Pada build Python 3.13t ke atas (PEP 703), GIL bisa dinonaktifkan dan `info_sistem()` akan menampilkan status itu. Di build tersebut, multi-thread pada Demo 2 *bisa* ikut lebih cepat, jadi bisa dijadikan bahan diskusi tambahan.

## Referensi

- Dokumentasi Python `threading`: https://docs.python.org/3/library/threading.html
- Dokumentasi Python `concurrent.futures`: https://docs.python.org/3/library/concurrent.futures.html
- PEP 703, Making the Global Interpreter Lock Optional: https://peps.python.org/pep-0703/
