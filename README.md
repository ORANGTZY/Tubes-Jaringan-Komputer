# Tugas Besar Jaringan Komputer — IFLAB Universitas Telkom
## Implementasi Client–Proxy–Server Berbasis Socket Python
### Kelompok 3 Orang

---

## STRUKTUR FOLDER (WAJIB PERSIS SEPERTI INI)

```
project_folder/          ← satu folder ini dikerjakan bersama
│
├── webserver.py         ← Laptop A jalankan ini
├── proxy.py             ← Laptop B jalankan ini
├── client.py            ← Laptop C jalankan ini
│
├── index.html           ← dari dosen
├── osi.html             ← dari dosen
├── tcpip.html           ← dari dosen
├── qos.html             ← dari dosen
├── implementation.html  ← dari dosen
│
├── css/
│   └── style.css        ← dari dosen (WAJIB ada subfolder css/)
│
├── assets/              ← buat folder ini, isi dengan gambar
│   ├── iflab.png
│   ├── network.png
│   ├── osi.png
│   └── tcpip.png
│
├── status/              ← buat folder ini
│   ├── 404.html         ← dari dosen
│   ├── 500.html         ← dari dosen
│   ├── 502.html         ← dari dosen
│   └── 504.html         ← dari dosen
│
└── proxy_cache/         ← dibuat OTOMATIS oleh proxy.py (tidak perlu buat manual)
```

---

## LANGKAH 1 — SUSUN FOLDER

### Di Laptop A (Web Server):
```
Buat folder: iflab_server/
Salin ke dalamnya:
  - webserver.py
  - index.html, osi.html, tcpip.html, qos.html, implementation.html
  - Buat subfolder css/  → taruh style.css di sini
  - Buat subfolder assets/ → taruh semua gambar di sini
  - Buat subfolder status/ → taruh 404.html, 500.html, 502.html, 504.html
```

### Di Laptop B (Proxy):
```
Buat folder: iflab_proxy/
Salin ke dalamnya:
  - proxy.py  (cukup satu file ini saja)
```

### Di Laptop C (Client):
```
Buat folder: iflab_client/
Salin ke dalamnya:
  - client.py  (cukup satu file ini saja)
```

---

## LANGKAH 2 — CARI IP MASING-MASING LAPTOP

Jalankan perintah berikut di setiap laptop:

**Windows:**
```
ipconfig
```
Cari "IPv4 Address" pada adapter WiFi/LAN.

**Linux/macOS:**
```
ip addr   atau   ifconfig
```

Contoh hasil:
```
Laptop A (Web Server) : 192.168.1.10
Laptop B (Proxy)      : 192.168.1.11
Laptop C (Client)     : 192.168.1.12
```

---

## LANGKAH 3 — KONFIGURASI IP DI KODE

### Edit proxy.py (di Laptop B):
Buka proxy.py, cari baris ini dan ubah:
```python
SERVER_HOST = "127.0.0.1"   # ← GANTI dengan IP Laptop A
```
Contoh:
```python
SERVER_HOST = "192.168.1.10"
```

### Edit client.py (di Laptop C):
Buka client.py, cari baris ini dan ubah:
```python
PROXY_HOST  = "127.0.0.1"   # ← GANTI dengan IP Laptop B
SERVER_HOST = "127.0.0.1"   # ← GANTI dengan IP Laptop A (untuk UDP)
```
Contoh:
```python
PROXY_HOST  = "192.168.1.11"
SERVER_HOST = "192.168.1.10"
```

---

## LANGKAH 4 — NONAKTIFKAN FIREWALL (SEMENTARA)

### Windows:
```
Buka Control Panel → Windows Defender Firewall
→ Turn off Windows Defender Firewall (sementara saat pengujian)
```
Atau via Command Prompt (Admin):
```cmd
netsh advfirewall set allprofiles state off
```
Aktifkan kembali setelah selesai:
```cmd
netsh advfirewall set allprofiles state on
```

### Linux:
```bash
sudo ufw disable
```

### macOS:
```
System Preferences → Security & Privacy → Firewall → Turn Off
```

---

## LANGKAH 5 — UJI KONEKTIVITAS ANTAR LAPTOP

Dari Laptop C, ping Laptop A dan B:
```bash
ping 192.168.1.10   # ping ke Web Server
ping 192.168.1.11   # ping ke Proxy
```
Pastikan ada reply sebelum lanjut.

---

## LANGKAH 6 — JALANKAN SISTEM (URUTAN WAJIB!)

### ① Laptop A — Jalankan Web Server PERTAMA:
```bash
cd iflab_server
python webserver.py
```
Output yang muncul:
```
[2026-...] [MAIN] ══════════════════════════════════════════
[2026-...] [MAIN]   IFLAB Web Server - Jaringan Komputer
[2026-...] [INIT] [OK] index.html
[2026-...] [INIT] [OK] osi.html
[2026-...] [INIT] [OK] css/style.css
[2026-...] [INIT] [OK] status/404.html
[2026-...] [TCP]  HTTP Server running on 0.0.0.0:8000
[2026-...] [UDP]  UDP Echo Server running on 0.0.0.0:9000
```

### ② Laptop B — Jalankan Proxy SETELAH Server:
```bash
cd iflab_proxy
python proxy.py
```
Output yang muncul:
```
[2026-...] [PROXY] ══════════════════════════════════════════
[2026-...] [PROXY]   IFLAB Proxy Server
[2026-...] [PROXY] Listening on     : 0.0.0.0:8080
[2026-...] [PROXY] Forward ke       : 192.168.1.10:8000
[2026-...] [PROXY] Cache directory  : .../proxy_cache
```

### ③ Laptop C — Jalankan Client TERAKHIR:
```bash
cd iflab_client

# HTTP GET index.html (pertama kali = MISS)
python client.py --mode tcp --url /index.html

# HTTP GET osi.html
python client.py --mode tcp --url /osi.html

# UDP QoS ping 10 paket
python client.py --mode udp --count 10

# Keduanya sekaligus
python client.py --mode both

# Semua halaman (MISS lalu HIT - untuk dokumentasi)
python client.py --mode all

# 5 client concurrent
python client.py --mode multi --clients 5
```

---

## LANGKAH 7 — CARA MENGUJI DARI BROWSER (OPSIONAL)

Buka browser di Laptop C, ketik di address bar:
```
http://192.168.1.11:8080/index.html
http://192.168.1.11:8080/osi.html
http://192.168.1.11:8080/qos.html
```
Halaman IFLAB seharusnya tampil lengkap dengan CSS.

---

## LANGKAH 8 — WIRESHARK

Jalankan Wireshark di Laptop B (Proxy) untuk capture semua traffic:

1. Buka Wireshark
2. Pilih interface: WiFi atau Ethernet yang digunakan
3. Masukkan filter:
```
tcp.port==8000 || tcp.port==8080 || udp.port==9000
```
4. Klik Start Capture
5. Jalankan client dari Laptop C
6. Amati:
   - TCP 3-way handshake (SYN, SYN-ACK, ACK)
   - HTTP request dan response
   - Paket UDP ping/echo
   - Tidak ada traffic langsung antara IP Laptop C dan port 8000

---

## SKENARIO PENGUJIAN LENGKAP

### Skenario 1: Cache MISS → HIT
```bash
# Laptop C:
python client.py --mode tcp --url /qos.html    # MISS (lambat ~50-200ms)
python client.py --mode tcp --url /qos.html    # HIT  (cepat ~1-5ms)
```
Perhatikan log di Laptop B:
```
[PROXY] MISS | [/qos.html] - forwarding ke server...
[PROXY] HIT  | [/qos.html] time=1.23ms
```

### Skenario 2: File tidak ditemukan (404)
```bash
python client.py --mode tcp --url /halaman-tidak-ada.html
```
Web server menampilkan halaman `status/404.html` yang sudah didesain.

### Skenario 3: QoS UDP
```bash
python client.py --mode udp --count 10
```

### Skenario 4: Multi-client (5 concurrent)
```bash
python client.py --mode multi --clients 5
```

### Skenario 5: Server dimatikan (502/504)
```bash
# Matikan webserver.py di Laptop A (Ctrl+C)
# Lalu dari Laptop C:
python client.py --mode tcp --url /index.html
# Proxy akan reply: 502 Bad Gateway
```

---

## TROUBLESHOOTING

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| `Connection refused` di proxy | Web Server belum jalan | Jalankan webserver.py dulu |
| `Connection refused` di client | Proxy belum jalan | Jalankan proxy.py dulu |
| CSS tidak muncul di browser | Folder `css/` tidak ada | Buat folder `css/` taruh style.css |
| 404 semua halaman | File HTML tidak di WEB_ROOT | Pastikan HTML di folder yang sama dengan webserver.py |
| UDP timeout | Firewall blokir UDP | Nonaktifkan firewall sementara |
| IP salah | Konfigurasi belum diubah | Edit SERVER_HOST di proxy.py dan PROXY_HOST di client.py |
| Error page tidak muncul (blank) | Folder `status/` tidak ada | Buat folder `status/`, taruh 404/500/502/504.html |
| Gambar tidak muncul | Folder `assets/` tidak ada | Buat folder `assets/`, taruh file gambar |

---

## RINGKASAN PORT

| Komponen | Port TCP | Port UDP | Keterangan |
|----------|----------|----------|------------|
| Web Server (Laptop A) | 8000 | 9000 | HTTP + Echo |
| Proxy Server (Laptop B) | 8080 | — | Forward + Cache |
| Client (Laptop C) | ephemeral | ephemeral | HTTP + Pinger |

---

## ALUR KOMUNIKASI (TOPOLOGI 3 ORANG)

```
Laptop C                Laptop B                Laptop A
(Client)                (Proxy)                 (Web Server)
192.168.1.12            192.168.1.11            192.168.1.10

    │──── TCP:8080 GET /index.html ──►│
    │                                 │──── TCP:8000 GET /index.html ──►│
    │                                 │◄─── HTTP 200 OK + HTML ─────────│
    │                                 │  [simpan ke proxy_cache/]
    │◄─── HTTP 200 OK + HTML ─────────│
    │
    │──── UDP ke :9000 "Ping 1 ..." ──────────────────────────────────►│
    │◄─── UDP Echo "Ping 1 ..." ──────────────────────────────────────│
```

