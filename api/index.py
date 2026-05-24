from flask import Flask, request, jsonify
from flask_cors import CORS
import cloudscraper
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)
# Izinkan akses dari domain manapun (CORS)
CORS(app)

# Bypass proteksi standar
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
BASE_URL = "https://g.shinigami.asia"

# ==========================================
# HALAMAN UTAMA (UI HTML)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Scraper Komik Shinigami</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f9; color: #333; }
        .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #5a67d8; border-bottom: 2px solid #ebf4ff; padding-bottom: 10px; }
        .endpoint { background: #edf2f7; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #4c51bf; }
        .endpoint h3 { margin-top: 0; color: #2d3748; }
        code { background: #2d3748; color: #e2e8f0; padding: 3px 6px; border-radius: 4px; font-size: 0.9em; }
        .method { display: inline-block; background: #48bb78; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; margin-right: 10px; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Shinigami Unofficial API</h1>
        <p>Gunakan endpoint di bawah ini untuk mengambil data JSON.</p>
        
        <div class="endpoint">
            <h3><span class="method">GET</span>Cari Komik</h3>
            <p>Mencari komik berdasarkan judul.</p>
            <p><strong>URL:</strong> <code>/api/search?q=judul_komik</code></p>
            <p><strong>Contoh:</strong> <a href="/api/search?q=Kang Lim">/api/search?q=Kang Lim</a></p>
        </div>

        <div class="endpoint">
            <h3><span class="method">GET</span>Ambil Daftar Chapter</h3>
            <p>Mengambil semua link chapter dari sebuah URL komik.</p>
            <p><strong>URL:</strong> <code>/api/chapters?url=link_komik</code></p>
            <p><strong>Contoh:</strong> <a href="/api/chapters?url=https://g.shinigami.asia/series/f7746c21-5bf2-4e71-a9e2-bbb7891a9bdb">/api/chapters?url=...</a></p>
        </div>

        <div class="endpoint">
            <h3><span class="method">GET</span>Ambil Gambar Chapter</h3>
            <p>Mendapatkan daftar link gambar mentahan untuk dibaca.</p>
            <p><strong>URL:</strong> <code>/api/images?url=link_chapter</code></p>
            <p><strong>Contoh:</strong> <a href="/api/images?url=https://g.shinigami.asia/chapter/87732de4-8099-4cb2-97c3-7afa8040b06b">/api/images?url=...</a></p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return HTML_PAGE

# ==========================================
# ENDPOINT API
# ==========================================

@app.route('/api/search', methods=['GET'])
def search_comic():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Parameter 'q' (query pencarian) dibutuhkan"}), 400

    url = f"{BASE_URL}/search?q={urllib.parse.quote(query)}"
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # CATATAN: Class ini mungkin perlu diubah jika struktur web aslinya ganti
        results = soup.find_all('a', href=True)
        comics = []
        seen = set()
        
        for a in results:
            if '/series/' in a['href']:
                title = a.text.strip()
                if not title: continue # Abaikan kalau kosong
                
                link = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
                
                if link not in seen:
                    comics.append({"title": title, "link": link})
                    seen.add(link)
                    
        return jsonify({"status": "sukses", "data": comics})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Parameter 'url' komik dibutuhkan"}), 400

    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        chapters = []
        seen = set()
        
        for a in links:
            if '/chapter/' in a['href']:
                chapter_name = a.text.strip()
                # Coba cari elemen text di dalamnya jika kosong
                if not chapter_name: 
                    chapter_name = "Chapter"
                
                link = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
                
                if link not in seen:
                    chapters.append({"name": chapter_name, "link": link})
                    seen.add(link)
                    
        return jsonify({"status": "sukses", "data": chapters})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/images', methods=['GET'])
def get_images():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Parameter 'url' chapter dibutuhkan"}), 400

    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        images = soup.find_all('img') 
        image_urls = []
        
        for img in images:
            # Cari atribut src atau data-src
            img_url = img.get('src') or img.get('data-src') 
            
            if img_url:
                img_url = img_url.strip()
                # Pastikan ini link valid dan bukan logo web
                if img_url.startswith('http') and ('logo' not in img_url.lower()) and ('icon' not in img_url.lower()):
                    image_urls.append(img_url)

        if not image_urls:
            return jsonify({
                "status": "gagal", 
                "pesan": "Tidak ada gambar. Pastikan URL benar atau proteksi Cloudflare sedang sangat ketat."
            }), 404

        return jsonify({
            "status": "sukses",
            "total_halaman": len(image_urls),
            "data": image_urls
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Wajib untuk Vercel
if __name__ == '__main__':
    app.run(debug=True)
