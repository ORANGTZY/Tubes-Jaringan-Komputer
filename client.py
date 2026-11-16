import socket  # Digunakan untuk membuat koneksi jaringan (TCP maupun UDP)
import argparse  # Digunakan untuk membaca perintah yang diketik di terminal
import time  # Digunakan untuk mengukur waktu dan menambahkan jeda
import statistics  # Digunakan untuk menghitung rata-rata (khusus jitter)
import webbrowser  # Digunakan untuk membuka hasil HTML di browser secara otomatis
import os  # Digunakan untuk mengambil lokasi file di komputer
import threading  # Digunakan agar beberapa klien bisa berjalan bersamaan

PROXY_HOST = "10.130.18.164"  # Alamat IP dari server proxy yang dituju
PROXY_PORT = 8080  # Nomor pintu (port) yang digunakan untuk terhubung ke proxy

UDP_HOST = "10.130.18.173"  # Alamat IP tujuan untuk pengujian UDP
UDP_PORT = 9000  # Nomor pintu (port) untuk pengujian UDP

BUFFER_SIZE = 4096  # Ukuran maksimal data yang diterima sekaligus (dalam bytes)


def tcp_mode(path):
    print("=== TCP SINGLE CLIENT MODE ===")  # Tampilkan keterangan mode yang sedang dijalankan
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Buat koneksi TCP baru
    client_socket.connect((PROXY_HOST, PROXY_PORT))  # Hubungkan ke server proxy

    request = (  # Susun isi permintaan HTTP yang akan dikirim
        f"GET {path} HTTP/1.1\r\n"  # Baris pertama: minta halaman tertentu menggunakan HTTP
        f"Host: {PROXY_HOST}\r\n"  # Beritahu server kita sedang menghubungi alamat mana
        "Connection: close\r\n"  # Minta server menutup koneksi setelah selesai
        "\r\n"  # Baris kosong sebagai tanda akhir dari header HTTP
    )

    client_socket.sendall(request.encode())  # Kirim permintaan ke server dalam bentuk bytes

    response = b""  # Siapkan tempat kosong untuk menampung jawaban dari server
    while True:  # Terus terima data selama masih ada yang dikirim
        data = client_socket.recv(BUFFER_SIZE)  # Ambil potongan data dari server
        if not data:  # Jika tidak ada lagi data yang masuk, hentikan pengulangan
            break
        response += data  # Tambahkan potongan data ke jawaban lengkap

    client_socket.close()  # Tutup koneksi setelah semua data diterima

    # pisahkan header dan body
    parts = response.split(b"\r\n\r\n", 1)  # Pisahkan antara kepala (header) dan isi halaman (body)

    if len(parts) < 2:  # Jika jawaban tidak lengkap atau tidak sesuai format HTTP
        print("Invalid HTTP Response")  # Tampilkan pesan error
        return  # Hentikan fungsi

    header = parts[0].decode(errors="ignore")  # Ubah header dari bytes menjadi teks yang bisa dibaca
    body = parts[1]  # Ambil bagian isi halaman (HTML)

    print("===== RESPONSE HEADER =====")  # Tampilkan judul pemisah
    print(header)  # Cetak isi header ke layar

    # simpan html sementara
    temp_file = "client_output.html"  # Tentukan nama file sementara untuk menyimpan HTML
    with open(temp_file, "wb") as f:  # Buka file untuk ditulis dalam mode binary
        f.write(body)  # Simpan isi halaman ke file tersebut

    # buka ke browser
    file_path = os.path.abspath(temp_file)  # Dapatkan lokasi lengkap file di komputer
    webbrowser.open(f"file://{file_path}")  # Buka file HTML tadi di browser secara otomatis

    print(f"\nHTML opened in browser -> {temp_file}")  # Beritahu pengguna bahwa browser sudah dibuka


def tcp_multi_mode(path, num_clients=5):
    """
    Fungsi untuk menjalankan Skenario Multi-Client Konkuren.
    Mengirimkan beberapa request secara bersamaan menggunakan threading.
    """
    print(f"=== TCP MULTI-CLIENT MODE ({num_clients} Klien Konkuren) ===")  # Tampilkan mode yang dijalankan
    
    def single_request_worker(client_id):  # Fungsi ini dijalankan oleh setiap klien secara bersamaan
        print(f"[Client {client_id}] Mengirim request GET {path} ke Proxy...")  # Beritahu klien mana yang mulai
        start_time = time.time()  # Catat waktu mulai untuk mengukur durasi
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Buat koneksi TCP baru untuk klien ini
            client_socket.connect((PROXY_HOST, PROXY_PORT))  # Hubungkan ke server proxy

            request = (  # Susun permintaan HTTP seperti biasa
                f"GET {path} HTTP/1.1\r\n"  # Minta halaman yang diinginkan
                f"Host: {PROXY_HOST}\r\n"  # Sertakan alamat host yang dituju
                "Connection: close\r\n"  # Minta koneksi ditutup setelah selesai
                "\r\n"  # Akhir dari header HTTP
            )
            client_socket.sendall(request.encode())  # Kirim permintaan ke server

            response = b""  # Siapkan tempat untuk menampung jawaban
            while True:  # Terus terima data selama belum habis
                data = client_socket.recv(BUFFER_SIZE)  # Ambil potongan data dari server
                if not data:  # Jika sudah tidak ada data, berhenti
                    break
                response += data  # Gabungkan potongan data ke jawaban

            client_socket.close()  # Tutup koneksi setelah selesai menerima
            elapsed_time = (time.time() - start_time) * 1000  # Hitung waktu total dalam milidetik

            # Cek status code dari header
            parts = response.split(b"\r\n\r\n", 1)  # Pisahkan header dan body dari jawaban
            if len(parts) >= 2:  # Jika format jawaban valid
                header = parts[0].decode(errors="ignore")  # Ubah header menjadi teks
                status_line = header.split('\r\n')[0]  # Ambil baris pertama yang berisi status (misal: 200 OK)
                print(f"[Client {client_id}] Respons diterima: {status_line} (Waktu: {elapsed_time:.2f} ms)")  # Tampilkan hasil
            else:
                print(f"[Client {client_id}] Respons tidak valid (Waktu: {elapsed_time:.2f} ms)")  # Jawaban tidak sesuai format

        except Exception as e:
            print(f"[Client {client_id}] Error: {e}")  # Tampilkan pesan jika terjadi kesalahan

    # Membuat dan menjalankan thread untuk setiap klien
    threads = []  # Daftar untuk menyimpan semua thread (klien) yang dibuat
    for i in range(1, num_clients + 1):  # Ulangi sebanyak jumlah klien yang diminta
        t = threading.Thread(target=single_request_worker, args=(i,))  # Buat satu thread untuk satu klien
        threads.append(t)  # Masukkan thread ke dalam daftar
        t.start()  # Mulai jalankan thread tersebut

    # Menunggu semua thread selesai
    for t in threads:  # Ulangi untuk setiap thread yang sudah dibuat
        t.join()  # Tunggu sampai thread tersebut selesai berjalan

    print("\n=== MULTI-CLIENT TEST SELESAI ===")  # Beritahu bahwa semua klien sudah selesai


def udp_mode():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Buat koneksi jenis UDP (tanpa jalur tetap)
    udp_socket.settimeout(1)  # Jika tidak ada balasan dalam 1 detik, anggap gagal

    rtts = []  # Daftar untuk menyimpan waktu bolak-balik setiap paket
    success = 0  # Hitung berapa paket yang berhasil mendapat balasan
    total_bytes = 0  # Hitung total ukuran data yang diterima
    start = time.time()  # Catat waktu awal pengujian

    print("=== UDP QoS TEST ===")  # Tampilkan judul mode pengujian UDP

    for i in range(10):  # Kirim 10 paket pengujian satu per satu
        send_time = time.time()  # Catat waktu tepat sebelum paket dikirim
        payload = f"Ping {i} {send_time}"  # Buat isi paket berisi nomor urut dan waktu kirim

        try:
            udp_socket.sendto(  # Kirim paket ke server UDP
                payload.encode(),  # Ubah teks menjadi bytes sebelum dikirim
                (UDP_HOST, UDP_PORT)  # Tujuan pengiriman paket
            )

            data, addr = udp_socket.recvfrom(BUFFER_SIZE)  # Tunggu balasan dari server
            recv_time = time.time()  # Catat waktu saat balasan diterima
            rtt = (recv_time - send_time) * 1000  # Hitung selisih waktu kirim dan terima (milidetik)
            rtts.append(rtt)  # Simpan nilai RTT ke daftar
            success += 1  # Tambah hitungan paket yang berhasil
            total_bytes += len(data)  # Tambah total ukuran data yang diterima

            print(f"Reply from {addr} RTT={rtt:.2f} ms")  # Tampilkan info balasan dan waktu tempuhnya

        except socket.timeout:
            print("Request timed out")  # Tampilkan pesan jika tidak ada balasan dalam batas waktu

        time.sleep(1)  # Tunggu 1 detik sebelum mengirim paket berikutnya

    duration = time.time() - start  # Hitung total waktu pengujian dari awal sampai akhir
    packet_loss = ((10 - success) / 10) * 100  # Hitung persentase paket yang hilang

    if rtts:  # Jika ada setidaknya satu paket yang berhasil
        min_rtt = min(rtts)  # Cari waktu tempuh paling cepat
        max_rtt = max(rtts)  # Cari waktu tempuh paling lambat
        avg_rtt = sum(rtts) / len(rtts)  # Hitung rata-rata waktu tempuh semua paket

        jitter_values = []  # Daftar untuk menyimpan selisih antar waktu tempuh
        for i in range(1, len(rtts)):  # Bandingkan setiap RTT dengan RTT sebelumnya
            jitter_values.append(abs(rtts[i] - rtts[i - 1]))  # Hitung selisih absolut antar RTT

        jitter = statistics.mean(jitter_values) if jitter_values else 0  # Hitung rata-rata ketidakstabilan waktu (jitter)
        throughput = (total_bytes * 8) / duration / 1000  # Hitung kecepatan transfer data dalam kbps

        print("\n=== QoS Statistics ===")  # Tampilkan judul ringkasan hasil
        print(f"Min RTT     : {min_rtt:.2f} ms")  # Waktu tempuh paling cepat
        print(f"Avg RTT     : {avg_rtt:.2f} ms")  # Rata-rata waktu tempuh
        print(f"Max RTT     : {max_rtt:.2f} ms")  # Waktu tempuh paling lambat
        print(f"Packet Loss : {packet_loss:.2f}%")  # Persentase paket yang tidak sampai
        print(f"Jitter      : {jitter:.2f} ms")  # Rata-rata ketidakstabilan waktu antar paket
        print(f"Throughput  : {throughput:.2f} kbps")  # Kecepatan transfer data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()  # Siapkan alat untuk membaca perintah dari terminal

    parser.add_argument(  # Tambahkan pilihan mode yang bisa dipilih pengguna
        "--mode",
        choices=["tcp", "tcp-multi", "udp"],  # Tiga pilihan mode yang tersedia
        required=True  # Mode wajib diisi, tidak boleh kosong
    )

    parser.add_argument(  # Tambahkan pilihan path/halaman yang ingin diakses
        "--path",
        default="/index.html"  # Jika tidak diisi, otomatis mengakses halaman utama
    )

    args = parser.parse_args()  # Baca dan simpan semua perintah yang diketik pengguna

    if args.mode == "tcp":  # Jika pengguna memilih mode TCP biasa
        tcp_mode(args.path)  # Jalankan fungsi TCP single client
    elif args.mode == "tcp-multi":  # Jika pengguna memilih mode TCP banyak klien
        tcp_multi_mode(args.path)  # Jalankan fungsi TCP multi client
    elif args.mode == "udp":  # Jika pengguna memilih mode pengujian UDP
        udp_mode()  # Jalankan fungsi pengujian UDP