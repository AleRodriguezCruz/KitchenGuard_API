from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection
from routes.sensors import sensors_bp
from routes.timers import timers_bp
from routes.panic import panic_bp
import firebase_admin
from firebase_admin import credentials, messaging
import os

cred = credentials.Certificate(os.getenv("FIREBASE_KEY_PATH", "firebase-key.json"))
firebase_admin.initialize_app(cred)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(sensors_bp)
app.register_blueprint(timers_bp)
app.register_blueprint(panic_bp)

FCM_TOKENS = []

@app.route("/register-token", methods=["POST"])
def register_token():
    data = request.get_json()
    token = data.get("token")
    if token and token not in FCM_TOKENS:
        FCM_TOKENS.append(token)
    return jsonify({"message": "Token registrado"}), 200

def send_push(title, body):
    for token in FCM_TOKENS:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=token,
            )
            messaging.send(message)
        except Exception as e:
            print(f"Error enviando notificacion: {e}")

@app.route("/status", methods=["GET"])
def status():
    conn = get_connection()
    gas_row = conn.execute(
        "SELECT value, alert FROM sensor_events WHERE type='gas' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    temp_row = conn.execute(
        "SELECT value FROM sensor_events WHERE type='temperature' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    panic_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM panic_events WHERE timestamp >= datetime('now', '-5 minutes')"
    ).fetchone()
    conn.close()

    stove_on = bool(gas_row and gas_row["alert"] == 1)
    panic = bool(panic_row and panic_row["cnt"] > 0)

    if stove_on:
        send_push("Alerta de Gas", "Se detecto fuga de gas en la cocina")
    if panic:
        send_push("Boton de Panico", "Se activo el boton de panico en el hogar")

    return jsonify({
        "stove_on":    stove_on,
        "gas_level":   round(gas_row["value"], 1) if gas_row else 0,
        "temperature": round(temp_row["value"], 1) if temp_row else 22,
        "humidity":    55,
        "panic":       panic
    }), 200

@app.route("/", methods=["GET"])
def api_docs():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KitchenGuard API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0A0D14; color: #F8FAFC; min-height: 100vh; }
        .container { max-width: 950px; margin: 0 auto; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 32px; }
        .header h1 { font-size: 36px; font-weight: 800; }
        .accent { color: #F97316; }
        .header p { color: #94A3B8; font-size: 14px; margin-top: 8px; }
        .status-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); padding: 10px 20px; border-radius: 30px; margin: 16px 0; }
        .status-dot { width: 10px; height: 10px; background: #10B981; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
        
        .test-panel { background: #1A1F2E; border: 1px solid #262D3D; border-radius: 20px; padding: 24px; margin-bottom: 28px; }
        .test-panel h2 { font-size: 18px; margin-bottom: 12px; }
        .buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        button { padding: 10px 16px; border-radius: 10px; font-weight: 600; font-size: 12px; cursor: pointer; border: none; color: white; transition: all 0.2s; }
        button:hover { transform: translateY(-2px); opacity: 0.9; }
        .btn-gas { background: #F59E0B; }
        .btn-gas2 { background: #EA580C; }
        .btn-gas3 { background: #DC2626; }
        .btn-temp { background: #F97316; }
        .btn-temp2 { background: #EA580C; }
        .btn-panic { background: #EF4444; }
        .btn-reset { background: #10B981; }
        .btn-view { background: #6366F1; }
        
        #result {
            background: #0A0D14;
            border: 1px solid #262D3D;
            border-radius: 12px;
            padding: 16px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #10B981;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            display: none;
        }
        #result.show { display: block; }
        
        .section-title { font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 14px; }
        .endpoint { background: #1A1F2E; border: 1px solid #262D3D; border-radius: 14px; padding: 18px; margin-bottom: 10px; }
        .endpoint-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
        .method { padding: 4px 8px; border-radius: 5px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; min-width: 52px; text-align: center; }
        .get { background: rgba(16,185,129,0.2); color: #10B981; }
        .post { background: rgba(249,115,22,0.2); color: #F97316; }
        .path { font-family: 'Courier New', monospace; font-size: 13px; color: #F8FAFC; font-weight: 600; }
        .desc { font-size: 12px; color: #94A3B8; }
        
        .footer { text-align: center; margin-top: 36px; padding-top: 20px; border-top: 1px solid #262D3D; color: #475569; font-size: 11px; }
        .footer a { color: #F97316; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍎 KitchenGuard <span class="accent">API</span></h1>
            <p>Sistema inteligente de monitoreo de cocina</p>
            <div class="status-badge"><span class="status-dot"></span><span>API Operativa</span></div>
        </div>

        <div class="test-panel">
            <h2>🧪 Panel de Pruebas</h2>
            <div class="buttons">
                <button class="btn-gas" onclick="test('POST','/api/sensor',{type:'gas',value:25,alert:0})">💨 Gas 25%</button>
                <button class="btn-gas2" onclick="test('POST','/api/sensor',{type:'gas',value:55,alert:0})">💨 Gas 55%</button>
                <button class="btn-gas3" onclick="test('POST','/api/sensor',{type:'gas',value:85,alert:1})">🔥 Fuga Gas</button>
                <button class="btn-temp" onclick="test('POST','/api/sensor',{type:'temperature',value:35})">🌡️ 35°C</button>
                <button class="btn-temp2" onclick="test('POST','/api/sensor',{type:'temperature',value:65})">🌡️ 65°C</button>
                <button class="btn-panic" onclick="test('POST','/api/panic',{})">🆘 Pánico</button>
                <button class="btn-reset" onclick="test('POST','/api/sensor',{type:'gas',value:0,alert:0})">🔄 Reset</button>
                <button class="btn-view" onclick="test('GET','/status')">📊 Estado</button>
                <button class="btn-view" onclick="test('GET','/api/sensor')">📋 Historial</button>
            </div>
            <div id="result"></div>
        </div>

        <div class="section-title">📡 Endpoints</div>
        <div class="endpoint"><div class="endpoint-header"><span class="method get">GET</span><span class="path">/status</span></div><p class="desc">Estado actual de todos los sensores</p></div>
        <div class="endpoint"><div class="endpoint-header"><span class="method get">GET</span><span class="path">/api/sensor</span></div><p class="desc">Historial de sensores (últimos 50)</p></div>
        <div class="endpoint"><div class="endpoint-header"><span class="method post">POST</span><span class="path">/api/sensor</span></div><p class="desc">Enviar lectura (body: type, value, alert)</p></div>
        <div class="endpoint"><div class="endpoint-header"><span class="method get">GET</span><span class="path">/api/panic</span></div><p class="desc">Historial de pánico (últimos 20)</p></div>
        <div class="endpoint"><div class="endpoint-header"><span class="method post">POST</span><span class="path">/api/panic</span></div><p class="desc">Activar botón de pánico + push</p></div>
        <div class="endpoint"><div class="endpoint-header"><span class="method post">POST</span><span class="path">/register-token</span></div><p class="desc">Registrar token para notificaciones</p></div>

        <div class="footer">
            <p>KitchenGuard API v1.0 · <a href="https://kitchenguard-six.vercel.app">Web App</a> · <a href="https://github.com/AleRodriguezCruz/KitchenGuard_API">GitHub</a></p>
        </div>
    </div>

    <script>
        async function test(method, path, body) {
            var r = document.getElementById('result');
            r.textContent = '⏳ Cargando...';
            r.classList.add('show');
            
            try {
                var options = { method: method, headers: { 'Content-Type': 'application/json' } };
                if (body && Object.keys(body).length > 0) options.body = JSON.stringify(body);
                
                var res = await fetch(path, options);
                var data = await res.json();
                r.textContent = JSON.stringify(data, null, 2);
                r.style.color = '#10B981';
            } catch (e) {
                r.textContent = '❌ Error: ' + e.message;
                r.style.color = '#EF4444';
            }
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    init_db()
    print("KitchenGuard backend iniciando...")
    app.run(host="0.0.0.0", port=5000, debug=True)