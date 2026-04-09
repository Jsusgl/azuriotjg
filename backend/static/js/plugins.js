function addLog(message, type="info") {
    const viewer = document.getElementById('log-viewer');
    const p = document.createElement('p');
    p.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString();
    p.textContent = `[${time}] ${message}`;
    viewer.appendChild(p);
    viewer.scrollTop = viewer.scrollHeight;
}

async function renderPlugins() {
    try {
        const res = await fetch('/api/plugins');
        const plugins = await res.json();
        
        const grid = document.getElementById('plugins-grid');
        grid.innerHTML = '';
        
        plugins.forEach(p => {
            const status = (p.status_detail && p.status_detail.status) ? p.status_detail.status : p.state;
            const badgeClass = status === 'active' || status === 'ok' ? 'active' : 'offline';
            
            const card = document.createElement('div');
            card.className = 'glass-card plugin-card';
            card.innerHTML = `
                <h2>${p.name} <span class="badge ${badgeClass}">${status}</span></h2>
                <div class="card-content" style="min-height: 80px;">
                    <p style="color: var(--text-secondary)">Plugin del sistema</p>
                </div>
                <div class="card-actions">
                    <button class="btn btn-toggle" onclick="togglePlugin('${p.name}', 'stop')">Detener</button>
                    <button class="btn btn-toggle active" onclick="togglePlugin('${p.name}', 'start')">Iniciar</button>
                </div>
            `;
            grid.appendChild(card);
        });
        
    } catch (e) {
        // Silently fail
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
        renderPlugins();
    } catch(e) {
        addLog(`Error de red al alternar ${name}`, 'error');
    }
}

setInterval(renderPlugins, 2000);
renderPlugins();
