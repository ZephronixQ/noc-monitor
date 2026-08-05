<!-- frontend/src/components/dashboard/DashboardMetrics.svelte -->
<script>
  import { data } from '../../stores/networkStore.js';

  export let isDark = false;
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0, massOlt: 0, massSw: 0 };
  export let dailyStats = { total_24h: 0, avg_repair_minutes: 0, active_now: 0 };

  let vendorCache = {};
  if (typeof window !== 'undefined') {
    try {
      vendorCache = JSON.parse(localStorage.getItem('noc_sw_vendor_cache') || '{}');
    } catch (e) {}
  }

  function updateCache(ip, vendor) {
    if (!ip || !vendor) return;
    if (vendorCache[ip] !== vendor) {
      vendorCache[ip] = vendor;
      if (typeof window !== 'undefined') {
        try { localStorage.setItem('noc_sw_vendor_cache', JSON.stringify(vendorCache)); } catch(e){}
      }
    }
  }

  $: hardwareStats = (() => {
    let stats = {
      zte: { name: 'ZTE', total: 0, down: 0 },
      dlink: { name: 'D-Link', total: 0, down: 0 },
      eltex: { name: 'Eltex', total: 0, down: 0 },
      snr: { name: 'SNR', total: 0, down: 0 }
    };

    const rawData = Array.isArray($data) ? $data : [];

    rawData.forEach(node => {
      if (node && node.isSwitch && Array.isArray(node.ports)) {
        node.ports.forEach(folder => {
          if (folder && Array.isArray(folder.onus)) {
            folder.onus.forEach(sw => {
              if (sw && sw.id) {
                const desc = (sw.contract || '').toLowerCase();
                const swId = String(sw.id).toLowerCase();
                let vendor = null;

                if (desc.includes('eltex') || desc.includes('mes') || swId.includes('eltex')) vendor = 'eltex';
                else if (desc.includes('snr') || desc.includes('s29') || swId.includes('snr')) vendor = 'snr';
                else if (desc.includes('d-link') || desc.includes('dlink') || desc.includes('des-') || desc.includes('dgs-') || swId.includes('dlink')) vendor = 'dlink';
                else if (desc.includes('zte') || swId.includes('zte') || desc.includes('zxr10')) vendor = 'zte';

                if (vendor) {
                  updateCache(sw.id, vendor);
                } else {
                  vendor = vendorCache[sw.id] || null;
                }

                if (vendor && stats[vendor]) {
                  stats[vendor].total++;
                  const state = String(sw.state || '').trim().toLowerCase();
                  if (state !== 'working' && state !== 'host is alive') {
                    stats[vendor].down++;
                  }
                }
              }
            });
          }
        });
      }
    });

    return Object.values(stats).filter(v => v.total > 0).sort((a, b) => b.down - a.down);
  })();

  $: onusCount = totalStats?.onus || 0;
  $: onlineCount = totalStats?.online || 0;
  $: switchesCount = totalStats?.switches || 0;
  $: swUpCount = totalStats?.swUp || 0;

  $: gponHealth = onusCount > 0 ? (onlineCount / onusCount) * 100 : 100;
  $: swHealth = switchesCount > 0 ? (swUpCount / switchesCount) * 100 : 100;

  $: offlineOlts = (Array.isArray($data) ? $data : []).filter(d => d && !d.isSwitch && (!d.ports || d.ports.length === 0 || d.ports.every(p => !p.onus || p.onus.length === 0)));

  const strokeDashArray = 226.19;
  $: gponOffset = strokeDashArray - (gponHealth / 100) * strokeDashArray;
  $: swOffset = strokeDashArray - (swHealth / 100) * strokeDashArray;
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-auto select-none shrink-0 font-sans">
  
  <!-- 1. КЛИЕНТЫ GPON -->
  <div class="p-4 rounded-xl border flex items-center justify-between transition-colors shadow-xs relative overflow-hidden
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    <div class="flex flex-col justify-between h-full flex-1 min-w-0 pr-2">
      <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-500'}">Клиенты (GPON)</span>
      <div class="my-1.5">
        <div class="flex items-baseline gap-1.5 leading-none">
          <span class="text-3xl font-extrabold font-mono tracking-tight {isDark ? 'text-slate-50' : 'text-slate-900'}">{onlineCount}</span>
          <span class="text-xs font-mono font-bold {isDark ? 'text-slate-300' : 'text-slate-600'}">/ {onusCount}</span>
        </div>
        <div class="text-[11px] font-semibold mt-1 {isDark ? 'text-slate-300' : 'text-slate-700'}">Активных ONU в сети</div>
      </div>
      <div class="flex items-center gap-3 font-mono text-[10px] font-bold">
        <span class="text-rose-500 flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>{totalStats?.los || 0} LOS</span>
        <span class="text-fuchsia-400 flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-fuchsia-400"></span>{totalStats?.losi || 0} LOSi</span>
      </div>
    </div>

    <div class="relative w-18 h-18 shrink-0 flex items-center justify-center">
      <svg class="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" stroke={isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)"} stroke-width="7" fill="none" />
        <circle cx="40" cy="40" r="36" stroke="url(#gponRing)" stroke-width="7" fill="none"
          stroke-dasharray={strokeDashArray} stroke-dashoffset={gponOffset} stroke-linecap="round" class="transition-all duration-500"
        />
        <defs>
          <linearGradient id="gponRing" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#818cf8" />
            <stop offset="100%" stop-color="#34d399" />
          </linearGradient>
        </defs>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center leading-none font-mono">
        <span class="font-extrabold text-xs {isDark ? 'text-slate-100' : 'text-slate-900'}">{gponHealth.toFixed(1)}%</span>
        <span class="text-[8px] font-bold mt-1 uppercase tracking-tighter {isDark ? 'text-slate-400' : 'text-slate-500'}">HEALTH</span>
      </div>
    </div>
  </div>

  <!-- 2. ОБОРУДОВАНИЕ SW -->
  <div class="p-4 rounded-xl border flex items-center justify-between transition-colors shadow-xs relative overflow-hidden
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    <div class="flex flex-col justify-between h-full flex-1 min-w-0 pr-2">
      <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-500'}">Оборудование (SW)</span>
      <div class="my-1.5">
        <div class="flex items-baseline gap-1.5 leading-none">
          <span class="text-3xl font-extrabold font-mono tracking-tight {isDark ? 'text-slate-50' : 'text-slate-900'}">{swUpCount}</span>
          <span class="text-xs font-mono font-bold {isDark ? 'text-slate-300' : 'text-slate-600'}">/ {switchesCount}</span>
        </div>
        <div class="text-[11px] font-semibold mt-1 {isDark ? 'text-slate-300' : 'text-slate-700'}">Коммутаторов в сети</div>
      </div>
      <div>
        <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border
          {(switchesCount - swUpCount) > 0 ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'}"
        >
          {(switchesCount - swUpCount)} DOWN
        </span>
      </div>
    </div>

    <div class="relative w-18 h-18 shrink-0 flex items-center justify-center">
      <svg class="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" stroke={isDark ? "rgba(255,255,255,0.08)" : "rgba(15,23,42,0.08)"} stroke-width="7" fill="none" />
        <circle cx="40" cy="40" r="36" stroke="url(#swRing)" stroke-width="7" fill="none"
          stroke-dasharray={strokeDashArray} stroke-dashoffset={swOffset} stroke-linecap="round" class="transition-all duration-500"
        />
        <defs>
          <linearGradient id="swRing" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#3b82f6" />
            <stop offset="100%" stop-color="#06b6d4" />
          </linearGradient>
        </defs>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center leading-none font-mono">
        <span class="font-extrabold text-xs {isDark ? 'text-slate-100' : 'text-slate-900'}">{swHealth.toFixed(1)}%</span>
        <span class="text-[8px] font-bold mt-1 uppercase tracking-tighter {isDark ? 'text-slate-400' : 'text-slate-500'}">HEALTH</span>
      </div>
    </div>
  </div>

  <!-- 3. СТАТУС СТАНЦИЙ & ЛОКАЦИЙ -->
  <div class="p-4 rounded-xl border flex flex-col justify-between transition-colors shadow-xs
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-500'}">Статус Станций & Локаций</span>
    
    <div class="space-y-2 font-mono text-xs my-auto">
      <div class="flex justify-between items-center pb-1.5 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'}">
        <span class="font-semibold {isDark ? 'text-slate-200' : 'text-slate-800'}">Падения OLT:</span>
        <span class="font-bold px-2 py-0.5 rounded-md text-[10px] border
          {offlineOlts.length > 0 ? 'bg-rose-500 text-white border-rose-600 animate-pulse' : (isDark ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-50 text-emerald-600 border-emerald-200')}"
        >
          {offlineOlts.length > 0 ? `${offlineOlts.length} ОФФЛАЙН` : '0 ОФФЛАЙН'}
        </span>
      </div>

      <div class="flex justify-between items-center pb-1.5 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'}">
        <span class="font-semibold {isDark ? 'text-slate-200' : 'text-slate-800'}">Массовые GPON:</span>
        <span class="font-bold px-2 py-0.5 rounded-md text-[10px] border
          {totalStats?.massOlt > 0 ? 'bg-rose-500 text-white border-rose-600 animate-pulse' : (isDark ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-50 text-emerald-600 border-emerald-200')}"
        >
          {totalStats?.massOlt || 0} ОЧАГОВ
        </span>
      </div>

      <div class="flex justify-between items-center">
        <span class="font-semibold {isDark ? 'text-slate-200' : 'text-slate-800'}">Массовые SW:</span>
        <span class="font-bold px-2 py-0.5 rounded-md text-[10px] border
          {totalStats?.massSw > 0 ? 'bg-rose-500 text-white border-rose-600 animate-pulse' : (isDark ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-50 text-emerald-600 border-emerald-200')}"
        >
          {totalStats?.massSw || 0} ЛОКАЦИЙ
        </span>
      </div>
    </div>
  </div>

  <!-- 4. СВОДКА ПО ВЕНДОРАМ -->
  <div class="p-4 rounded-xl border flex flex-col justify-between transition-colors shadow-xs
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    <span class="text-[11px] font-mono font-bold uppercase tracking-wider block mb-1 {isDark ? 'text-slate-300' : 'text-slate-500'}">
      Вендоры Коммутаторов
    </span>

    <div class="space-y-1.5 font-mono text-xs my-auto">
      {#each hardwareStats as v}
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold {isDark ? 'text-slate-100' : 'text-slate-900'}">{v.name}</span>
          <div class="flex items-center gap-2">
            <span class="text-[11px] font-semibold {isDark ? 'text-slate-300' : 'text-slate-600'}">всего: {v.total}</span>
            <span class="font-bold px-1.5 py-0.5 rounded-md text-[10px] border min-w-[52px] text-center
              {v.down > 0 ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : (isDark ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-50 text-emerald-600 border-emerald-200')}"
            >
              {v.down} сбой
            </span>
          </div>
        </div>
      {/each}
    </div>
  </div>

</div>