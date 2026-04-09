function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

async function fetchSystemInfo() {
    try {
        const res = await fetch('/api/system');
        const data = await res.json();
        
        // CPU
        document.getElementById('cpu-fill').style.width = `${data.cpu_percent}%`;
        document.getElementById('cpu-text').textContent = `${data.cpu_percent}%`;
        
        // RAM
        document.getElementById('ram-fill').style.width = `${data.memory.percent}%`;
        document.getElementById('ram-text').textContent = `${data.memory.percent}%`;
        document.getElementById('ram-detail').textContent = `${formatBytes(data.memory.used)} / ${formatBytes(data.memory.total)}`;
        
        // Disk
        document.getElementById('disk-fill').style.width = `${data.disk.percent}%`;
        document.getElementById('disk-text').textContent = `${data.disk.percent}%`;
        document.getElementById('disk-detail').textContent = `${formatBytes(data.disk.used)} / ${formatBytes(data.disk.total)}`;
        
        // Additional info
        const sysInfo = document.getElementById('sys-info');
        sysInfo.innerHTML = `
            <p><strong>Memoria Libre:</strong> ${formatBytes(data.memory.total - data.memory.used)}</p>
            <p><strong>Espacio Libre (Disco):</strong> ${formatBytes(data.disk.total - data.disk.used)}</p>
        `;
        
    } catch (e) {
        console.error("Error fetching system info:", e);
    }
}

setInterval(fetchSystemInfo, 2000);
fetchSystemInfo();
