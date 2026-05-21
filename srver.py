import subprocess
import os
import shutil
import zipfile
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

    # 1. Crear una carpeta temporal única para procesar la descarga sin mezclar archivos
    temp_dir = os.path.join(os.getcwd(), "temp_download")
    os.makedirs(temp_dir, exist_ok=True)

    # Estructura del nombre: "01 - Nombre.mp3". Si es video suelto, arranca en 01 por defecto.
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
        # Ejecutar la descarga apuntando a la carpeta temporal
        print("> Descargando contenido de forma numerada...")
        subprocess.run(comando, capture_output=True, text=True, check=True)
        
        # 2. Obtener el nombre real de la Playlist o usar un nombre por defecto si es video suelto
        # Usamos yt-dlp rápido para extraer solo el título del contenedor principal
        cmd_title = [executable, "--get-filename", "-o", "%(playlist)s", url]
        res_title = subprocess.run(cmd_title, capture_output=True, text=True)
        playlist_name = res_title.stdout.strip()
        
        if not playlist_name or playlist_name == "NA" or playlist_name == "None":
            playlist_name = "MBG_SINGLE_TRACKS"
            
        # Limpiar caracteres raros del nombre de la carpeta para evitar errores de Windows
        for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>']:
            playlist_name = playlist_name.replace(char, "_")

        # 3. Empaquetar todo en un archivo ZIP estructurado
        zip_filename = f"{playlist_name}.zip"
        print(f"> Creando archivo comprimido: {zip_filename}")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    # Arreglo de seguridad por si algún video suelto no traía número en el index
                    file_src = file
                    if file.startswith("NA - "):
                        file_src = file.replace("NA - ", "01 - ")
                    
                    file_path = os.path.join(root, file)
                    # Al meterlo al zip con este arco, el ZIP crea la carpeta con el nombre de la playlist adentro
                    arcname = os.path.join(playlist_name, file_src)
                    zipf.write(file_path, arcname)
                    
        # 4. Limpieza: Borramos la carpeta temporal de archivos sueltos para dejar espacio limpio
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'status': 'success', 
            'message': f'¡Completado! Pack empaquetado en: "{zip_filename}" listo para tu iPhone.'
        })
        
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'status': 'error', 'message': f'Fallo en yt-dlp: {e.stderr}'}), 500
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("=========================================================")
    print("   MBG STVDIO ZIP-PACKER RUNNING ON http://localhost:5000")
    print("=========================================================")
    app.run(port=5000)