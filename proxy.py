# Mengimpor modul/library bawaan Python yang dibutuhkan
import socket     # Untuk komunikasi jaringan via TCP/UDP
import threading  # Untuk menangani banyak klien secara bersamaan (multithreading)
import os         # Untuk berinteraksi dengan sistem operasi (seperti cek file/folder)
import hashlib    # Untuk melakukan enkripsi/hashing (membuat nama file cache unik)
import time       # Untuk menghitung waktu respons

# Konfigurasi alamat IP dan Port untuk Proxy Server ini
PROXY_HOST = "10.130.18.74"
PROXY_PORT = 8080

# Konfigurasi alamat IP dan Port untuk Server Tujuan (Server Utama)
SERVER_HOST = "10.130.18.70"
SERVER_PORT = 8000

# Batas maksimal ukuran data yang diterima dalam satu waktu (4 Kilobytes)
BUFFER_SIZE = 4096

# Nama folder untuk menyimpan file cache
CACHE_DIR = "cache"

# Mengecek apakah folder cache sudah ada. Jika belum, buat foldernya.
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Membuat 'kunci' (lock) agar saat beberapa klien mengakses file cache yang sama,
# datanya tidak rusak atau saling bertabrakan (mencegah race condition).
lock = threading.Lock()


def log(message):
    # Fungsi sederhana untuk mencetak aktivitas proxy ke terminal
    print(f"[PROXY] {message}")


def cache_name(path):
    # Mengubah path file (misal: /index.html) menjadi string acak (MD5 Hash)
    # Ini berguna agar nama file cache aman dan seragam di dalam sistem operasi
    return hashlib.md5(path.encode()).hexdigest()


def get_cache_path(path):
    # Menggabungkan nama folder cache dengan nama file hash
    # Contoh output: "cache/a1b2c3d4e5f6..."
    return os.path.join(CACHE_DIR, cache_name(path))


def fetch_from_server(request):
    # Fungsi untuk meneruskan permintaan klien ke server utama karena data belum ada di cache
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Menetapkan batas waktu maksimal 5 detik menunggu balasan dari server utama
    server_socket.settimeout(5)

    # Melakukan koneksi ke server utama
    server_socket.connect((SERVER_HOST, SERVER_PORT))

    # Mengirimkan permintaan HTTP (request) dari klien secara utuh ke server
    server_socket.sendall(request)

    # Variabel kosong bertipe bytes untuk menampung balasan (response) dari server
    response = b""

    # Terus menerima data dari server sedikit demi sedikit sampai habis
    while True:
        data = server_socket.recv(BUFFER_SIZE)

        # Jika tidak ada data lagi yang diterima, hentikan perulangan
        if not data:
            break

        # Gabungkan potongan data yang diterima ke variabel response
        response += data

    # Tutup koneksi ke server utama dan kembalikan datanya
    server_socket.close()
    return response


def handle_client(client_socket, addr):
    # Fungsi utama yang dieksekusi untuk setiap klien yang terhubung
    
    # Mencatat waktu mulai untuk menghitung kecepatan respons (QoS)
    start = time.time()

    try:
        # Menerima permintaan dari klien
        request = client_socket.recv(BUFFER_SIZE)

        # Mengambil baris pertama dari permintaan HTTP (misal: "GET /index.html HTTP/1.1")
        request_line = request.decode().splitlines()[0]

        # Memecah baris pertama menjadi 3 bagian: metode (GET), path (/index.html), dan versi HTTP
        method, path, version = request_line.split()

        # Mendapatkan lokasi file cache berdasarkan path yang diminta
        cache_file = get_cache_path(path)

        # KONDISI 1: CACHE HIT (File sudah ada di proxy)
        if os.path.exists(cache_file):

            # Kunci proses ini, baca isi file cache, lalu simpan ke variabel response
            with lock:
                with open(cache_file, "rb") as f:
                    response = f.read()

            # Kirimkan data dari cache langsung ke klien tanpa harus ke server utama
            client_socket.sendall(response)

            # Hitung waktu pemrosesan dalam milidetik dan cetak log HIT
            elapsed = (time.time() - start) * 1000
            log(f"{path} | HIT | {elapsed:.2f} ms")

        # KONDISI 2: CACHE MISS (File belum ada di proxy)
        else:
            # Ambil data dari server utama memanggil fungsi fetch_from_server
            response = fetch_from_server(request)

            # Kunci proses ini, lalu buat file cache baru untuk disimpan
            with lock:
                with open(cache_file, "wb") as f:
                    f.write(response)

            # Kirimkan data yang baru saja didapat dari server utama ke klien
            client_socket.sendall(response)

            # Hitung waktu pemrosesan dan cetak log MISS
            elapsed = (time.time() - start) * 1000
            log(f"{path} | MISS | {elapsed:.2f} ms")

    # Penanganan Error: Jika server utama terlalu lama merespons (lebih dari 5 detik)
    except socket.timeout:
        
        # Baca halaman error 504 yang tersimpan secara lokal
        with open("status/504.html", "rb") as f:
            body = f.read()

        # Rakit header HTTP 504 Gateway Timeout beserta isi halamannya
        response = (
            "HTTP/1.1 504 Gateway Timeout\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
        ).encode() + body

        # Kirimkan halaman error ke klien
        client_socket.sendall(response)

    # Penanganan Error: Jika terjadi kendala sistem atau jaringan lainnya
    except Exception as e:
        
        print(e) # Cetak detail error ke terminal proxy

        # Baca halaman error 502 yang tersimpan secara lokal
        with open("status/502.html", "rb") as f:
            body = f.read()

        # Rakit header HTTP 502 Bad Gateway beserta isi halamannya
        response = (
            "HTTP/1.1 502 Bad Gateway\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
        ).encode() + body

        # Kirimkan halaman error ke klien
        client_socket.sendall(response)

    # Blok ini akan selalu dijalankan pada akhirnya: Memutuskan/menutup koneksi dengan klien
    finally:
        client_socket.close()


def start_proxy():
    # Fungsi untuk menyalakan server proxy
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Mengikat proxy ke IP dan Port yang sudah diatur di atas
    proxy_socket.bind((PROXY_HOST, PROXY_PORT))

    # Memulai mendengarkan permintaan masuk (maksimal 20 antrean klien)
    proxy_socket.listen(20)

    log(f"Proxy running on port {PROXY_PORT}")

    # Server loop: Berjalan terus-menerus tanpa henti
    while True:
        # Menerima koneksi baru dari klien
        client_socket, addr = proxy_socket.accept()

        # Melemparkan klien yang baru masuk ke thread baru agar tidak mengganggu antrean klien lain
        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, addr)
        )

        # Menjalankan thread tersebut
        thread.start()

# Memastikan skrip ini hanya dieksekusi jika dijalankan secara langsung (bukan di-import dari file lain)
if __name__ == "__main__":
    start_proxy()