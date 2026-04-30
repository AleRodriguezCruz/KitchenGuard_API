from flask import Blueprint, jsonify
from database import get_connection

panic_bp = Blueprint("panic", __name__)

@panic_bp.route("/api/panic", methods=["POST"])
def panic_button():
    conn = get_connection()
    cursor = conn.execute("INSERT INTO panic_events DEFAULT VALUES")
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    print("BOTON DE PANICO ACTIVADO")
    return jsonify({
        "message": "Alerta de panico registrada",
        "id":      event_id
    }), 201

@panic_bp.route("/api/panic", methods=["GET"])
def get_panic_events():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM panic_events ORDER BY timestamp DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200