import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://shvsgwvzqmmcbvpkqwig.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNodnNnd3Z6cW1tY2J2cGtxd2lnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNTA5OTksImV4cCI6MjA4ODkyNjk5OX0.VeilcM-9rg_TkA6EhDW0x46lxUQv4UHIwtA57M6sGXQ")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_connection():
    """Devuelve el cliente de Supabase (reemplaza la conexión SQLite)"""
    return supabase

def init_db():
    """Las tablas ya se crearon en Supabase, no necesita hacer nada"""
    print("✅ Conectado a Supabase PostgreSQL")