"""
start_all.py - Inicia ambos procesos: scanner de value bets y bot de comandos Telegram
"""
import subprocess
import sys
import time
import signal
import os

def signal_handler(sig, frame):
    """Maneja Ctrl+C para cerrar ambos procesos"""
    print("\n🛑 Cerrando procesos...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print("🚀 Iniciando Value Bet Bot - Sistema completo")
    print("=" * 50)
    
    # Iniciar el scanner de value bets (main.py via simple_start.py)
    print("\n📊 Iniciando scanner de value bets...")
    scanner_process = subprocess.Popen(
        [sys.executable, "simple_start.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    time.sleep(2)
    
    # Iniciar el bot de comandos de Telegram
    print("\n🤖 Iniciando bot de comandos Telegram...")
    telegram_process = subprocess.Popen(
        [sys.executable, "bot_telegram.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    print("\n✅ Ambos procesos iniciados correctamente")
    print("=" * 50)
    print("\n📝 Logs en tiempo real:\n")
    
    # Mostrar logs de ambos procesos
    try:
        while True:
            # Leer output del scanner
            if scanner_process.poll() is None:
                line = scanner_process.stdout.readline()
                if line:
                    print(f"[SCANNER] {line.strip()}")
            
            # Leer output del bot telegram
            if telegram_process.poll() is None:
                line = telegram_process.stdout.readline()
                if line:
                    print(f"[TELEGRAM] {line.strip()}")
            
            # Si ambos procesos terminaron, salir
            if scanner_process.poll() is not None and telegram_process.poll() is not None:
                break
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo procesos...")
        scanner_process.terminate()
        telegram_process.terminate()
        scanner_process.wait()
        telegram_process.wait()
        print("✅ Procesos detenidos")
