<!-- frontend\src\components\DashboardMetrics.svelte -->
<script>
  import { data } from '../../stores/networkStore.js';

  export let isDark = false;
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0, massOlt: 0, massSw: 0 };
  
  // Экспорт для сохранения полной совместимости с родительским компонентом
  export let dailyStats = { total_24h: 0, avg_repair_minutes: 0, active_now: 0 };

  // Реактивный расчет здоровья сети только для коммутаторов доступа (SW) с кэшированием
  let vendorCache = {};
  try {
    vendorCache = JSON.parse(localStorage.getItem('noc_sw_vendor_cache') || '{}');
  } catch (e) {
    console.warn('Не удалось загрузить кэш вендоров:', e);
  }

  function updateCache(ip, vendor) {
    if (vendorCache[ip] !== vendor) {
      vendorCache[ip] = vendor;
      try {
        localStorage.setItem('noc_sw_vendor_cache', JSON.stringify(vendorCache));
      } catch (e) {
        console.warn('Не удалось сохранить кэш вендоров:', e);
      }
    }
  }

  $: hardwareStats = (() => {
    let stats = {
      zte: { name: 'ZTE', total: 0, down: 0 },
      eltex: { name: 'Eltex', total: 0, down: 0 },
      snr: { name: 'SNR', total: 0, down: 0 },
      dlink: { name: 'D-Link', total: 0, down: 0 }
    };

    const rawData = $data || [];

    rawData.forEach(node => {
      if (node && node.isSwitch && node.ports) {
        node.ports.forEach(folder => {
          if (folder && folder.onus) {
            folder.onus.forEach(sw => {
              if (sw) {
                const desc = (sw.contract || '').toLowerCase();
                const swId = (sw.id || '').toLowerCase();
                
                let vendor = null;
                if (desc.includes('eltex') || desc.includes('mes') || swId.includes('eltex')) {
                  vendor = 'eltex';
                } else if (desc.includes('snr') || desc.includes('s29') || swId.includes('snr')) {
                  vendor = 'snr';
                } else if (desc.includes('d-link') || desc.includes('dlink') || desc.includes('des-') || desc.includes('dgs-') || swId.includes('dlink')) {
                  vendor = 'dlink';
                } else if (desc.includes('zte') || swId.includes('zte') || desc.includes('zxr10')) {
                  vendor = 'zte';
                }

                if (vendor) {
                  updateCache(sw.id, vendor);
                } else {
                  vendor = vendorCache[sw.id] || null;
                }

                if (vendor && stats[vendor]) {
                  stats[vendor].total++;
                  const state = (sw.state || '').trim().toLowerCase();
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

    return Object.values(stats)
      .filter(v => v.total > 0)
      .sort((a, b) => b.down - a.down || b.total - a.total);
  })();

  // Расчет кругов здоровья
  $: onusCount = totalStats?.onus || 0;
  $: onlineCount = totalStats?.online || 0;
  $: switchesCount = totalStats?.switches || 0;
  $: swUpCount = totalStats?.swUp || 0;

  $: gponHealth = onusCount > 0 ? (onlineCount / onusCount) * 100 : 100;
  $: swHealth = switchesCount > 0 ? (swUpCount / switchesCount) * 100 : 100;

  const strokeDashArray = 226.19;
  $: gponOffset = strokeDashArray - (gponHealth / 100) * strokeDashArray;
  $: swOffset = strokeDashArray - (swHealth / 100) * strokeDashArray;
</script>

<div class="grid grid-cols-4 gap-6 h-40 shrink-0 select-none">
  
  <!-- Карточка 1: Клиенты -->
  <div class="relative p-5 rounded-[24px] overflow-hidden flex items-center justify-between group transition-all duration-300 hover:translate-y-[-2px] border
    {isDark 
      ? 'bg-[#161f33] border-slate-800/80 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.25)]' 
      : 'bg-white border-slate-200/60 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.02)]'}"
  >
    <div class="flex flex-col justify-between h-full flex-1">
      <span class="text-[10px] font-bold text-slate-400 dark:text-slate-400 uppercase tracking-widest">Клиенты (GPON)</span>
      <div>
        <div class="flex items-baseline gap-1.5 leading-none">
          <span class="text-3xl font-black tracking-tight {isDark ? 'text-white' : 'text-slate-900'}">{totalStats?.online || 0}</span>
          <span class="text-xs font-semibold text-slate-400">/ {totalStats?.onus || 0}</span>
        </div>
        <div class="text-[10px] font-semibold text-slate-400 mt-1">Активных ONU в сети</div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-[10px] font-bold text-rose-500 flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.7)]"></span>
          {totalStats?.los || 0} LOS
        </span>
        <span class="text-[10px] font-bold text-fuchsia-500 flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-fuchsia-500 shadow-[0_0_8px_rgba(217,70,239,0.7)]"></span>
          {totalStats?.losi || 0} LOSi
        </span>
      </div>
    </div>

    <!-- Встроенное кольцо GPON Health -->
    <div class="relative w-[76px] h-[76px] shrink-0 ml-3">
      <svg class="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" stroke={isDark ? "rgba(255,255,255,0.03)" : "rgba(15,23,42,0.04)"} stroke-width="7" fill="none" />
        <circle cx="40" cy="40" r="36" stroke="url(#gponCardRingGrad)" stroke-width="7" fill="none"
          stroke-dasharray={strokeDashArray} stroke-dashoffset={gponOffset} stroke-linecap="round"
          class="transition-all duration-500"
        />
        <defs>
          <linearGradient id="gponCardRingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#818cf8" />
            <stop offset="100%" stop-color="#34d399" />
          </linearGradient>
        </defs>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span class="font-mono font-black text-xs {isDark ? 'text-slate-100' : 'text-slate-900'}">{gponHealth.toFixed(1)}%</span>
        <span class="text-[7px] font-bold text-slate-400 mt-1 uppercase tracking-wider">HEALTH</span>
      </div>
    </div>
  </div>

  <!-- Карточка 2: Оборудование (SW) -->
  <div class="relative p-5 rounded-[24px] overflow-hidden flex items-center justify-between group transition-all duration-300 hover:translate-y-[-2px] border
    {isDark 
      ? 'bg-[#161f33] border-slate-800/80 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.25)]' 
      : 'bg-white border-slate-200/60 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.02)]'}"
  >
    <div class="flex flex-col justify-between h-full flex-1">
      <span class="text-[10px] font-bold text-slate-400 dark:text-slate-400 uppercase tracking-widest">Оборудование (SW)</span>
      <div>
        <div class="flex items-baseline gap-1.5 leading-none">
          <span class="text-3xl font-black tracking-tight {isDark ? 'text-white' : 'text-slate-900'}">{totalStats?.swUp || 0}</span>
          <span class="text-xs font-semibold text-slate-400">/ {totalStats?.switches || 0}</span>
        </div>
        <div class="text-[10px] font-semibold text-slate-400 mt-1">Коммутаторов в сети</div>
      </div>
      <div>
        <span class="text-[10px] font-bold px-2 py-0.5 rounded
          {((totalStats?.switches || 0) - (totalStats?.swUp || 0)) > 0 
            ? 'bg-rose-500/10 text-rose-500 border border-rose-500/15' 
            : 'bg-emerald-50 text-emerald-400 border border-emerald-500/15'}"
        >
          {((totalStats?.switches || 0) - (totalStats?.swUp || 0))} DOWN
        </span>
      </div>
    </div>

    <!-- Встроенное кольцо SW Health -->
    <div class="relative w-[76px] h-[76px] shrink-0 ml-3">
      <svg class="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" stroke={isDark ? "rgba(255,255,255,0.03)" : "rgba(15,23,42,0.04)"} stroke-width="7" fill="none" />
        <circle cx="40" cy="40" r="36" stroke="url(#swCardRingGrad)" stroke-width="7" fill="none"
          stroke-dasharray={strokeDashArray} stroke-dashoffset={swOffset} stroke-linecap="round"
          class="transition-all duration-500"
        />
        <defs>
          <linearGradient id="swCardRingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#3b82f6" />
            <stop offset="100%" stop-color="#06b6d4" />
          </linearGradient>
        </defs>
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span class="font-mono font-black text-xs {isDark ? 'text-slate-100' : 'text-slate-900'}">{swHealth.toFixed(1)}%</span>
        <span class="text-[7px] font-bold text-slate-400 mt-1 uppercase tracking-wider">HEALTH</span>
      </div>
    </div>
  </div>

  <!-- Карточка 3: Статус локаций -->
  <div class="p-6 rounded-[24px] flex flex-col justify-between transition-all duration-300 hover:translate-y-[-2px] border
    {isDark 
      ? 'bg-[#161f33] border-slate-800/80 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.25)]' 
      : 'bg-white border-slate-200/60 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.02)]'}"
  >
    <span class="text-[10px] font-bold text-slate-400 dark:text-slate-400 uppercase tracking-widest">Статус локаций</span>
    
    <div class="space-y-2 mt-2">
      <div class="flex justify-between items-center py-1 border-b border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'}">
        <span class="text-xs font-medium {isDark ? 'text-slate-300' : 'text-slate-600'}">Массовые GPON:</span>
        <span class="text-[10px] font-extrabold px-2 py-0.5 rounded
          {totalStats?.massOlt > 0 
            ? 'bg-rose-500 text-white shadow-[0_0_12px_rgba(239,68,68,0.4)] animate-pulse' 
            : (isDark ? 'bg-slate-800 text-slate-300 border border-slate-700' : 'bg-slate-100 text-slate-500 border border-slate-200')}"
        >
          {totalStats?.massOlt || 0} ОЧАГОВ
        </span>
      </div>
      <div class="flex justify-between items-center py-1">
        <span class="text-xs font-medium {isDark ? 'text-slate-300' : 'text-slate-600'}">Массовые SW:</span>
        <span class="text-[10px] font-extrabold px-2 py-0.5 rounded
          {totalStats?.massSw > 0 
            ? 'bg-rose-500 text-white shadow-[0_0_12px_rgba(239,68,68,0.4)] animate-pulse' 
            : (isDark ? 'bg-slate-800 text-slate-300 border border-slate-700' : 'bg-slate-100 text-slate-500 border border-slate-200')}"
        >
          {totalStats?.massSw || 0} ЛОКАЦИЙ
        </span>
      </div>
    </div>
  </div>

  <!-- Карточка 4: Сводка по типам оборудования (Hardware Health - ультракомпактная) -->
  <div class="p-4 rounded-[24px] flex flex-col justify-between transition-all duration-300 hover:translate-y-[-2px] border
    {isDark 
      ? 'bg-[#161f33] border-slate-800/80 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.25)]' 
      : 'bg-white border-slate-200/60 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.02)]'}"
  >
    <span class="text-[10px] font-bold text-slate-400 dark:text-slate-400 uppercase tracking-widest block mb-1">
      Коммутаторы по вендорам
    </span>

    <div class="space-y-1 mt-1.5">
      {#each hardwareStats as vendor}
        <div class="flex items-center justify-between text-[11px] py-0.5">
          <span class="font-bold {isDark ? 'text-slate-300' : 'text-slate-700'}">
            {vendor.name}
          </span>
          <div class="flex items-center gap-1.5">
            <span class="text-[9px] font-semibold font-mono {isDark ? 'text-slate-400' : 'text-slate-500'}">
              всего: {vendor.total}
            </span>
            <span class="font-mono font-extrabold px-1.5 py-0.5 rounded text-[10px]
              {vendor.down > 0 
                ? (isDark ? 'bg-rose-500/10 text-rose-400 border border-rose-500/15' : 'bg-rose-50 text-rose-600 border border-rose-200') 
                : (isDark ? 'bg-emerald-500/10 text-emerald-400' : 'bg-emerald-50 text-emerald-700')}"
            >
              {vendor.down} сбой
            </span>
          </div>
        </div>
      {/each}
    </div>
  </div>

</div>