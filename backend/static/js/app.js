function addLog(message, type="info") {
    const viewer = document.getElementById('log-viewer');
    const p = document.createElement('p');
    p.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString();
    p.textContent = `[${time}] ${message}`;
    viewer.appendChild(p);
    viewer.scrollTop = viewer.scrollHeight;
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/plugins');
        const plugins = await res.json();
        
        plugins.forEach(p => {
            const badge = document.getElementById(`badge-${p.name}`);
            if(badge) {
                const status = (p.status_detail && p.status_detail.status) ? p.status_detail.status : p.state;
                badge.className = `badge ${status}`;
                badge.textContent = status;
            }
        });
        
    } catch (e) {
        // Silently fail to avoid console spam
    }
}

async function fetchWeight() {
    try {
        const res = await fetch('/hw_proxy/scale_read');
        const data = await res.json();
        const display = document.getElementById('weight-display');
        
        if (data.status === 'ok' || data.status === 'active') {
            display.textContent = data.weight.toFixed(3);
        } else {
            display.textContent = "---";
        }
    } catch (e) {
        const display = document.getElementById('weight-display');
        display.textContent = "ERR";
    }
}

async function togglePlugin(name, action) {
    addLog(`Solicitando ${action} para plugin ${name}...`, 'info');
    try {
        const res = await fetch('/api/plugins/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, action})
        });
        const data = await res.json();
        if(data.success) {
            addLog(`Ejecución exitosa: ${action} en ${name}`, 'success');
        } else {
            addLog(`Fallo al ejecutar ${action} en ${name}`, 'error');
        }
        fetchStatus();
    } catch(e) {
        addLog(`Error de red al alternar ${name}`, 'error');
    }
}

// Bucle de Polling
setInterval(() => {
    fetchStatus();
    fetchWeight();
}, 1000);

// Carga Inicial
addLog('Interfaz UI Iniciada. Consultando al backend...', 'success');
fetchStatus();
