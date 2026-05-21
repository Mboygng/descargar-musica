import subprocess
import os
import shutil
import zipfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'status': 'error', 'message': 'Falta el enlace.'}), 400

    temp_dir = os.path.join(os.getcwd(), "temp_download")
    os.makedirs(temp_dir, exist_ok=True)

    # yt-dlp ya viene instalado nativo en los servidores de Linux en Render
    output_template = os.path.join(temp_dir, "%(playlist_index)02d - %(title)s.%(ext)s")

    comando = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "128k",
        "-o", output_template,
        url
    ]

    try:
        subprocess.run(comando, capture_output=True, text=True, check=True)

        # Crear el ZIP en el servidor para enviárselo al iPhone
        zip_filename = "MBG_PACK.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.join("Playlist", file))

        shutil.rmtree(temp_dir)

        # Le mandamos el archivo ZIP físico directo al navegador del iPhone
        return send_file(zip_filename, as_attachment=True)

    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Lee el puerto que le asigna Render automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)