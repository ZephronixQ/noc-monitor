export function formatLosTime(startTs, currentUnixTime) {
  if (!startTs) return '';
  const diff = currentUnixTime - startTs;
  if (diff < 0) return 'Только что';
  const h = Math.floor(diff / 3600);
  const m = Math.floor((diff % 3600) / 60);
  return h > 0 ? `${h}ч ${m}м` : `${m}м`;
}

export function getStatusColor(state) {
  if (!state) return 'text-slate-500';
  const s = state.trim().toLowerCase();
  if (s === 'working' || s === 'host is alive') return 'text-emerald-500';
  if (s === 'dyinggasp') return 'text-orange-500';
  if (s === 'losi') return 'text-fuchsia-500';
  return 'text-red-500';
}

export function getDotColor(state) {
  if (!state) return 'bg-slate-500';
  const s = state.trim().toLowerCase();
  if (s === 'working' || s === 'host is alive') return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
  if (s === 'dyinggasp') return 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]';
  if (s === 'losi') return 'bg-fuchsia-500 shadow-[0_0_8px_rgba(217,70,239,0.5)] animate-pulse';
  return 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)] animate-pulse';
}

export function exportPortCsv(port) {
  if (!port || !port.onus) return;
  let csvContent = "data:text/csv;charset=utf-8,";
  csvContent += "ID,Договор/Адрес,Статус\n";
  port.onus.forEach(onu => {
    const id = onu.id || '';
    const contract = onu.contract || '';
    const state = onu.state || '';
    csvContent += `"${id}","${contract}","${state}"\n`;
  });
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `export_port_${port.name}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}