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

    # Usamos os.path.abspath para que Windows sepa la ruta exacta real en el disco
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_dir, "temp_download")
    
    # Limpieza previa por si quedó algo trabado antes
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
        
        if not playlist_name or playlist_name == "NA" or playlist_name == "None":
            playlist_name = "MBG_PACK"
            
        for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>']:
            playlist_name = playlist_name.replace(char, "_")

        # Ruta absoluta donde se va a crear el archivo .zip físico en tu PC antes de mandarlo
        zip_filepath = os.path.join(base_dir, f"{playlist_name}.zip")
        print(f"> Creando archivo comprimido definitivo en: {zip_filepath}")
        
        # Armamos el ZIP leyendo los archivos descargados
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_src = file.replace("NA - ", "01 - ") if file.startswith("NA - ") else file
                    # Guardamos el archivo físico adentro de la estructura del ZIP
                    zipf.write(os.path.join(root, file), os.path.join(playlist_name, file_src))
                    
        # Ahora que el ZIP ya está cerrado y creado, borramos los temas sueltos de la carpeta temporal
        shutil.rmtree(temp_dir)
        
        # Mandamos el archivo ZIP real directo a la barra de descargas de tu navegador
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