import socket
import time
import fcntl

BROADCAST = "0.0.0.0"
UDP_PORT = 3456
LOG_PATH = "Log/telemetry.log"

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

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((BROADCAST, UDP_PORT))
	print("[!] Telemetria in ascolto su UDP 3456...")

	try:
		while True:
			packet, addr = sock.recvfrom(2048)
			src = f"{addr[0]}:{addr[1]}"
			local = sock.getsockname()
			dst = f"{local[0]}:{local[1]}"
			print(f"{_now_stamp()} RX {src} -> {dst} len={len(packet)} hex={packet.hex()}")
			_write_log("RX", packet, src, dst)
	except KeyboardInterrupt:
		print("\n[!] Interrotto dall'utente.")
	finally:
		sock.close()

if __name__ == "__main__":
	main()
