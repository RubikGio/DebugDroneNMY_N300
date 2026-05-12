import argparse
import socket
import time
from FlightControl import DroneInput

# Costanti Rete
DRONE_IP = "192.168.80.1"
UDP_PORT = 3456
KEEP_ALIVE  = 0x65
LOCK_MODE   = 0x67  
USE_MODE    = 0x69  
FLIGHT_MODE = 0x6A  

sock_snd = None

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

    try:
        while True:
            controller.update()
            
            # 1. Controllo Uscita
            if controller.exit_requested:
                print("\n[!] Richiesta uscita (Q ricevuta)...")
                break
                
            # 2. Controllo Cambio Modalità (GPS / Flow)
            if controller.mode_code is not None:
                if not test_mode:
                    sock_snd.sendto(build_frame(USE_MODE, bytes([controller.mode_code])), (DRONE_IP, UDP_PORT))
                controller.mode_code = None 
                
            # 3. Controllo Sblocco Motori (U)
            if controller.arm_requested:
                if not test_mode:
                    sock_snd.sendto(build_frame(LOCK_MODE, bytes([0x00])), (DRONE_IP, UDP_PORT))
                controller.arm_requested = False 

            # 4. Invio Flusso Dati Principale
            if controller.flight_mode_requested:
                data = bytes([controller.roll, controller.pitch, controller.throttle, controller.yaw])
                if not test_mode:
                    sock_snd.sendto(build_frame(FLIGHT_MODE, data), (DRONE_IP, UDP_PORT))
            else:
                if not test_mode:
                    sock_snd.sendto(build_frame(KEEP_ALIVE, bytes([0x01])), (DRONE_IP, UDP_PORT))

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
        if test_mode:
            print("\n[!] Uscita modalita test.")
        else:
            print("\n[!] Spegnimento d'emergenza motori e chiusura socket...")
            sock_snd.sendto(build_frame(LOCK_MODE, bytes([0x01])), (DRONE_IP, UDP_PORT))
            sock_snd.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Avvia in modalita test (no UDP)")
    args = parser.parse_args()
    main(test_mode=args.test)