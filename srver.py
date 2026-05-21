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
        return jsonify({'status': 'error', 'message': 'No se proporcionó un enlace.'}), 400
    
    executable = "./yt-dlp.exe"
    if not os.path.exists(executable):
        return jsonify({'status': 'error', 'message': 'Falta el archivo yt-dlp.exe al lado de este script.'}), 500

    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_dir, "temp_download")
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    os.makedirs(temp_dir, exist_ok=True)

    output_template = os.path.join(temp_dir, "%(playlist_index)02d - %(title)s.%(ext)s")
    
    comando = [
        executable,
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "96k",
        "--embed-thumbnail",
        "--ppa", "ffmpeg:-ac 1 -ar 22050",
        "-o", output_template,
        "--no-warnings",
        url
    ]
    
    try:
        print("> Descargando contenido en carpeta temporal fija...")
        subprocess.run(comando, capture_output=True, text=True, check=True)
        
        # Obtener el nombre de la playlist original
        cmd_title = [executable, "--get-filename", "-o", "%(playlist)s", url]
        res_title = subprocess.run(cmd_title, capture_output=True, text=True)
        playlist_name = res_title.stdout.strip()
        
        # --- LIMPIEZA BLINDADA DE NOMBRE ---
        # 1. Eliminamos saltos de línea (\n y \r) que rompen Windows
        playlist_name = playlist_name.replace('\n', '_').replace('\r', '_')
        
        # 2. Si quedó vacío o por defecto, le clavamos un nombre genérico limpio
        if not playlist_name or playlist_name in ["NA", "None", ""]:
            playlist_name = "MBG_PACK"
            
        # 3. Limpiamos caracteres prohibidos de carpetas en Windows
        for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '\n', '\r']:
            playlist_name = playlist_name.replace(char, "_")
            
        # Nos aseguramos de que no queden espacios dobles raros
        playlist_name = " ".join(playlist_name.split())
        # -----------------------------------

        zip_filepath = os.path.join(base_dir, f"{playlist_name}.zip")
        print(f"> Creando archivo comprimido definitivo en: {zip_filepath}")
        
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_src = file.replace("NA - ", "01 - ") if file.startswith("NA - ") else file
                    zipf.write(os.path.join(root, file), os.path.join(playlist_name, file_src))
                    
        shutil.rmtree(temp_dir)
        
        return send_file(zip_filepath, as_attachment=True)
        
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        print(f"! Error interno: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("=========================================================")
    print("   MBG STVDIO PC-SERVER RUNNING ON http://localhost:5000")
    print("=========================================================")
    app.run(port=5000)