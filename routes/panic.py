from flask import Blueprint, jsonify
from database import get_connection

panic_bp = Blueprint("panic", __name__)

@panic_bp.route("/api/panic", methods=["POST"])
def panic_button():
    supabase = get_connection()
    result = supabase.table("panic_events").insert({}).execute()
    
    print("🆘 BOTON DE PANICO ACTIVADO")
    return jsonify({
        "message": "Alerta de panico registrada",
        "id": result.data[0]["id"] if result.data else 0
    }), 201

@panic_bp.route("/api/panic", methods=["GET"])
def get_panic_events():
    supabase = get_connection()
    result = supabase.table("panic_events").select("*").order("timestamp", desc=True).limit(20).execute()
    return jsonify(result.data), 200