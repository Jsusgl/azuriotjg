import serial
import time
import threading
import logging
from serial.tools import list_ports

logger = logging.getLogger("ITAequipmentScale")

class ScaleConnectionError(Exception):
    pass

class ITAequipmentScaleDriver:
    def __init__(self):
        self.serial_port = None
        self.baudrate = 9600
        self.is_connected = False
        self.running = False
        self.thread = None
        self.current_weight = 0.0
        self.current_status = "offline"
        self._connect_scale()

    def _connect_scale(self):
        ports = [p.device for p in list_ports.comports()]
        port_list = list(ports)
        port_list.insert(0, '/dev/balanza')
        
        for port in port_list:
            try:
                self.serial_port = serial.Serial(port, baudrate=self.baudrate, timeout=1)
                self.is_connected = True
                self.current_status = "ok"
                logger.info(f"Connected to scale on port {port} at {self.baudrate} baud.")
                return
            except Exception as e:
                logger.debug(f"Failed to connect on {port}: {e}")
                
        self.is_connected = False
        self.current_status = "error"
        logger.error("Could not find or connect to scale on any port.")
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def _run_loop(self):
        while self.running:
            if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                time.sleep(2)
                self._connect_scale()
                continue
                
            try:
                self._parse_weight()
            except Exception as e: # Catch any other errors to avoid thread death
                if isinstance(e, serial.SerialException):
                    self.current_status = "error"
                    self.is_connected = False
                    if self.serial_port and self.serial_port.is_open:
                        self.serial_port.close()
                    logger.warning(f"Scale connection lost: {e}. Attempting to reconnect...")
                else:
                    logger.error(f"Error parsing weight: {e}")
                time.sleep(1)
            time.sleep(0.1)

    def _parse_weight(self):
        if not self.serial_port.in_waiting:
            return
            
        raw_data = self.serial_port.readline()
        if not raw_data:
            return
            
        logger.debug(f"RAW DATA RECEIVED: {raw_data}") # critical log for debugging payload errors
        try:
            data_str = raw_data.decode('ascii', errors='ignore').strip()
            if not data_str:
                return
            import re
            match = re.search(r'[-+]?\d*\.\d+|\d+', data_str)
            if match:
                self.current_weight = float(match.group())
            else:
                raise ScaleConnectionError("unparsable payload")
        except Exception as e:
            if isinstance(e, ScaleConnectionError):
                raise
            raise ScaleConnectionError(str(e))

    def read_weight(self):
        return {
            "weight": self.current_weight,
            "unit": "kg",
            "status": self.current_status
        }
        
    def get_status(self):
        return {
            "connected": self.is_connected,
            "status": self.current_status,
            "port": self.serial_port.name if self.serial_port else None
        }
        
    def teardown(self):
        self.stop()

def setup(plugin_manager):
    driver = ITAequipmentScaleDriver()
    driver.start()
    return driver
