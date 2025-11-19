"""
run_render.py - Arranca solo el bot de Telegram (sin webserver) - v2
"""
import sys
import os

if __name__ == "__main__":
    print("[RUN_RENDER v2] Iniciando bot de Telegram sin webserver...")
    print(f"[RUN_RENDER v2] Python: {sys.version}")
    print(f"[RUN_RENDER v2] Working dir: {os.getcwd()}")
    try:
        import bot_telegram
        bot_telegram.main()
    except Exception as e:
        print(f"[RUN_RENDER v2] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
