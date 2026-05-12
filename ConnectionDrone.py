import argparse
import os
import socket
import subprocess
import sys
import time
import fcntl
from FlightControl import DroneInput

# Costanti Rete
DRONE_IP = "192.168.80.1"
UDP_PORT = 3456
KEEP_ALIVE  = 0x65
LOCK_MODE   = 0x67  
USE_MODE    = 0x69  
FLIGHT_MODE = 0x6A  
LOG_PATH = "Log/telemetry.log"

sock_snd = None
telemetry_proc = None

def checkSum(data):
    check = 0
    for b in data: 
        check ^= b
    return check

def build_frame(opcode, payload):
    frame = bytearray([0x46, 0x48, 0x3C, opcode])
    frame.extend(len(payload).to_bytes(2, byteorder="little"))
    frame.extend(payload)
    frame.append(checkSum(frame[3:]))
    return frame

def _now_stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _write_log(direction, payload, src, dst):
    line = (
        f"{_now_stamp()} {direction} src={src} dst={dst} "
        f"len={len(payload)} hex={payload.hex()}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
        except OSError:
            pass
        f.write(line)
        try:
            fcntl.flock(f, fcntl.LOCK_UN)
        except OSError:
            pass

def _send_frame(opcode, payload, test_mode):
    frame = build_frame(opcode, payload)
    if not test_mode:
        sock_snd.sendto(frame, (DRONE_IP, UDP_PORT))
        local_addr = sock_snd.getsockname()
        src = f"{local_addr[0]}:{local_addr[1]}"
        dst = f"{DRONE_IP}:{UDP_PORT}"
        _write_log("TX", frame, src, dst)
    return frame

def _start_telemetry():
    script_path = os.path.join(os.path.dirname(__file__), "Telemtry.py")
    return subprocess.Popen([sys.executable, script_path])

def main(test_mode=False):
    print("\n[!] Avvio Stazione di Controllo Silenziosa...")
    
    # Inizializza e avvia il modulo di input
    controller = DroneInput()
    controller.start_listener()
    
    print("[!] Listener Tastiera Attivo in Background.")
    print("[!] GCS in esecuzione a 20Hz. Interfaccia pulita.")
    print("[!] Tasti: 'U'=Sblocca | 'M'=Pilota | 'N'=Rilascia | 'Q'=Esci\n")

    if test_mode:
        print("[TEST] Modalita test attiva: nessun invio UDP.")
    else:
        global sock_snd
        sock_snd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    global telemetry_proc
    if not test_mode:
        telemetry_proc = _start_telemetry()

    try:
        while True:
            controller.update()
            
            # 1. Controllo Uscita
            if controller.exit_requested:
                print("\n[!] Richiesta uscita (Q ricevuta)...")
                break
                
            # 2. Controllo Cambio Modalità (GPS / Flow)
            if controller.mode_code is not None:
                _send_frame(USE_MODE, bytes([controller.mode_code]), test_mode)
                controller.mode_code = None 
                
            # 3. Controllo Sblocco Motori (U)
            if controller.arm_requested:
                _send_frame(LOCK_MODE, bytes([0x00]), test_mode)
                controller.arm_requested = False 

            # 4. Invio Flusso Dati Principale
            if controller.flight_mode_requested:
                data = bytes([controller.roll, controller.pitch, controller.throttle, controller.yaw])
                _send_frame(FLIGHT_MODE, data, test_mode)
            else:
                _send_frame(KEEP_ALIVE, bytes([0x01]), test_mode)

            if test_mode:
                print(
                    f"\r[TEST] R:{controller.roll:3d} P:{controller.pitch:3d} "
                    f"T:{controller.throttle:3d} Y:{controller.yaw:3d}",
                    end="",
                    flush=True,
                )

            # Nessuna stampa qui: il terminale rimane perfettamente statico e pulito
            time.sleep(0.05) 
            
    finally:
        if telemetry_proc and telemetry_proc.poll() is None:
            telemetry_proc.terminate()
            try:
                telemetry_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                telemetry_proc.kill()
        if test_mode:
            print("\n[!] Uscita modalita test.")
        else:
            print("\n[!] Spegnimento d'emergenza motori e chiusura socket...")
            _send_frame(LOCK_MODE, bytes([0x01]), test_mode)
            sock_snd.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Avvia in modalita test (no UDP)")
    args = parser.parse_args()
    main(test_mode=args.test)