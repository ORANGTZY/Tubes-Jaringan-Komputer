import socket  # Digunakan untuk membuat koneksi jaringan antar komputer
import threading  # Digunakan agar server TCP dan UDP bisa berjalan bersamaan
import os  # Digunakan untuk membaca lokasi file di komputer
import mimetypes  # Digunakan untuk menebak jenis file (misal: HTML, gambar, CSS)
from datetime import datetime  # Digunakan untuk menampilkan waktu saat ini di log

HOST = "0.0.0.0"  # Artinya server menerima koneksi dari alamat IP mana pun
TCP_PORT = 8000  # Nomor pintu (port) yang digunakan untuk melayani permintaan web
UDP_PORT = 9000  # Nomor pintu (port) yang digunakan untuk pengujian UDP
BUFFER_SIZE = 4096  # Ukuran maksimal data yang diterima sekaligus (dalam bytes)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Dapatkan lokasi folder tempat file server ini berada


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")  # Cetak pesan beserta waktu saat ini ke layar


def build_response(status, content, content_type="text/html"):
    header = (  # Susun bagian kepala (header) dari jawaban HTTP
        f"HTTP/1.1 {status}\r\n"  # Baris pertama: versi HTTP dan kode status (misal: 200 OK)
        f"Content-Type: {content_type}\r\n"  # Beritahu browser jenis konten yang dikirim
        f"Content-Length: {len(content)}\r\n"  # Beritahu browser ukuran isi konten dalam bytes
        "Connection: close\r\n"  # Minta browser menutup koneksi setelah menerima jawaban
        "\r\n"  # Baris kosong sebagai tanda pemisah antara header dan isi konten
    ).encode()  # Ubah seluruh header dari teks menjadi bytes agar bisa dikirim lewat jaringan

    return header + content  # Gabungkan header dan isi konten menjadi satu jawaban lengkap


def serve_file(path):
    if path == "/":  # Jika pengguna mengakses halaman utama tanpa nama file
        path = "/index.html"  # Otomatis arahkan ke file index.html

    filepath = os.path.join(BASE_DIR, path.lstrip("/"))  # Gabungkan lokasi folder server dengan nama file yang diminta

    if not os.path.exists(filepath):  # Jika file yang diminta tidak ditemukan di server
        filepath = os.path.join(BASE_DIR, "status", "404.html")  # Arahkan ke halaman error 404

        with open(filepath, "rb") as f:  # Buka file halaman error 404
            content = f.read()  # Baca seluruh isi file tersebut

        return build_response("404 Not Found", content)  # Kirim jawaban dengan status 404 (tidak ditemukan)

    try:
        with open(filepath, "rb") as f:  # Buka file yang diminta dalam mode baca binary
            content = f.read()  # Baca seluruh isi file

        content_type = mimetypes.guess_type(filepath)[0]  # Tebak jenis file berdasarkan ekstensinya (misal: .html, .png)

        if not content_type:  # Jika jenis file tidak bisa dikenali
            content_type = "application/octet-stream"  # Gunakan jenis umum agar tetap bisa dikirim

        return build_response("200 OK", content, content_type)  # Kirim jawaban sukses beserta isi file

    except Exception as e:
        log(f"500 ERROR: {e}")  # Catat pesan error ke layar jika terjadi masalah saat membaca file

        filepath = os.path.join(BASE_DIR, "status", "500.html")  # Arahkan ke halaman error 500

        with open(filepath, "rb") as f:  # Buka file halaman error 500
            content = f.read()  # Baca isi file tersebut

        return build_response(  # Kirim jawaban dengan status 500 (kesalahan server)
            "500 Internal Server Error",
            content
        )


def handle_client(client_socket, addr):
    try:
        request = client_socket.recv(BUFFER_SIZE).decode()  # Terima dan baca permintaan yang dikirim oleh browser/klien

        if not request:  # Jika permintaan kosong atau tidak ada isinya
            client_socket.close()  # Tutup koneksi tanpa melakukan apa-apa
            return  # Keluar dari fungsi

        request_line = request.splitlines()[0]  # Ambil baris pertama dari permintaan (berisi metode, path, versi HTTP)

        method, path, version = request_line.split()  # Pisahkan baris pertama menjadi tiga bagian

        log(f"{addr} -> {method} {path}")  # Catat siapa yang mengakses dan halaman apa yang diminta

        if method != "GET":  # Jika metode yang digunakan bukan GET (hanya GET yang didukung)
            client_socket.close()  # Tutup koneksi karena metode tidak didukung
            return  # Keluar dari fungsi

        response = serve_file(path)  # Cari dan siapkan file yang diminta oleh klien

        client_socket.sendall(response)  # Kirim seluruh jawaban (header + isi file) ke klien

    except Exception as e:
        log(f"ERROR: {e}")  # Tampilkan pesan error jika ada masalah saat memproses permintaan

    finally:
        client_socket.close()  # Selalu tutup koneksi di akhir, baik berhasil maupun gagal


def tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Buat soket bertipe TCP untuk melayani web

    server_socket.bind((HOST, TCP_PORT))  # Daftarkan server agar mendengarkan di alamat dan port yang ditentukan
    server_socket.listen(10)  # Izinkan hingga 10 koneksi mengantri sebelum diproses

    log(f"HTTP Server running on port {TCP_PORT}")  # Beritahu bahwa server web sudah aktif

    while True:  # Terus berjalan dan siap menerima koneksi baru
        client_socket, addr = server_socket.accept()  # Tunggu dan terima koneksi dari klien baru

        thread = threading.Thread(  # Buat jalur pemrosesan baru khusus untuk klien ini
            target=handle_client,  # Tugaskan fungsi handle_client untuk menangani klien tersebut
            args=(client_socket, addr)  # Kirimkan koneksi dan alamat klien ke fungsi tersebut
        )

        thread.start()  # Mulai jalankan pemrosesan klien secara bersamaan dengan klien lainnya


def udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Buat soket bertipe UDP (tanpa jalur tetap)

    udp_socket.bind((HOST, UDP_PORT))  # Daftarkan server UDP agar mendengarkan di port yang ditentukan

    log(f"UDP Echo Server running on port {UDP_PORT}")  # Beritahu bahwa server UDP sudah aktif

    while True:  # Terus berjalan dan siap menerima data kapan saja
        data, addr = udp_socket.recvfrom(BUFFER_SIZE)  # Terima paket data dari klien mana pun yang mengirim

        udp_socket.sendto(data, addr)  # Kembalikan data yang sama persis ke pengirimnya (echo)


if __name__ == "__main__":
    tcp_thread = threading.Thread(target=tcp_server)  # Siapkan server TCP agar bisa berjalan di jalur tersendiri
    udp_thread = threading.Thread(target=udp_server)  # Siapkan server UDP agar bisa berjalan di jalur tersendiri

    tcp_thread.start()  # Mulai jalankan server TCP
    udp_thread.start()  # Mulai jalankan server UDP

    tcp_thread.join()  # Tunggu server TCP selesai (biasanya tidak berhenti selama program aktif)
    udp_thread.join()  # Tunggu server UDP selesai (biasanya tidak berhenti selama program aktif)