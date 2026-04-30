[README.md](url)
# 🍎 KitchenGuard API

![Version](https://img.shields.io/badge/version-1.0-orange) ![Python](https://img.shields.io/badge/python-3.x-blue) ![Flask](https://img.shields.io/badge/flask-3.0-red) ![Firebase](https://img.shields.io/badge/firebase-admin-6.2-yellow) ![Render](https://img.shields.io/badge/deploy-Render-purple)

API REST para el sistema inteligente de monitoreo de cocina **KitchenGuard**. Detecta fugas de gas, monitorea temperatura, identifica estufas abandonadas y activa alertas de pánico con notificaciones push en tiempo real.

---

## 🚀 URL Base

```
https://kitchenguard-api.onrender.com
```

---

## 🧪 Panel de Pruebas Interactivo

Visita la raíz de la API para acceder al panel de pruebas:

👉 **[https://kitchenguard-api.onrender.com](https://kitchenguard-api.onrender.com)**

Desde el panel puedes:
- 📊 **Ver estado actual** de todos los sensores
- 💨 **Simular niveles de gas** (normal, alto, fuga)
- 🌡️ **Simular temperatura** (35°C, 65°C)
- 🆘 **Activar botón de pánico**
- 🔄 **Resetear sensores**
- 📋 **Ver historial** de lecturas

---

## 📡 Endpoints

### 🔍 Estado del Sistema

#### `GET /status`

Obtiene el estado actual de todos los sensores de la cocina.

**Respuesta exitosa (200):**
```json
{
  "stove_on": false,
  "gas_level": 12.5,
  "temperature": 24.0,
  "humidity": 55,
  "panic": false
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `stove_on` | boolean | `true` si hay fuga de gas activa |
| `gas_level` | float | Nivel de gas en porcentaje (0-100) |
| `temperature` | float | Temperatura en grados Celsius |
| `humidity` | integer | Humedad relativa (fija: 55%) |
| `panic` | boolean | `true` si se activó pánico en los últimos 5 min |

---

### 📊 Sensores

#### `GET /api/sensor`

Historial de lecturas de sensores (últimos 50 registros).

**Respuesta exitosa (200):**
```json
[
  {
    "id": 42,
    "type": "gas",
    "value": 85.0,
    "alert": 1,
    "timestamp": "2026-04-28T22:00:00.000Z"
  },
  {
    "id": 41,
    "type": "temperature",
    "value": 35.5,
    "alert": 0,
    "timestamp": "2026-04-28T21:59:00.000Z"
  }
]
```

#### `POST /api/sensor`

Envía una lectura de sensor.

**Body requerido:**
```json
{
  "type": "gas",
  "value": 85.0,
  "alert": 1
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `type` | string | ✅ | Tipo de sensor: `"gas"` o `"temperature"` |
| `value` | number | ✅ | Valor de la lectura |
| `alert` | integer | ❌ (default: 0) | `0` = normal, `1` = alerta activa |

**Respuesta exitosa (201):**
```json
{
  "message": "Lectura guardada",
  "type": "gas",
  "value": 85.0,
  "alert": 1
}
```

**Respuesta error (400):**
```json
{
  "error": "Faltan campos: type y value"
}
```

---

### 🆘 Botón de Pánico

#### `GET /api/panic`

Historial de eventos de pánico (últimos 20).

**Respuesta exitosa (200):**
```json
[
  {
    "id": 1,
    "timestamp": "2026-04-28T22:05:00.000Z"
  }
]
```

#### `POST /api/panic`

Activa el botón de pánico. **Envía notificaciones push** a todos los dispositivos registrados vía Firebase.

**Body:** `{}` (vacío)

**Respuesta exitosa (201):**
```json
{
  "message": "Alerta de panico registrada",
  "id": 2
}
```

---

### 📱 Notificaciones Push

#### `POST /register-token`

Registra un token de dispositivo Expo para recibir notificaciones push.

**Body:**
```json
{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
}
```

**Respuesta exitosa (200):**
```json
{
  "message": "Token registrado"
}
```

---

## 🔄 Flujo de Datos

```
📱 App Móvil ──→ POST /register-token (registrar dispositivo)
     │
     ├──→ GET /status (cada 3 segundos - polling)
     │
     ├──→ POST /api/sensor (enviar lectura de gas/temperatura)
     │
     └──→ POST /api/panic (activar pánico)

💻 App Web ──→ GET /status + GET /api/sensor (dashboard)

🔥 Firebase ──→ Notificaciones push a dispositivos registrados
```

---

## 🛠️ Tecnologías Utilizadas

| Tecnología | Uso |
|------------|-----|
| **Python 3** | Lenguaje principal |
| **Flask 3.0** | Framework web |
| **Flask-CORS** | Habilitar peticiones cross-origin |
| **SQLite** | Base de datos local |
| **Firebase Admin SDK** | Envío de notificaciones push |
| **Render** | Despliegue en la nube (gratuito) |
| **Raspberry Pi** | Servidor local de respaldo |
| **ngrok** | Túnel para exponer servidor local |

---

## 🏠 Instalación Local

### Requisitos previos
- Python 3.8 o superior
- pip (gestor de paquetes)
- Firebase Admin SDK (`firebase-key.json`)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/AleRodriguezCruz/KitchenGuard_API.git
cd KitchenGuard_API

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar Firebase
# Coloca tu archivo firebase-key.json en la raíz del proyecto

# 4. Ejecutar
python app.py
```

La API estará disponible en: **`http://localhost:5000`**

---

## 🧪 Pruebas con cURL

```bash
# Ver estado
curl http://localhost:5000/status

# Enviar lectura de gas
curl -X POST http://localhost:5000/api/sensor \
  -H "Content-Type: application/json" \
  -d '{"type":"gas","value":85,"alert":1}'

# Enviar temperatura
curl -X POST http://localhost:5000/api/sensor \
  -H "Content-Type: application/json" \
  -d '{"type":"temperature","value":65}'

# Activar pánico
curl -X POST http://localhost:5000/api/panic \
  -H "Content-Type: application/json" \
  -d '{}'

# Ver historial
curl http://localhost:5000/api/sensor

# Registrar token push
curl -X POST http://localhost:5000/register-token \
  -H "Content-Type: application/json" \
  -d '{"token":"ExponentPushToken[test123]"}'
```

---

## 📱 Apps Conectadas

| Plataforma | URL | Descripción |
|------------|-----|-------------|
| 🌐 **Web App** | [kitchenguard-six.vercel.app](https://kitchenguard-six.vercel.app) | Dashboard, Timers, Historial, QR |
| 📱 **App Móvil** | Expo Go | iOS & Android con Supabase Auth |
| 🐍 **Raspberry Pi** | Local + ngrok | Servidor de respaldo |

---

## 📁 Estructura del Proyecto

```
KitchenGuard_API/
├── app.py                  # Aplicación principal Flask
├── database.py             # Conexión y creación de SQLite
├── requirements.txt        # Dependencias Python
├── firebase-key.json       # Credenciales Firebase (NO se sube a Git)
├── kitchenguard.db         # Base de datos SQLite (autogenerada)
├── routes/
│   ├── __init__.py
│   ├── sensors.py          # Rutas de sensores
│   ├── timers.py           # Rutas de temporizadores
│   └── panic.py            # Rutas de pánico
└── README.md               # Documentación
```

---

## ⚠️ Consideraciones

### Render (Plan Gratuito)
- La API **se duerme** después de 15 minutos de inactividad
- La primera petición puede tardar **30-50 segundos** en responder
- Para mantenerla activa: usar un servicio como [UptimeRobot](https://uptimerobot.com)

### Firebase
- Las notificaciones push requieren que el dispositivo tenga la app **en segundo plano**
- El archivo `firebase-key.json` **NUNCA** se sube a GitHub
- En Render, se configura como **Secret File**

### SQLite
- Los datos se guardan en un archivo local `kitchenguard.db`
- En Render, los datos **persisten entre deploys** pero pueden perderse si se recrea el servicio

---

## 📄 Licencia

MIT © 2026 KitchenGuard

---

## 👩‍💻 Autora

**Alejandra Rodríguez de la Cruz**
**Flor Jazmin Mayon Cisneros**
- GitHub: [@AleRodriguezCruz](https://github.com/AleRodriguezCruz)
- Proyecto: [KitchenGuard_API](https://github.com/AleRodriguezCruz/KitchenGuard_API)

---

<div align="center">
  <p>🍎 Hecho con ❤️ para proteger tu cocina</p>
</div>