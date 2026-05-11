import socket
import sys
import select
import termios
import tty
import time

# -- VALORI COSTANTI DA CONFIGURARE --
DRONE_IP = "192.168.80.1"
UDP_PORT = 3456

# OPCODE
KEEP_ALIVE = 0x65
LOCK_MODE  = 0x67  # Arm/Disarm motori
USE_MODE   = 0x69  # Selezione flusso ottico/GPS
FLIGHT_MODE= 0x6A  # Comando Joystick

RC_NEUTRAL = 0x80  # 128 (Centro perfetto)
RC_MIN = 0x00
RC_MAX = 0xFF
RC_STEP = 8
TELEMETRY_TIMEOUT_SEC = 1.0

# CORREZIONE INDICI TELEMETRIA (Tutto risiede nel Byte 12)
TELEMETRY_STATE_BYTE = 12

sock_rcv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_rcv.bind(("0.0.0.0", UDP_PORT))
sock_rcv.setblocking(False)
sock_snd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

motors_unlocked = False
flight_mode_active = False
last_telemetry_time = 0.0

# Assi di volo inizializzati al centro
roll = RC_NEUTRAL
pitch = RC_NEUTRAL
throttle = RC_NEUTRAL
yaw = RC_NEUTRAL


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

def invia_keepalive():
    pacchetto = build_frame(KEEP_ALIVE, bytes([0x01]))
    sock_snd.sendto(pacchetto, (DRONE_IP, UDP_PORT))
    # Stampiamo a schermo solo se strettamente necessario per non intasare

def invia_flight_frame():
    # CORREZIONE ORDINE PAYLOAD: Rollio, Beccheggio, Gas, Imbardata
    payload = bytes([roll, pitch, throttle, yaw])
    pacchetto = build_frame(FLIGHT_MODE, payload)
    sock_snd.sendto(pacchetto, (DRONE_IP, UDP_PORT))
    print(f"[FLIGHT] R:{roll} P:{pitch} T:{throttle} Y:{yaw} -> {pacchetto.hex(' ')}")

def invia_modalita_volo(mode_value):
    pacchetto = build_frame(USE_MODE, bytes([mode_value]))
    sock_snd.sendto(pacchetto, (DRONE_IP, UDP_PORT))
    mode_name = "GPS" if mode_value == 0x01 else "OPTICAL_FLOW"
    print(f"[MODE:{mode_name}] {pacchetto.hex(' ')}")

def aggiorna_stato_telemetria(byte_packet):
    global motors_unlocked, flight_mode_active, last_telemetry_time
    
    # Controlliamo di aver ricevuto un pacchetto FH> valido e abbastanza lungo
    if len(byte_packet) < 30 or byte_packet[:3] != b"FH>":
        return
        
    byte12 = byte_packet[TELEMETRY_STATE_BYTE]
    
    # ESTRAZIONE CORRETTA DAL BYTE 12 (Come da reverse engineering Java)
    # I 4 bit di destra ( & 15 ) indicano lo stato dei motori
    stato_motori = byte12 & 15
    # I 4 bit di sinistra ( >> 4 ) indicano la modalità logica
    modalita_volo = (byte12 >> 4) & 15

    # Consideriamo sbloccati i motori se lo stato è 1 o 2
    motors_unlocked = (stato_motori == 1 or stato_motori == 2)
    
    # Consideriamo attiva la modalità volo se siamo passati in Indoor (8) o GPS (9)
    flight_mode_active = (modalita_volo == 8 or modalita_volo == 9)
    
    last_telemetry_time = time.time()

def leggi_telemetria_non_blocking():
    try:
        while True:
            byte_packet, _ = sock_rcv.recvfrom(256)
            aggiorna_stato_telemetria(byte_packet)
    except BlockingIOError:
        pass

def clamp(v):
    return max(RC_MIN, min(RC_MAX, v))

def apply_key(key):
    global throttle, roll, pitch, yaw
    if key == "w":
        throttle = clamp(throttle + RC_STEP)
    elif key == "s":
        throttle = clamp(throttle - RC_STEP)
    elif key == "a":
        yaw = clamp(yaw - RC_STEP)
    elif key == "d":
        yaw = clamp(yaw + RC_STEP)
    elif key == "UP":
        pitch = clamp(pitch + RC_STEP)
    elif key == "DOWN":
        pitch = clamp(pitch - RC_STEP)
    elif key == "LEFT":
        roll = clamp(roll - RC_STEP)
    elif key == "RIGHT":
        roll = clamp(roll + RC_STEP)
    elif key == "SPACE":
        # Reset di emergenza di tutti gli assi al centro neutro
        throttle = RC_NEUTRAL
        roll = RC_NEUTRAL
        pitch = RC_NEUTRAL
        yaw = RC_NEUTRAL

def leggi_tasto():
    if not select.select([sys.stdin], [], [], 0.0)[0]:
        return None
    primo = sys.stdin.read(1)
    if primo == "\x1b":
        if select.select([sys.stdin], [], [], 0.0)[0]:
            secondo = sys.stdin.read(1)
            if secondo == "[" and select.select([sys.stdin], [], [], 0.0)[0]:
                terzo = sys.stdin.read(1)
                if terzo == "A": return "UP"
                if terzo == "B": return "DOWN"
                if terzo == "C": return "RIGHT"
                if terzo == "D": return "LEFT"
        return "ESC"
    if primo == " ":
        return "SPACE"
    return primo.lower()

def can_send_flight():
    fresh = (time.time() - last_telemetry_time) <= TELEMETRY_TIMEOUT_SEC
    return fresh and motors_unlocked and flight_mode_active

def print_help():
    print("\n" + "="*50)
    print("  STAZIONE DI CONTROLLO DRONE (PYTHON GCS)")
    print("="*50)
    print(" [W]/[S]     : Incrementa/Decrementa Gas (Throttle)")
    print(" [A]/[D]     : Ruota a Sinistra/Destra (Yaw)")
    print(" [SU]/[GIU]  : Avanti/Indietro (Pitch)")
    print(" [SX]/[DX]   : Traslazione Laterale (Roll)")
    print(" [SPAZIO]    : Riporta tutti i comandi al centro (128)")
    print(" [O] / [G]   : Richiedi Modalità Optical Flow / GPS")
    print(" [Q]         : Chiudi ed esci")
    print("="*50 + "\n")

def main():
    stdin_fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(stdin_fd)
    try:
        tty.setcbreak(stdin_fd)
        print_help()
        while True:
            leggi_telemetria_non_blocking()
            key = leggi_tasto()
            if key == "q":
                break
            if key == "o":
                invia_modalita_volo(0x02)
            elif key == "g":
                invia_modalita_volo(0x01)
            elif key:
                apply_key(key)

            # Logica di sicurezza: inviamo i comandi assi solo se il drone è pronto
            if can_send_flight():
                invia_flight_frame()
            else:
                invia_keepalive()

            # Frequenza di loop a 5 Hz (0.2s) - Aumentabile a 0.05 (20 Hz) per maggiore reattività
            time.sleep(0.2)
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        sock_snd.close()
        sock_rcv.close()

if __name__ == "__main__":
    main()