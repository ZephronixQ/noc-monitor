import { writable, derived } from 'svelte/store';
import { analyzeDataChanges } from './notificationStore.js';

export const data = writable([]);
export const dailyStats = writable({ total_24h: 0, avg_repair_minutes: 0, active_now: 0 });
export const wsConnected = writable(false);
export const isUpdating = writable(true);
export const timeToNextUpdate = writable("00:00");

let nextUpdateTs = 0;

export let BACKEND_URL = "";
export let WS_URL = "";

if (typeof window !== 'undefined') {
  const isDev = window.location.port === "5173";
  const backendPort = isDev ? "8000" : (window.location.port || (window.location.protocol === 'https:' ? '443' : '80'));
  const backendHost = `${window.location.hostname}:${backendPort}`;

  BACKEND_URL = `${window.location.protocol}//${backendHost}`;
  WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${backendHost}/ws`;
}

// Автоматический реактивный подсчет общей статистики при изменении data
export const totalStats = derived(data, ($data) => {
  const olts = $data.filter(d => !d.isSwitch);
  const switchDataNode = $data.find(d => d.isSwitch) || { ports: [] };
  const switchFolders = switchDataNode.ports || [];
  const allSwitchesFlat = switchFolders.flatMap(folder => folder.onus || []);

  return {
    onus: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).length, 0),
    online: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => (o.state||'').trim().toLowerCase() === 'working').length, 0),
    los: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length, 0),
    losi: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => (o.state||'').trim().toLowerCase() === 'losi').length, 0),
    olts: olts.length,
    switches: allSwitchesFlat.length,
    swUp: allSwitchesFlat.filter(sw => (sw.state||'').trim().toLowerCase() === 'working' || (sw.state||'').trim().toLowerCase() === 'host is alive').length,
    massOlt: olts.reduce((acc, olt) => acc + olt.ports.filter(p => p.is_mass_outage).length, 0),
    massSw: switchFolders.filter(f => f.is_mass_outage).length
  };
});

export async function fetchInitialData() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/data`);
    if (res.ok) {
      const json = await res.json();
      data.set(json.data);
      nextUpdateTs = json.next_update;
      isUpdating.set(json.is_updating);
    }
  } catch(e) {
    console.error("Ошибка API данных:", e);
  }
}

export async function fetchDailyStats() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/stats/daily`);
    if (res.ok) {
      const json = await res.json();
      dailyStats.set({
        total_24h: json.total_24h ?? 0,
        avg_repair_minutes: json.avg_repair_minutes ?? 0,
        active_now: json.active_now ?? 0
      });
    }
  } catch(e) { 
    console.error("Ошибка загрузки отчета:", e); 
  }
}

export async function forceUpdate() {
  try {
    isUpdating.set(true);
    await fetch(`${BACKEND_URL}/api/update/force`, { method: 'POST' });
  } catch(e) { console.error("Ошибка принудительного обновления:", e); }
}

export function updateTimer() {
  if (!nextUpdateTs) return;
  const diff = nextUpdateTs - Math.floor(Date.now() / 1000);
  timeToNextUpdate.set(diff <= 0 ? "00:00" : `${Math.floor(diff/60)}:${(diff%60).toString().padStart(2,'0')}`);
}

let ws;
export function connectWebSocket(onUpdateChart) {
  if (ws) ws.close();
  ws = new WebSocket(WS_URL);
  ws.onopen = () => { wsConnected.set(true); };
  ws.onmessage = async (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "update") {
      analyzeDataChanges(msg.data); 
      data.set(msg.data); 
      nextUpdateTs = msg.next_update; 
      isUpdating.set(msg.is_updating);
      if (!msg.is_sw_only && onUpdateChart) {
        onUpdateChart();
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