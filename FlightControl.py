import time
from pynput import keyboard

class DroneInput:
    def __init__(self):
        # Stato neutro iniziale
        self.roll = 128
        self.pitch = 128
        self.throttle = 128
        self.yaw = 128
        
        # Comandi speciali
        self.flight_mode_requested = False
        self.arm_requested = False
        self.exit_requested = False
        self.mode_code = None  # 0x01 per GPS, 0x02 per Optical Flow

        # Step di manovra
        self.step = 10
        self.rate = 90  # variazione al secondo per pressione continua

        # Stato pressione tasti
        self._pressed = set()
        self._last_update = time.monotonic()

    def start_listener(self):
        # Avvia il listener in un thread separato
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def update(self, dt=None):
        if dt is None:
            now = time.monotonic()
            dt = now - self._last_update
            self._last_update = now

        if 'w' in self._pressed:
            self.throttle = self._clamp(self.throttle + int(self.rate * dt))
        if 's' in self._pressed:
            self.throttle = self._clamp(self.throttle - int(self.rate * dt))
        if 'a' in self._pressed:
            self.yaw = self._clamp(self.yaw - int(self.rate * dt))
        if 'd' in self._pressed:
            self.yaw = self._clamp(self.yaw + int(self.rate * dt))
        if 'up' in self._pressed:
            self.pitch = self._clamp(self.pitch + int(self.rate * dt))
        if 'down' in self._pressed:
            self.pitch = self._clamp(self.pitch - int(self.rate * dt))
        if 'left' in self._pressed:
            self.roll = self._clamp(self.roll - int(self.rate * dt))
        if 'right' in self._pressed:
            self.roll = self._clamp(self.roll + int(self.rate * dt))

    def _clamp(self, val):
        return max(0, min(255, val))

    def _on_press(self, key):
        try:
            # --- Tasti Alfanumerici ---
            if hasattr(key, 'char') and key.char:
                c = key.char.lower()
                self._pressed.add(c)
                if c == 'w':
                    self.throttle = self._clamp(self.throttle + self.step)
                elif c == 's':
                    self.throttle = self._clamp(self.throttle - self.step)
                elif c == 'a':
                    self.yaw = self._clamp(self.yaw - self.step)
                elif c == 'd':
                    self.yaw = self._clamp(self.yaw + self.step)
                elif c == 'm':
                    self.flight_mode_requested = True
                elif c == 'n':
                    self.flight_mode_requested = False
                elif c == 'u':
                    self.arm_requested = True # Segnale a impulso
                elif c == 'o':
                    self.mode_code = 0x02
                elif c == 'g':
                    self.mode_code = 0x01
                elif c == 'q':
                    self.exit_requested = True

            # --- Tasti Speciali (Frecce e Spazio) ---
            else:
                if key == keyboard.Key.up:
                    self._pressed.add('up')
                    self.pitch = self._clamp(self.pitch + self.step)
                elif key == keyboard.Key.down:
                    self._pressed.add('down')
                    self.pitch = self._clamp(self.pitch - self.step)
                elif key == keyboard.Key.left:
                    self._pressed.add('left')
                    self.roll = self._clamp(self.roll - self.step)
                elif key == keyboard.Key.right:
                    self._pressed.add('right')
                    self.roll = self._clamp(self.roll + self.step)
                elif key == keyboard.Key.space:
                    # Reset di emergenza
                    self.roll, self.pitch, self.throttle, self.yaw = 128, 128, 128, 128

        except Exception:
            pass

    def _on_release(self, key):
        # RILASCIO NATIVO: Appena molli una direzione, torna subito al centro!
        try:
            if hasattr(key, 'char') and key.char:
                c = key.char.lower()
                if c in self._pressed:
                    self._pressed.discard(c)
                if c in ['a', 'd']:
                    self.yaw = 128  # Ferma la rotazione
                elif c in ['w', 's']:
                    self.throttle = 128  # Ferma l'altezza
            else:
                if key in [keyboard.Key.up, keyboard.Key.down]:
                    if key == keyboard.Key.up:
                        self._pressed.discard('up')
                    if key == keyboard.Key.down:
                        self._pressed.discard('down')
                    self.pitch = 128  # Ferma il beccheggio
                elif key in [keyboard.Key.left, keyboard.Key.right]:
                    if key == keyboard.Key.left:
                        self._pressed.discard('left')
                    if key == keyboard.Key.right:
                        self._pressed.discard('right')
                    self.roll = 128   # Ferma il rollio
        except Exception:
            pass