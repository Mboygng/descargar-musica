import subprocess
import os
from flask import Flask, request, jsonify
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
    
    try:
        print("> Obteniendo el nombre de la playlist (Filtro único activo)...")
        # Agregamos "--playlist-items 1" para que traiga el nombre UNA sola vez
        cmd_title = [executable, "--playlist-items", "1", "--get-filename", "-o", "%(playlist)s", url]
        res_title = subprocess.run(cmd_title, capture_output=True, text=True)
        playlist_name = res_title.stdout.strip()
        
        # Limpieza de saltos de línea
        playlist_name = playlist_name.replace('\n', '_').replace('\r', '_')
        
        if not playlist_name or playlist_name in ["NA", "None", ""]:
            playlist_name = "MBG_PACK"
            
        # Limpiamos caracteres prohibidos de Windows
        for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '\n', '\r']:
            playlist_name = playlist_name.replace(char, "_")
            
        # Nos quedamos con el nombre limpio final
        playlist_name = " ".join(playlist_name.split())

        # Si por alguna razón quedó un guión bajo colgado al final, lo volamos
        if playlist_name.endswith('_'):
            playlist_name = playlist_name.rstrip('_')

        # Creamos la carpeta con el nombre único real
        target_dir = os.path.join(base_dir, playlist_name)
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"> Descargando pistas directo en la carpeta: {playlist_name}")
        
        output_template = os.path.join(target_dir, "%(playlist_index)02d - %(title)s.%(ext)s")
        
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
        
        # Descarga normal de toda la playlist
        subprocess.run(comando, check=True)
        
        print(f"✓ ¡Completado! Carpeta lista en: {target_dir}")
        return jsonify({'status': 'success', 'message': f'Carpeta "{playlist_name}" creada con éxito.'})
        
    except Exception as e:
        print(f"! Error interno: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("=========================================================")
    print("   MBG STVDIO PC-SERVER RUNNING ON http://localhost:5000")
    print("=========================================================")
    app.run(port=5000)