import os
import random
import socket
from flask import Flask, jsonify, render_template_string, send_from_directory
import qrcode

app = Flask(__name__)

# Las 16 plantillas balanceadas de 3x3
PLANTILLAS = [
    [1, 2, 3, 9, 12, 13, 17, 19, 21],
    [4, 5, 11, 12, 16, 17, 22, 27, 28],
    [3, 11, 14, 16, 17, 19, 21, 24, 25],
    [1, 4, 9, 10, 14, 18, 21, 25, 29],
    [5, 10, 13, 14, 15, 16, 20, 24, 30],
    [2, 4, 7, 10, 11, 22, 26, 28, 30],
    [8, 9, 12, 18, 22, 23, 26, 28, 30],
    [1, 3, 4, 6, 11, 16, 23, 25, 28],
    [8, 9, 15, 18, 19, 20, 22, 25, 29],
    [2, 8, 12, 13, 15, 23, 24, 29, 30],
    [5, 6, 10, 16, 17, 19, 20, 27, 29],
    [7, 9, 14, 18, 20, 24, 25, 26, 28],
    [2, 5, 8, 10, 15, 19, 21, 22, 30],
    [4, 6, 7, 15, 21, 23, 24, 26, 27],
    [1, 2, 3, 6, 7, 8, 13, 23, 27],
    [3, 5, 7, 11, 13, 14, 18, 20, 29]
]

# Estado en memoria del servidor
plantillas_libres = list(range(len(PLANTILLAS)))
baraja_organizador = list(range(1, 31))
random.shuffle(baraja_organizador)

# -------------------------------------------------------------
# RUTAS DE SERVICIO DE IMÁGENES
# -------------------------------------------------------------
@app.route('/img/<int:num>')
def servir_imagen(num):
    extensiones = ['.png', '.jpg', '.jpeg', '.webp']
    for ext in extensiones:
        nombre = f"lot{num}{ext}"
        if os.path.exists(nombre):
            return send_from_directory('.', nombre)
        if os.path.exists(os.path.join('imagenes', nombre)):
            return send_from_directory('imagenes', nombre)
    
    # SVG provisional si no se ha subido la imagen aún
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="260" viewBox="0 0 200 260">
        <rect width="200" height="260" fill="#f0ede6" stroke="#bda" stroke-width="6" rx="12"/>
        <text x="100" y="110" font-size="42" font-family="Arial" font-weight="bold" fill="#2d6a4f" text-anchor="middle">#{num}</text>
        <text x="100" y="160" font-size="22" font-family="Arial" fill="#555" text-anchor="middle">lot{num}</text>
    </svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml'}

# -------------------------------------------------------------
# VISTA: JUGADOR (MÓVIL / RESPONSIVA)
# -------------------------------------------------------------
HTML_JUGADOR = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Lotería Mexicana - Jugador</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #fdfbf7; margin: 0; padding: 10px; text-align: center; color: #222; }
        h1 { font-size: 1.3rem; margin: 8px 0; color: #1b4332; }
        .instruccion { font-size: 0.85rem; color: #666; margin-bottom: 10px; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; max-width: 380px; margin: 0 auto; }
        .casilla { position: relative; aspect-ratio: 3/4; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.15); border: 2px solid #ccc; cursor: pointer; }
        .casilla img { width: 100%; height: 100%; object-fit: cover; display: block; }
        .casilla.marcada::after {
            content: "✔";
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.65);
            display: flex; align-items: center; justify-content: center;
            color: #fff; font-size: 2.2rem; font-weight: bold;
        }
        #banner-victoria { display: none; margin-top: 15px; padding: 15px; background: #d00000; color: #fff; font-size: 1.4rem; font-weight: bold; border-radius: 10px; animation: pop 0.4s ease; }
        @keyframes pop { 0% { transform: scale(0.8); } 100% { transform: scale(1); } }
    </style>
</head>
<body>
    <h1>Plantilla #{{ id_plantilla + 1 }}</h1>
    <div class="instruccion">Toca las casillas que vayan saliendo para marcarlas.</div>
    
    <div class="grid" id="grid">
        {% for carta in cartas %}
        <div class="casilla" onclick="toggleCasilla(this)">
            <img src="/img/{{ carta }}" alt="Carta {{ carta }}">
        </div>
        {% endfor %}
    </div>

    <div id="banner-victoria">🎉 ¡¡LOTERÍA!! 🎉<br><span style="font-size: 0.9rem; font-weight: normal;">¡Has completado toda tu plantilla!</span></div>

    <script>
        function toggleCasilla(el) {
            el.classList.toggle('marcada');
            const total = document.querySelectorAll('.casilla').length;
            const marcadas = document.querySelectorAll('.casilla.marcada').length;
            document.getElementById('banner-victoria').style.display = (marcadas === total) ? 'block' : 'none';
        }
    </script>
</body>
</html>
'''

@app.route('/')
@app.route('/jugador')
def vista_jugador():
    global plantillas_libres
    if not plantillas_libres:
        return "<h2>¡Todas las 16 plantillas ya han sido asignadas!</h2><p>Pide al organizador que reinicie la partida.</p>", 403

    idx = random.choice(plantillas_libres)
    plantillas_libres.remove(idx)
    return render_template_string(HTML_JUGADOR, id_plantilla=idx, cartas=PLANTILLAS[idx])

# -------------------------------------------------------------
# VISTA: ORGANIZADOR (PANTALLA / PROYECTOR)
# -------------------------------------------------------------
HTML_ORGANIZADOR = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mesa del Organizador</title>
    <style>
        body { font-family: sans-serif; background: #2b2d42; color: #edf2f4; text-align: center; margin: 0; padding: 20px; }
        h1 { color: #ef233c; margin-bottom: 5px; }
        .contador { font-size: 1.2rem; color: #8d99ae; margin-bottom: 15px; }
        .carta-container { width: 320px; height: 440px; margin: 0 auto; border: 4px solid #fff; border-radius: 16px; overflow: hidden; background: #fff; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .carta-container img { width: 100%; height: 100%; object-fit: contain; }
        .controles { margin-top: 25px; }
        button { font-size: 1.1rem; padding: 12px 24px; margin: 0 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .btn-sig { background: #06d6a0; color: #073b4c; }
        .btn-ant { background: #8d99ae; color: #2b2d42; }
        .btn-reset { background: #e63946; color: white; margin-top: 30px; }
    </style>
</head>
<body>
    <h1>Mesa del Organizador (Cantor)</h1>
    <div class="contador" id="contador">Carta 1 de {{ total }}</div>

    <div class="carta-container">
        <img id="carta-img" src="/img/{{ baraja[0] }}">
    </div>

    <div class="controles">
        <button class="btn-ant" onclick="cambiar(-1)">◀ Anterior</button>
        <button class="btn-sig" onclick="cambiar(1)">Siguiente ▶</button>
    </div>

    <div>
        <button class="btn-reset" onclick="reiniciarPartida()">Reiniciar Plantillas para Nueva Partida</button>
    </div>

    <script>
        const baraja = {{ baraja|tojson }};
        let index = 0;

        function cambiar(delta) {
            index = Math.max(0, Math.min(baraja.length - 1, index + delta));
            document.getElementById('carta-img').src = '/img/' + baraja[index];
            document.getElementById('contador').innerText = `Carta ${index + 1} de ${baraja.length}`;
        }

        window.addEventListener('keydown', (e) => {
            if (e.key === ' ' || e.key === 'ArrowRight') cambiar(1);
            if (e.key === 'ArrowLeft') cambiar(-1);
        });

        function reiniciarPartida() {
            if(confirm("¿Liberar las 16 plantillas y barajar de nuevo?")) {
                fetch('/api/reset').then(() => location.reload());
            }
        }
    </script>
</body>
</html>
'''

@app.route('/organizador')
def vista_organizador():
    return render_template_string(HTML_ORGANIZADOR, baraja=baraja_organizador, total=len(baraja_organizador))

@app.route('/api/reset')
def api_reset():
    global plantillas_libres, baraja_organizador
    plantillas_libres = list(range(len(PLANTILLAS)))
    random.shuffle(baraja_organizador)
    return jsonify({"status": "ok", "disponibles": len(plantillas_libres)})

# -------------------------------------------------------------
# EJECUCIÓN Y GENERACIÓN DE QR
# -------------------------------------------------------------
def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    ip = obtener_ip_local()
    puerto = 5000
    url_juego = f"http://{ip}:{puerto}"

    print("\n" + "=" * 50)
    print(f"🎮 URL PARA LOS JUGADORES: {url_juego}")
    print(f"📢 URL DEL ORGANIZADOR:   {url_juego}/organizador")
    print("=" * 50 + "\n")
    print("CÓDIGO QR PARA ESCANEAR CON EL CELULAR:")

    # Imprime el código QR directamente en la consola de la terminal
    qr = qrcode.QRCode()
    qr.add_data(url_juego)
    qr.print_ascii(invert=True)

    app.run(host='0.0.0.0', port=puerto, debug=False)


