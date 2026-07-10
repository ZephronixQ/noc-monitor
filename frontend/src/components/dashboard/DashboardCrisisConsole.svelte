<!-- frontend\src\components\DashboardCrisisConsole.svelte -->
<script>
  import { fade } from 'svelte/transition';
  import { data } from '../../stores/networkStore.js';
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0, massOlt: 0, massSw: 0 };

  const currentUnixTime = Math.floor(Date.now() / 1000);

  $: activeIncidents = (() => {
    let list = [];
    const rawData = $data || [];

    const swNode = rawData.find(d => d && d.isSwitch);
    if (swNode && swNode.ports) {
      swNode.ports.forEach(folder => {
        if (folder && folder.onus) {
          folder.onus.forEach(sw => {
            if (sw) {
              const state = (sw.state || '').trim().toLowerCase();
              if (state !== 'working' && state !== 'host is alive') {
                list.push({
                  type: 'sw',
                  id: sw.id || '',
                  contract: sw.contract || '—',
                  state: sw.state || 'DOWN',
                  los_time: sw.los_time,
                  location: folder.name || 'Общая'
                });
              }
            }
          });
        }
      });
    }

    const olts = rawData.filter(d => d && !d.isSwitch);
    olts.forEach(olt => {
      if (olt && olt.ports) {
        olt.ports.forEach(port => {
          if (port && port.onus) {
            port.onus.forEach(onu => {
              if (onu) {
                const state = (onu.state || '').trim().toLowerCase();
                if (['los', 'down'].includes(state)) {
                  list.push({
                    type: 'onu',
                    id: onu.id || '', 
                    contract: onu.contract || '—',
                    state: onu.state || 'DOWN',
                    los_time: onu.los_time,
                    oltIp: olt.ip || '',
                    portName: port.name || ''
                  });
                }
              }
            });
          }
        });
      }
    });

    list.sort((a, b) => {
      const timeA = a.los_time || 0;
      const timeB = b.los_time || 0;
      if (timeA === 0) return 1;
      if (timeB === 0) return -1;
      return timeA - timeB;
    });

    return list;
  })();

  $: groupedSwIncidents = (() => {
    let groups = {};
    const switches = activeIncidents.filter(i => i && i.type === 'sw');
    switches.forEach(item => {
      const loc = item.location || 'Общие узлы';
      if (!groups[loc]) groups[loc] = [];
      groups[loc].push(item);
    });
    return Object.entries(groups).map(([name, items]) => ({ name, items }));
  })();

  $: nestedGponIncidents = (() => {
    let oltsMap = {};
    const onus = activeIncidents.filter(i => i && i.type === 'onu');

    onus.forEach(item => {
      const olt = item.oltIp || 'Неизвестный OLT';
      const port = item.portName || 'Неизвестный порт';
      
      if (!oltsMap[olt]) oltsMap[olt] = {};
      if (!oltsMap[olt][port]) oltsMap[olt][port] = [];
      oltsMap[olt][port].push(item);
    });

    return Object.entries(oltsMap).map(([oltIp, portsMap]) => {
      const ports = Object.entries(portsMap).map(([portName, items]) => ({
        portName,
        items
      }));
      const totalCount = ports.reduce((sum, p) => sum + p.items.length, 0);
      return { oltIp, ports, totalCount };
    });
  })();

  $: anomalyStats = (() => {
    let los = 0; let losi = 0; let dying = 0; let offline = 0;
    const rawData = $data || [];

    rawData.forEach(d => {
      if (d && !d.isSwitch && d.ports) {
        d.ports.forEach(port => {
          if (port && port.onus) {
            port.onus.forEach(onu => {
              if (onu) {
                const state = (onu.state || '').trim().toLowerCase();
                if (state === 'dyinggasp') dying++;
                else if (state === 'offline') offline++;
                else if (state === 'losi') losi++;
                else if (['los', 'down'].includes(state)) los++;
              }
            });
          }
        });
      }
    });

    const total = los + losi + dying + offline;
    return { los, losi, dying, offline, total };
  })();

  // Модифицированный расчет очагов с выводом соотношения упавших к общему числу
  $: topBadLocations = (() => {
    let list = [];
    const rawData = $data || [];
    const swNode = rawData.find(d => d && d.isSwitch);
    if (swNode && swNode.ports) {
      swNode.ports.forEach(folder => {
        const total = folder.onus ? folder.onus.length : 0;
        const down = folder.onus ? folder.onus.filter(sw => {
          const state = (sw.state || '').trim().toLowerCase();
          return state !== 'working' && state !== 'host is alive';
        }).length : 0;

        if (down > 0) {
          list.push({
            name: folder.name || 'Общая',
            down: down,
            total: total
          });
        }
      });
    }
    return list.sort((a, b) => b.down - a.down);
  })();

  $: swIncidents = activeIncidents.filter(i => i && i.type === 'sw');
  $: gponLosIncidents = activeIncidents.filter(i => i && i.type === 'onu');
</script>

<div class="flex-1 min-h-0 grid grid-cols-10 gap-6">
    
  <!-- ЛЕВАЯ ПАНЕЛЬ -->
  <div class="col-span-7 p-6 rounded-[24px] border shadow-sm flex flex-col relative overflow-hidden
    {isDark ? 'bg-[#161f33] border-slate-800/80 shadow-[0_20px_40px_rgba(0,0,0,0.3)]' : 'bg-white border-slate-200/60 shadow-[0_4px_20px_rgba(0,0,0,0.01)]'}"
  >
    <div class="flex items-center justify-between mb-4 pb-2 border-b border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'} select-none shrink-0">
      <div class="flex items-center gap-2">
        <span class="relative flex h-2.5 w-2.5">
          {#if activeIncidents.length > 0}
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
          {:else}
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          {/if}
        </span>
        <span class="text-[11px] font-black uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-700'}">
          Консоль оперативного реагирования (Hierarchical Crisis Board)
        </span>
      </div>
      <span class="text-[9px] font-mono font-bold text-rose-500 animate-pulse">КРИТИЧЕСКИЕ АВАРИИ</span>
    </div>

    <div class="flex-1 grid grid-cols-2 gap-8 min-h-0">
      <div class="flex flex-col min-h-0 border-r border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'} pr-4">
        <div class="flex justify-between items-center mb-3 px-1 select-none shrink-0">
          <span class="text-[10px] font-black tracking-wider uppercase text-blue-500 dark:text-blue-400">🔌 Магистрали & Коммутаторы ({swIncidents.length})</span>
        </div>
        
        <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-4">
          {#if groupedSwIncidents.length === 0}
            <div class="h-full flex flex-col items-center justify-center text-center opacity-30 select-none py-10" in:fade>
              <div class="text-2xl mb-1">👍</div>
              <span class="text-[10px] font-bold {isDark ? 'text-slate-400' : 'text-slate-500'} uppercase tracking-wider">Все коммутаторы в сети</span>
            </div>
          {:else}
            {#each groupedSwIncidents as group}
              <div class="space-y-2">
                <div class="flex items-center justify-between py-1.5 px-3 rounded-lg border 
                  {isDark ? 'bg-slate-950/40 border-slate-800/40' : 'bg-slate-50 border-slate-200/80'} select-none"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-indigo-500 dark:text-indigo-400 font-extrabold text-[10px]">◆</span>
                    <span class="text-[10px] font-black uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-700'}">{group.name}</span>
                  </div>
                  <span class="text-[8px] font-bold text-rose-500 bg-rose-500/5 dark:text-rose-400 dark:bg-rose-50/10 border border-rose-500/10 dark:border-rose-50/15 px-1.5 py-0.5 rounded-full">
                    {group.items.length} DOWN
                  </span>
                </div>
                
                <div class="space-y-1.5 pl-3 border-l border-dashed {isDark ? 'border-white/[0.03]' : 'border-slate-200'}">
                  {#each group.items as item}
                    {@const swDescParts = item.contract ? item.contract.split('|') : []}
                    {@const swAddress = swDescParts[0] ? swDescParts[0].trim() : '—'}
                    {@const swDetail = swDescParts[1] ? swDescParts[1].trim() : ''}

                    <div class="p-2.5 rounded-xl border flex flex-col gap-1 transition-all
                      {isDark 
                        ? 'bg-[#121724]/40 border-slate-800/80 hover:border-slate-700 hover:bg-[#121724]/75' 
                        : 'bg-white border-slate-200/80 hover:border-slate-300/80 hover:bg-slate-50/40 shadow-[0_2px_8px_-3px_rgba(0,0,0,0.02)]'}"
                    >
                      <div class="flex justify-between items-center w-full">
                        <div class="flex items-center gap-2 min-w-0">
                          <span class="font-mono text-[10px] select-none {isDark ? 'text-slate-600' : 'text-slate-300'}">└──</span>
                          <div class="font-mono font-bold text-xs truncate {isDark ? 'text-slate-200' : 'text-slate-850'}">{(item.id || '')}</div>
                        </div>
                        
                        {#if item.los_time}
                          <span class="font-mono text-[9px] font-extrabold shrink-0 px-1.5 py-0.5 rounded border
                            {isDark 
                              ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' 
                              : 'text-rose-600 bg-rose-50 border-rose-200'}"
                          >
                            ⏱ {formatLosTime(item.los_time, currentUnixTime)}
                          </span>
                        {/if}
                      </div>
                      
                      <div class="pl-7 text-[10px] font-medium truncate w-full {isDark ? 'text-slate-400' : 'text-slate-500'}" title={swAddress}>
                        {swAddress}
                        {#if swDetail}
                          <span class="text-[9px] font-mono ml-1 {isDark ? 'text-slate-500' : 'text-slate-400'}">({swDetail})</span>
                        {/if}
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      <div class="flex flex-col min-h-0 pl-1">
        <div class="flex justify-between items-center mb-3 px-1 select-none shrink-0">
          <span class="text-[10px] font-black tracking-wider uppercase text-purple-600 dark:text-purple-400">✂️ Обрывы оптики GPON LOS ({gponLosIncidents.length})</span>
        </div>

        <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-5">
          {#if nestedGponIncidents.length === 0}
            <div class="h-full flex flex-col items-center justify-center text-center opacity-30 select-none py-10" in:fade>
              <div class="text-2xl mb-1">✨</div>
              <span class="text-[10px] font-bold {isDark ? 'text-slate-400' : 'text-slate-500'} uppercase tracking-wider">Обрывы оптики не зафиксированы</span>
            </div>
          {:else}
            {#each nestedGponIncidents as oltGroup}
              <div class="space-y-3">
                <div class="flex items-center justify-between py-1.5 px-3 rounded-lg border 
                  {isDark ? 'bg-slate-950/40 border-slate-800/40' : 'bg-slate-50 border-slate-200/80'} select-none"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-indigo-500 dark:text-indigo-400 font-extrabold text-[11px]">⚙ OLT:</span>
                    <span class="text-xs font-mono font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">{oltGroup.oltIp}</span>
                  </div>
                  <span class="text-[8px] font-bold text-rose-500 bg-rose-500/5 dark:text-rose-400 dark:bg-rose-50/10 border border-rose-500/10 dark:border-rose-50/15 px-2 py-0.5 rounded-full font-mono">
                    {oltGroup.totalCount} LOS
                  </span>
                </div>

                <div class="space-y-3 pl-3 border-l border-dashed {isDark ? 'border-white/[0.03]' : 'border-slate-200'}">
                  {#each oltGroup.ports as portGroup}
                    <div class="space-y-1.5">
                      <div class="text-[10px] font-bold font-mono pl-4 select-none flex items-center gap-1.5 {isDark ? 'text-indigo-400' : 'text-indigo-600'}">
                        <span>◆ Platа:</span> <span>{portGroup.portName}</span>
                      </div>

                      <div class="space-y-1.5 pl-4 border-l border-dashed {isDark ? 'border-white/[0.02]' : 'border-slate-200/60'}">
                        {#each portGroup.items as item}
                          {@const descParts = item.contract ? item.contract.split('|') : []}
                          {@const address = descParts[0] ? descParts[0].trim() : '—'}
                          
                          <div class="p-2.5 rounded-xl border flex flex-col gap-1 transition-all
                            {isDark 
                              ? 'bg-[#121724]/40 border-slate-800/80 hover:border-slate-700 hover:bg-[#121724]/75' 
                              : 'bg-white border-slate-200/80 hover:border-slate-300/80 hover:bg-slate-50/40 shadow-[0_2px_8px_-3px_rgba(0,0,0,0.02)]'}"
                          >
                            <div class="flex justify-between items-center w-full">
                              <div class="flex items-center gap-2 min-w-0">
                                <span class="font-mono text-[10px] select-none {isDark ? 'text-slate-600' : 'text-slate-300'}">└──</span>
                                <span class="font-mono font-bold text-xs {isDark ? 'text-indigo-400' : 'text-indigo-600'}">#{(item.id || '').split(':').pop()}</span>
                              </div>
                              
                              {#if item.los_time}
                                <span class="font-mono text-[9px] font-extrabold shrink-0 px-1.5 py-0.5 rounded border
                                  {isDark 
                                    ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' 
                                    : 'text-rose-600 bg-rose-50 border-rose-200'}"
                                >
                                  ⏱ {formatLosTime(item.los_time, currentUnixTime)}
                                </span>
                              {/if}
                            </div>
                            
                            <div class="pl-7 text-[10px] font-medium truncate w-full {isDark ? 'text-slate-400' : 'text-slate-500'}" title={address}>
                              {address}
                            </div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- ПРАВАЯ ПАНЕЛЬ -->
  <div class="col-span-3 p-6 rounded-[24px] border shadow-sm flex flex-col justify-between relative overflow-hidden
    {isDark ? 'bg-[#161f33] border-slate-800/80 shadow-[0_20px_40px_rgba(0,0,0,0.3)]' : 'bg-white border-slate-200/60 shadow-[0_4px_20px_rgba(0,0,0,0.01)]'}"
  >
    <div class="pb-2 border-b border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'} select-none shrink-0">
      <span class="text-[11px] font-black uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-700'}">Анализ аномалий</span>
    </div>

    <div class="flex-1 flex flex-col justify-between py-2.5 min-h-0 gap-4">
      
      <div class="space-y-2.5">
        <span class="text-[9px] font-black uppercase text-slate-400 tracking-wider block mb-1">Распределение по статусам:</span>
        
        <!-- LOS -->
        <div class="space-y-1">
          <div class="flex justify-between text-[10px] font-bold">
            <span class="{isDark ? 'text-rose-400' : 'text-rose-600'}">LOS (Обрыв сигнала)</span>
            <span class="font-mono {isDark ? 'text-slate-200' : 'text-slate-700'}">{anomalyStats?.los || 0} шт</span>
          </div>
          <div class="h-1.5 rounded-full bg-slate-200/35 dark:bg-slate-800 overflow-hidden">
            <div class="bg-rose-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.los / anomalyStats.total) * 100 : 0}%"></div>
          </div>
        </div>

        <!-- LOSi -->
        <div class="space-y-1">
          <div class="flex justify-between text-[10px] font-bold">
            <span class="{isDark ? 'text-fuchsia-400' : 'text-fuchsia-600'}">LOSi (Затухание/Изгиб)</span>
            <span class="font-mono {isDark ? 'text-slate-200' : 'text-slate-700'}">{anomalyStats?.losi || 0} шт</span>
          </div>
          <div class="h-1.5 rounded-full bg-slate-200/35 dark:bg-slate-800 overflow-hidden">
            <div class="bg-fuchsia-550 dark:bg-fuchsia-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.losi / anomalyStats.total) * 100 : 0}%"></div>
          </div>
        </div>

        <!-- DyingGasp -->
        <div class="space-y-1">
          <div class="flex justify-between text-[10px] font-bold">
            <span class="{isDark ? 'text-amber-500' : 'text-amber-600'}">DyingGasp (Отключение питания)</span>
            <span class="font-mono {isDark ? 'text-slate-200' : 'text-slate-700'}">{anomalyStats?.dying || 0} шт</span>
          </div>
          <div class="h-1.5 rounded-full bg-slate-200/35 dark:bg-slate-800 overflow-hidden">
            <div class="bg-amber-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.dying / anomalyStats.total) * 100 : 0}%"></div>
          </div>
        </div>

        <!-- Offline -->
        <div class="space-y-1">
          <div class="flex justify-between text-[10px] font-bold">
            <span class="{isDark ? 'text-slate-400' : 'text-slate-500'}">Offline (Плановое отключение)</span>
            <span class="font-mono {isDark ? 'text-slate-200' : 'text-slate-700'}">{anomalyStats?.offline || 0} шт</span>
          </div>
          <div class="h-1.5 rounded-full bg-slate-200/35 dark:bg-slate-800 overflow-hidden">
            <div class="bg-slate-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.offline / anomalyStats.total) * 100 : 0}%"></div>
          </div>
        </div>
      </div>

      <!-- Очаги падений -->
      <div class="border-t border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'} pt-2.5 select-none">
        <span class="text-[9px] font-black uppercase text-slate-400 tracking-wider block mb-2">Очаги падений в группах SW:</span>
        
        {#if topBadLocations.length === 0}
          <div class="text-[10px] font-bold text-center text-emerald-500 py-2.5 bg-emerald-500/5 rounded-xl border border-emerald-500/10">
            Локальных очагов аварий нет
          </div>
        {:else}
          <!-- ИСПРАВЛЕНО: Добавлен вертикальный скролл с максимальной высотой -->
          <div class="space-y-1 font-mono text-[10px] max-h-[140px] overflow-y-auto always-visible-scroll pr-1">
            {#each topBadLocations as loc}
              <div class="flex justify-between items-center p-1.5 rounded-lg border 
                {isDark ? 'bg-black/15 border-white/[0.02]' : 'bg-slate-50 border-slate-100'}"
              >
                <span class="font-sans font-bold truncate max-w-[130px] {isDark ? 'text-slate-300' : 'text-slate-700'}">{loc.name}</span>
                <!-- ИСПРАВЛЕНО: Пишется соотношение упавших к общему числу коммутаторов в локации -->
                <span class="px-2 py-0.5 rounded font-black border font-mono text-[9px]
                  {isDark 
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' 
                    : 'bg-rose-50 text-rose-600 border-rose-200'}"
                >
                  {loc.down}/{loc.total} DOWN
                </span>
              </div>
            {/each}
          </div>
        {/if}
      </div>

    </div>
  </div>

</div>