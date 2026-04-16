from escpos.printer import Usb
import usb.core
import logging

logger = logging.getLogger("EscposPrinter")

PLUGIN_NAME = "Controlador Impresoras ESC/POS"
PLUGIN_VERSION = "2.1.0"

class PrinterDriver:
    def __init__(self):
        self.idVendor = None
        self.idProduct = None
        self.printer = None
        self.status = "offline"
        self._connect()

    def _connect(self):
        try:
            # Universal discovery: find first USB device acting as a printer (bDeviceClass=7)
            # or known ESCPOS vendor/product pairs (class 255 vendor specific sometimes).
            found_printer = None
            
            # Common ESC/POS Vendor IDs (Epson, Bixolon, Star, generic thermal)
            escpos_vids = [0x04b8, 0x0483, 0x1fc9, 0x154f, 0x0519, 0x4B8, 0x0dd4]
            
            # First try pyusb find
            devices = usb.core.find(find_all=True)
            for dev in devices:
                # Check for Printer class (7) in device or across interfaces
                is_printer = False
                if dev.bDeviceClass == 7:
                    is_printer = True
                else:
                    for cfg in dev:
                        for intf in cfg:
                            if intf.bInterfaceClass == 7:
                                is_printer = True
                                break
                                
                if is_printer or dev.idVendor in escpos_vids:
                    found_printer = dev
                    break
                    
            if found_printer:
                self.idVendor = found_printer.idVendor
                self.idProduct = found_printer.idProduct
                
                # Attempt connection with auto-endpoint resolution
                self.printer = Usb(self.idVendor, self.idProduct)
                self.status = "ok"
                logger.info(f"Dynamically connected to universal printer {hex(self.idVendor)}:{hex(self.idProduct)}")
            else:
                self.status = "error"
                self.printer = None
                logger.error("No USB printer found dynamically.")
                
        except BaseException as e:
            self.status = "error"
            self.printer = None
            logger.error(f"Failed to connect to printer: {e}")

    def get_status(self):
        # Auto-reconnect try if offline
        if self.status in ["offline", "error"]:
            self._connect()
            
        return {
            "status": self.status,
            "idVendor": hex(self.idVendor) if self.idVendor else None,
            "idProduct": hex(self.idProduct) if self.idProduct else None
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
