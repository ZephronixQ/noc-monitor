// frontend/src/stores/networkStore.js
import { writable, derived, get } from 'svelte/store';
import { analyzeDataChanges } from './notificationStore.js';

// Загрузка последнего сохраненного состояния сети из кэша для мгновенного старта (0 секунд задержки)
let initialNetworkData = [];
if (typeof window !== 'undefined') {
  try {
    const saved = localStorage.getItem('noc_cached_network_data');
    if (saved) {
      initialNetworkData = JSON.parse(saved);
    }
  } catch (e) {
    console.error("Ошибка загрузки кэша сети:", e);
  }
}

export const data = writable(initialNetworkData);
export const dailyStats = writable({ total_24h: 0, avg_repair_minutes: 0, active_now: 0 });
export const wsConnected = writable(false);
export const isUpdating = writable(true);
export const timeToNextUpdate = writable("00:00");

export const isPollingActive = writable(false);
export const pollingProgress = writable(0);
export const pollingStatusText = writable('');
export const pollingDetectedStats = writable({ los: 0, losi: 0 });

let nextUpdateTs = 0;
let progressInterval = null;

export let BACKEND_URL = "";
export let WS_URL = "";

if (typeof window !== 'undefined') {
  const isDev = window.location.port === "5173";
  const backendPort = isDev ? "8000" : (window.location.port || (window.location.protocol === 'https:' ? '443' : '80'));
  const backendHost = `${window.location.hostname}:${backendPort}`;

  BACKEND_URL = `${window.location.protocol}//${backendHost}`;
  WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${backendHost}/ws`;
}

// Реактивная статистика
export const totalStats = derived(data, ($data) => {
  const olts = $data.filter(d => d && !d.isSwitch);
  const switchDataNode = $data.find(d => d && d.isSwitch) || { ports: [] };
  const switchFolders = switchDataNode.ports || [];
  const allSwitchesFlat = switchFolders.flatMap(folder => folder.onus || []);

  return {
    onus: olts.reduce((acc, olt) => acc + (olt.ports ? olt.ports.flatMap(p => p.onus || []).length : 0), 0),
    online: olts.reduce((acc, olt) => acc + (olt.ports ? olt.ports.flatMap(p => p.onus || []).filter(o => (o.state||'').trim().toLowerCase() === 'working').length : 0), 0),
    los: olts.reduce((acc, olt) => acc + (olt.ports ? olt.ports.flatMap(p => p.onus || []).filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length : 0), 0),
    losi: olts.reduce((acc, olt) => acc + (olt.ports ? olt.ports.flatMap(p => p.onus || []).filter(o => (o.state||'').trim().toLowerCase() === 'losi').length : 0), 0),
    olts: olts.length,
    switches: allSwitchesFlat.length,
    swUp: allSwitchesFlat.filter(sw => (sw.state||'').trim().toLowerCase() === 'working' || (sw.state||'').trim().toLowerCase() === 'host is alive').length,
    massOlt: olts.reduce((acc, olt) => acc + (olt.ports ? olt.ports.filter(p => p.is_mass_outage).length : 0), 0),
    massSw: switchFolders.filter(f => f.is_mass_outage).length
  };
});

export function updateTimer() {
  if (!nextUpdateTs) return;
  const diff = nextUpdateTs - Math.floor(Date.now() / 1000);
  timeToNextUpdate.set(diff <= 0 ? "00:00" : `${Math.floor(diff/60)}:${(diff%60).toString().padStart(2,'0')}`);
}

export async function fetchInitialData() {
  try {
    const token = localStorage.getItem('noc_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    
    const res = await fetch(`${BACKEND_URL}/api/data`, { headers });
    if (res.ok) {
      const json = await res.json();
      if (json.data && json.data.length > 0) {
        data.set(json.data);
        localStorage.setItem('noc_cached_network_data', JSON.stringify(json.data));
      }
      if (json.next_update) {
        nextUpdateTs = json.next_update;
        updateTimer();
      }
      isUpdating.set(json.is_updating);
    }
  } catch(e) {
    console.error("Ошибка получения данных:", e);
  }
}

export async function fetchDailyStats() {
  try {
    const token = localStorage.getItem('noc_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

    const res = await fetch(`${BACKEND_URL}/api/stats/daily`, { headers });
    if (res.ok) {
      const json = await res.json();
      dailyStats.set({
        total_24h: json.total_24h ?? 0,
        avg_repair_minutes: json.avg_repair_minutes ?? 0,
        active_now: json.active_now ?? 0
      });
    }
  } catch(e) { 
    console.error("Ошибка отчета:", e); 
  }
}

export async function forceUpdate() {
  if (get(isPollingActive)) return;

  isPollingActive.set(true);
  pollingProgress.set(10);
  pollingStatusText.set('Парсинг OLT станций по Telnet...');
  
  const currentStats = get(totalStats);
  pollingDetectedStats.set({ los: currentStats.los, losi: currentStats.losi });

  if (progressInterval) clearInterval(progressInterval);
  progressInterval = setInterval(() => {
    pollingProgress.update(p => {
      if (p < 40) return p + 5;
      if (p < 75) return p + 2;
      if (p < 92) return p + 1;
      return p;
    });
  }, 800);

  try {
    isUpdating.set(true);
    const token = localStorage.getItem('noc_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

    await fetch(`${BACKEND_URL}/api/update/force`, { method: 'POST', headers });
  } catch (e) {
    console.error("Ошибка принудительного обновления:", e);
    pollingStatusText.set('Ошибка связи с сервером');
    if (progressInterval) clearInterval(progressInterval);
    setTimeout(() => isPollingActive.set(false), 2000);
  }
}

let ws;
export function connectWebSocket(onUpdateChart) {
  if (ws) ws.close();
  ws = new WebSocket(WS_URL);
  ws.onopen = () => { wsConnected.set(true); };
  
  ws.onmessage = async (e) => {
    const msg = JSON.parse(e.data);
    
    if (msg.type === "update") {
      if (msg.data && msg.data.length > 0) {
        analyzeDataChanges(msg.data); 
        data.set(msg.data); 
        localStorage.setItem('noc_cached_network_data', JSON.stringify(msg.data));
      }
      
      if (msg.next_update) {
        nextUpdateTs = msg.next_update;
        updateTimer();
      }
      
      isUpdating.set(msg.is_updating);
      
      if (!msg.is_sw_only && onUpdateChart) {
        onUpdateChart();
      }

      if (!msg.is_updating && !msg.is_sw_only && get(isPollingActive)) {
        if (progressInterval) clearInterval(progressInterval);
        
        const freshStats = get(totalStats);
        pollingDetectedStats.set({ los: freshStats.los, losi: freshStats.losi });
        
        pollingProgress.set(100);
        pollingStatusText.set('Опрос полностью завершен!');

        setTimeout(() => {
          isPollingActive.set(false);
          pollingProgress.set(0);
        }, 1500);
      }

    } else if (msg.type === "status") { 
      isUpdating.set(msg.is_updating);
    }
  };
  
  ws.onclose = () => {
    wsConnected.set(false); 
    setTimeout(() => connectWebSocket(onUpdateChart), 1000);
  };
  ws.onerror = () => { ws.close(); };
}