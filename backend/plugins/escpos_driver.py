from escpos.printer import Usb
import logging

logger = logging.getLogger("EscposPrinter")

class PrinterDriver:
    def __init__(self):
        self.idVendor = 0x04b8 # Generic Epson
        self.idProduct = 0x0202
        self.printer = None
        self.status = "offline"
        self._connect()

    def _connect(self):
        try:
            self.printer = Usb(self.idVendor, self.idProduct, timeout=0)
            self.status = "ok"
            logger.info(f"Connected to printer {hex(self.idVendor)}:{hex(self.idProduct)}")
        except Exception as e:
            self.status = "error"
            self.printer = None
            logger.error(f"Failed to connect to printer: {e}")

    def get_status(self):
        # Auto-reconnect try if offline
        if self.status in ["offline", "error"]:
            self._connect()
            
        return {
            "status": self.status,
            "idVendor": hex(self.idVendor),
            "idProduct": hex(self.idProduct)
        }

    def print_receipt(self, data):
        if not self.printer:
            self._connect()
        if not self.printer:
            return {"success": False, "error": "Printer not connected"}
            
        try:
            # We assume data is raw ESCPOS or string
            if isinstance(data, str):
                self.printer.text(data + "\n")
            elif isinstance(data, dict) and 'receipt' in data:
                self.printer.text(data['receipt'] + "\n")
                
            self.printer.cut()
            return {"success": True}
        except Exception as e:
            self.status = "error"
            logger.error(f"Print failed: {e}")
            return {"success": False, "error": str(e)}

    def teardown(self):
        if self.printer:
            try:
                self.printer.close()
            except:
                pass

def setup(plugin_manager):
    driver = PrinterDriver()
    return driver
