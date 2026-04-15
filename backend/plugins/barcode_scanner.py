import threading
import time
import logging
import keyboard

logger = logging.getLogger("BarcodeScanner")

class BarcodeScannerDriver:
    def __init__(self):
        self.is_connected = False
        self.running = False
        self.current_status = "offline"
        self.last_scan = ""
        self.buffer = ""
        self.last_key_time = 0

    def _on_key_event(self, event):
        if event.event_type == keyboard.KEY_DOWN:
            current_time = time.time()
            # Scanners typically send keystrokes very fast (e.g. < 50ms between keys)
            if current_time - self.last_key_time > 0.1:
                self.buffer = "" # Reset buffer if too much time passed (human typing)
            
            self.last_key_time = current_time
            
            if event.name == 'enter':
                if len(self.buffer) > 3: # Assuming valid barcodes are longer than 3 chars
                    self.last_scan = self.buffer
                    self.current_status = "ok"
                    logger.info(f"Barcode Scanned: {self.last_scan}")
                self.buffer = ""
            elif len(event.name) == 1: # It's a standard character
                self.buffer += event.name

    def start(self):
        self.running = True
        try:
            keyboard.hook(self._on_key_event)
            self.is_connected = True
            # Iniciamos en offline hasta que el escáner registre su primera lectura completa para validar conexión física
            self.current_status = "offline" 
            logger.info("Barcode Scanner universal hook started. Esperando primera lectura...")
        except Exception as e:
            self.current_status = "error"
            self.is_connected = False
            logger.error(f"Failed to start scanner hook: {e}")

    def stop(self):
        self.running = False
        try:
            keyboard.unhook_all()
        except:
            pass
        self.is_connected = False
        self.current_status = "offline"

    def read_scanner(self):
        return {
            "last_scan": self.last_scan,
            "status": self.current_status
        }
        
    def get_status(self):
        return {
            "connected": self.is_connected,
            "status": self.current_status,
            "last_scan": self.last_scan
        }
        
    def teardown(self):
        self.stop()

def setup(plugin_manager):
    driver = BarcodeScannerDriver()
    driver.start()
    return driver
