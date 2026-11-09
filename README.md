# AzurIoT - Middleware & IoT Gateway para Odoo POS

**AzurIoT** es un middleware ligero y modular de pasarela IoT (IoT Box alternativa) diseñado para conectar periféricos de Punto de Venta (TPV / POS) físicos con **Odoo** (optimizado para Odoo 18).

Permite interactuar de forma transparente con balanzas seriales (RS232/USB), impresoras térmicas de tickets (ESC/POS vía USB) y lectores de códigos de barras (HID Keyboard), ofreciendo además una interfaz web moderna en tiempo real para diagnóstico, monitoreo de hardware y telemetría del sistema.

---

## 🚀 Características Principales

- **Compatibilidad con Odoo POS (`hw_proxy`)**:
  - Emula y responde a los endpoints estándar de hardware proxy de Odoo:
    - `/hw_proxy/scale_read` (Lectura de balanza).
    - `/hw_proxy/print_receipt` (Impresión de tickets ESC/POS).
    - `/hw_proxy/scanner_read` (Lectura de escáner óptico).
    - `/hw_proxy/status` (Estado general del hardware).
- **Arquitectura Basada en Plugins Modulares**:
  - Gestor dinámico (`PluginManager`) con capacidad de descubrimiento automático, carga, recarga y descarga en caliente de drivers sin reiniciar el servidor.
- **Drivers de Periféricos Incluidos**:
  - **Balanza Electrónica RS232/Serial** (`ita_equipment.py`): Lectura en hilo continuo (`threading`), detección de puertos comports / `/dev/balanza` y parsing robusto con expresiones regulares.
  - **Ticketera Térmica ESC/POS** (`escpos_driver.py`): Autodescubrimiento de impresoras USB mediante clases USB estándar (Class 7 - Printer) y Vendors comunes (Epson, Bixolon, Star, etc.).
  - **Lector de Códigos de Barras** (`barcode_scanner.py`): Captura universal de ráfagas de teclado HID vía hooks globales de `keyboard`.
- **Dashboard Web Moderno (Glassmorphism UI)**:
  - Vista de estado de periféricos en tiempo real con lecturas de peso y tickets.
  - Gestión y alternancia (start/stop) de plugins en caliente.
  - Telemetría en vivo del sistema (Uso de CPU, memoria RAM y almacenamiento con `psutil`).
  - Visor interactivo de registros (log viewer).
- **Listo para Producción en Linux / Raspberry Pi**:
  - Scripts de configuración de `udev` para nombres de dispositivos fijos.
  - Script para deshabilitar el driver del kernel `usblp` (necesario para acceso exclusivo a impresoras USB).
  - Servicio configurado para `systemd` y proxy inverso para `Nginx` con soporte SSL.

---

## 📁 Estructura del Proyecto

```text
azuriot/
├── backend/
│   ├── plugins/                    # Drivers modulares de periféricos
│   │   ├── barcode_scanner.py      # Lector de códigos de barras (HID)
│   │   ├── escpos_driver.py        # Impresora térmica USB (ESC/POS)
│   │   └── ita_equipment.py        # Balanza serial (RS232)
│   ├── static/                     # Assets web (CSS & JS)
│   │   ├── css/
│   │   │   └── style.css           # Estilos Glassmorphism UI
│   │   └── js/
│   │       ├── app.js              # Lógica de dashboard y hardware
│   │       ├── plugins.js          # Control de plugins
│   │       └── system.js           # Métricas del sistema en tiempo real
│   ├── templates/                  # Vistas HTML (Jinja2 / Flask)
│   │   ├── dashboard.html          # Panel principal de hardware
│   │   ├── plugins.html            # Gestión de drivers y plugins
│   │   └── system.html             # Métricas de CPU, RAM y disco
│   ├── plugin_manager.py           # Gestor dinámico de plugins
│   ├── requirements.txt            # Dependencias Python
│   └── server.py                   # Servidor principal Flask (API + Web)
├── nginx/
│   └── azuriot.conf                # Configuración de proxy inverso Nginx
├── scripts/
│   ├── azuriot-start.sh            # Script de arranque del backend
│   ├── setup-blacklist.sh          # Blacklist del kernel para módulo usblp
│   └── setup-udev.sh               # Reglas udev para puertos serie persistentes
└── systemd/
    └── azuriot.service             # Definición del servicio systemd
```

---

## 🛠️ Requisitos Previos

- **Sistema Operativo**: Linux (Debian, Ubuntu, Raspberry Pi OS recomendado).
- **Python**: 3.9 o superior.
- **Acceso Root/Sudo**: Para configuración de reglas `udev`, `systemd` y `usblp`.
- **Dependencias del sistema** (librerías USB y compiladores):
  ```bash
  sudo apt update
  sudo apt install -y python3-pip python3-venv libusb-1.0-0-dev nginx
  ```

---

## 📦 Instalación y Configuración

### 1. Clonar y Ubicar el Proyecto
Por convención con los scripts del sistema, se recomienda desplegar en `/opt/azuriot`:
```bash
sudo mkdir -p /opt/azuriot
sudo chown -R $USER:$USER /opt/azuriot
cp -r . /opt/azuriot/
cd /opt/azuriot/backend
```

### 2. Crear Entorno Virtual e Instalar Dependencias
```bash
python3 -m venv /opt/azuriot/venv
source /opt/azuriot/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuración de Hardware en Linux

#### A. Evitar Conflicto con la Impresora USB (`usblp`)
En Linux, el driver del kernel `usblp` suele tomar posesión de las impresoras térmicas e impedir que `pyusb` y `python-escpos` envíen comandos directos. Ejecute el script de blacklist:
```bash
cd /opt/azuriot/scripts
chmod +x *.sh
sudo ./setup-blacklist.sh
```
*(Requiere reiniciar el equipo para aplicar).*

#### B. Asignar Nombre Fijo a la Balanza Serial (`udev`)
Para que la balanza siempre esté accesible en `/dev/balanza` sin importar el orden de conexión USB:
1. Conecte su adaptador RS232-USB y verifique su Vendor/Product ID con `lsusb`:
   ```bash
   lsusb
   # Ejemplo: ID 0403:6001 Future Technology Devices International...
   ```
2. Edite `scripts/setup-udev.sh` con los IDs correctos si son diferentes a `0403:6001`.
3. Aplique la regla:
   ```bash
   sudo ./setup-udev.sh
   ```

---

## 🚦 Ejecución

### Modo Desarrollo / Manual
```bash
source /opt/azuriot/venv/bin/activate
cd /opt/azuriot/backend
python server.py
```
El servidor quedará accesible en:
- **Panel Web**: `http://localhost:8069/`
- **Proxy Odoo**: `http://localhost:8069/hw_proxy/...`

### Modo Producción con Systemd
1. Crear el usuario del servicio si aún no existe:
   ```bash
   sudo useradd -r -s /bin/false azuriot || true
   sudo usermod -aG dialout,plugdev azuriot
   sudo chown -R azuriot:azuriot /opt/azuriot
   ```
2. Instalar y habilitar el servicio:
   ```bash
   sudo cp /opt/azuriot/systemd/azuriot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable azuriot
   sudo systemctl start azuriot
   ```
3. Verificar el estado del servicio:
   ```bash
   sudo systemctl status azuriot
   ```

### Configuración con Nginx (Opcional - HTTPS)
Para conectar con instancias remotas de Odoo que requieren comunicación segura vía HTTPS / WSS:
```bash
sudo cp /opt/azuriot/nginx/azuriot.conf /etc/nginx/sites-available/azuriot.conf
sudo ln -s /etc/nginx/sites-available/azuriot.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔌 Configuración en Odoo Punto de Venta (POS)

1. En Odoo, diríjase a **Punto de Venta** > **Configuración** > **Ajustes**.
2. Ubique la sección **Dispositivos IoT / IoT Box**.
3. Active la opción **Caja IoT (IoT Box)** o **Hardware Proxy**.
4. Configure la dirección IP de su dispositivo AzurIoT (por ejemplo: `http://192.168.1.50:8069` o el dominio HTTPS configurado en Nginx).
5. Active los periféricos correspondientes:
   - **Balanza electrónica**: Activada.
   - **Lector de código de barras**: Activado.
   - **Impresora de recibos**: Activada.

---

## 📡 Referencia de la API

### Endpoints para Odoo POS (`/hw_proxy`)

| Método | Endpoint | Descripción | Formato Respuesta |
| :--- | :--- | :--- | :--- |
| `GET` | `/hw_proxy/scale_read` | Retorna el peso actual detectado por la balanza. | `{"weight": 1.250, "unit": "kg", "status": "ok"}` |
| `GET` | `/hw_proxy/scanner_read` | Retorna el último código de barras escaneado. | `{"last_scan": "7791234567890", "status": "ok"}` |
| `POST` | `/hw_proxy/print_receipt`| Recibe payload de ticket e imprime vía ESC/POS. | `{"success": true}` o `{"success": false, "error": "..."}` |
| `GET` | `/hw_proxy/status` | Devuelve el estado de todos los plugins y periféricos. | `{"status": "ok", "plugins": [...]}` |

### Endpoints de Gestión y UI (`/api`)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/plugins` | Lista detallada de plugins instalados, versiones y estados. |
| `POST` | `/api/plugins/toggle` | Activa o desactiva un driver (`{"name": "...", "action": "start\|stop"}`). |
| `GET` | `/api/system` | Métricas de CPU (%), Memoria RAM y Almacenamiento en disco. |

---

## 🧩 Creación de Nuevos Plugins

Para añadir un nuevo driver de periférico:
1. Cree un nuevo archivo Python en `backend/plugins/mi_driver.py`.
2. Defina los metadatos y la clase controladora:
   ```python
   PLUGIN_NAME = "Mi Nuevo Dispositivo"
   PLUGIN_VERSION = "1.0.0"

   class MiDispositivoDriver:
       def __init__(self):
           self.status = "ok"

       def get_status(self):
           return {"status": self.status}

       def teardown(self):
           # Liberación de recursos / puertos
           pass

   def setup(plugin_manager):
       driver = MiDispositivoDriver()
       return driver
   ```
3. El `PluginManager` lo descubrirá y cargará automáticamente en el sistema.

---

## 📄 Licencia

Este proyecto se distribuye bajo licencia de código abierto. Consulta los términos de tu organización o el archivo de licencia correspondiente.

