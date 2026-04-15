from flask import Flask, jsonify, request, render_template
from plugin_manager import PluginManager
import logging
import psutil
# Configure basic logging for the main server
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates', static_folder='static')
pm = PluginManager()

# Automatically load plugins on startup
pm.load_plugin('ita_equipment')
pm.load_plugin('escpos_driver')
pm.load_plugin('barcode_scanner')

# --- FRONTEND ROUTES ---
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/plugins_view')
def plugins_view():
    return render_template('plugins.html')

@app.route('/system_view')
def system_view():
    return render_template('system.html')

# --- ODOO 18 API ENDPOINTS ---
@app.route('/hw_proxy/scale_read', methods=['GET'])
def scale_read():
    scale = pm.get_plugin('ita_equipment')
    if scale:
        return jsonify(scale.read_weight())
    return jsonify({"weight": 0.0, "unit": "kg", "status": "plugin_missing"}), 500

@app.route('/hw_proxy/scanner_read', methods=['GET'])
def scanner_read():
    scanner = pm.get_plugin('barcode_scanner')
    if scanner:
        return jsonify(scanner.read_scanner())
    return jsonify({"last_scan": "", "status": "offline"}), 200

@app.route('/hw_proxy/print_receipt', methods=['POST'])
def print_receipt():
    printer = pm.get_plugin('escpos_driver')
    if printer:
        # Assuming payload has keys like 'receipt'
        data = request.json or {}
        # In case Odoo sends text payload directly
        if request.data and not request.json:
            data = request.data.decode('utf-8', errors='ignore')
        return jsonify(printer.print_receipt(data))
    return jsonify({"success": False, "error": "plugin_missing"}), 500

@app.route('/hw_proxy/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ok", "plugins": pm.get_all_status()})

# --- UI MANAGEMENT API ---
@app.route('/api/plugins', methods=['GET'])
def api_get_plugins():
    return jsonify(pm.get_all_status())

@app.route('/api/plugins/toggle', methods=['POST'])
def api_toggle_plugin():
    data = request.json
    name = data.get('name')
    action = data.get('action')
    
    success = False
    message = ""
    
    if action == 'start':
        success = pm.load_plugin(name)
        if success:
            instance = pm.get_plugin(name)
            if instance and hasattr(instance, 'get_status'):
                st = instance.get_status()
                # Check hardware status
                if st.get('status') in ['error', 'offline']:
                    message = "Driver activado, pero hardware no conectado físicamente. Buscando..."
                else:
                    message = f"Driver de {name} iniciado y conectado correctamente."
            else:
                message = f"Driver de {name} iniciado."
        else:
            message = "Error interno al iniciar el plugin."
            
    elif action == 'stop':
        success = pm.unload_plugin(name)
        message = f"Driver {name} detenido."
        
    return jsonify({"success": success, "message": message})

@app.route('/api/system', methods=['GET'])
def api_system():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return jsonify({
        "cpu_percent": cpu,
        "memory": {
            "percent": mem.percent,
            "used": mem.used,
            "total": mem.total
        },
        "disk": {
            "percent": disk.percent,
            "used": disk.used,
            "total": disk.total
        }
    })

if __name__ == '__main__':
    logging.info("Starting AzurIoT Backend on port 8069")
    # For production, we'd use waitress, gunicorn, etc. 
    # But for an internal proxy on a Raspberry Pi, Flask's threaded dev server handles lightweight traffic fine.
    app.run(host='0.0.0.0', port=8069, threaded=True)
