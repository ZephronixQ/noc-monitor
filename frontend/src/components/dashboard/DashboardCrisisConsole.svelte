<!-- frontend/src/components/dashboard/DashboardCrisisConsole.svelte -->
<script>
  import { slide } from 'svelte/transition';
  import { data } from '../../stores/networkStore.js';
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;

  const currentUnixTime = Math.floor(Date.now() / 1000);

  let expandedGroupKey = null; 
  let expandedPortKey = null;  

  function toggleGroup(key) {
    expandedGroupKey = expandedGroupKey === key ? null : key;
  }

  function togglePort(key) {
    expandedPortKey = expandedPortKey === key ? null : key;
  }

  $: offlineOlts = ($data || []).filter(d => !d.isSwitch && (!d.ports || d.ports.length === 0 || d.ports.every(p => !p.onus || p.onus.length === 0)));

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

    list.sort((a, b) => (a.los_time || 0) - (b.los_time || 0));
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
</script>

<div class="col-span-7 p-5 rounded-2xl border shadow-xs flex flex-col relative overflow-hidden font-sans
  {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
>
  <div class="flex items-center justify-between pb-3 mb-3 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} select-none shrink-0">
    <div class="flex items-center gap-2">
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
      </span>
      <span class="text-[11px] font-semibold uppercase tracking-wider font-mono {isDark ? 'text-slate-300' : 'text-slate-700'}">
        Консоль оперативного реагирования (Hierarchical Crisis Board)
      </span>
    </div>
    <span class="text-[10px] font-mono font-semibold text-rose-500 animate-pulse uppercase tracking-wider">КРИТИЧЕСКИЕ АВАРИИ</span>
  </div>

  <!-- БАННЕР ПАДЕНИЯ OLT СТАНЦИЙ -->
  {#if offlineOlts.length > 0}
    <div class="mb-3 p-3 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-500 font-mono text-xs font-semibold flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm">⛔</span>
        <span>КРИТИЧЕСКАЯ АВАРИЯ: {offlineOlts.length} СТАНЦИЙ OLT В ОФФЛАЙНЕ</span>
      </div>
      <div class="flex gap-1.5">
        {#each offlineOlts as olt}
          <span class="px-2 py-0.5 rounded bg-rose-500 text-white font-mono font-bold text-[10px]">{olt.ip}</span>
        {/each}
      </div>
    </div>
  {/if}

  <div class="flex-1 grid grid-cols-2 gap-5 min-h-0">
    
    <!-- ЛЕВАЯ КОЛОНКА: СВИЧИ ПО ЛОКАЦИЯМ -->
    <div class="flex flex-col min-h-0 border-r border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} pr-3">
      <span class="text-[11px] font-semibold tracking-wider uppercase font-mono mb-2.5 block {isDark ? 'text-indigo-400' : 'text-indigo-600'}">
        🔌 Магистрали & Коммутаторы ({groupedSwIncidents.reduce((s, g) => s + g.items.length, 0)})
      </span>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
        {#if groupedSwIncidents.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs py-8 {isDark ? 'text-slate-400' : 'text-slate-500'}">
            <span>👍 Все коммутаторы работают штатно</span>
          </div>
        {:else}
          {#each groupedSwIncidents as group}
            {@const isExpanded = expandedGroupKey === group.name}
            
            <div class="rounded-xl border overflow-hidden transition-colors {isDark ? 'border-slate-700/60 bg-slate-800/60' : 'border-slate-200 bg-slate-50'}">
              <button on:click={() => toggleGroup(group.name)}
                class="w-full flex justify-between items-center p-2.5 text-left font-mono text-xs font-semibold select-none cursor-pointer
                {isDark ? 'hover:bg-slate-700/60 text-slate-100' : 'hover:bg-slate-100 text-slate-900'}"
              >
                <div class="flex items-center gap-2 min-w-0 pr-2">
                  <span class="text-indigo-400 shrink-0">◆</span>
                  <span class="truncate {isDark ? 'text-slate-100' : 'text-slate-900'}">{group.name}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded-md text-[10px] bg-rose-500/15 text-rose-400 border border-rose-500/30 font-semibold">{group.items.length} DOWN</span>
                  <svg class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200 {isExpanded ? 'rotate-180 text-indigo-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {#if isExpanded}
                <div transition:slide={{duration: 150}} class="p-2 space-y-1.5 border-t border-dashed {isDark ? 'border-slate-700/60 bg-slate-900/60' : 'border-slate-200 bg-white'}">
                  {#each group.items as item}
                    <div class="p-2.5 rounded-lg border flex justify-between items-center font-mono text-xs
                      {isDark ? 'bg-slate-800/80 border-slate-700/60 text-slate-100' : 'bg-slate-50 border-slate-200 text-slate-900'}"
                    >
                      <div class="min-w-0 pr-2">
                        <span class="font-bold text-[11px] block {isDark ? 'text-indigo-400' : 'text-indigo-600'}">{item.id}</span>
                        <div class="font-sans text-xs font-semibold truncate mt-0.5 {isDark ? 'text-slate-200' : 'text-slate-800'}">
                          {item.contract.split('|')[0].trim()}
                        </div>
                      </div>
                      {#if item.los_time}
                        <span class="px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-400 border border-rose-500/30 text-[10px] shrink-0 font-medium font-mono">
                          ⏱ {formatLosTime(item.los_time, currentUnixTime)}
                        </span>
                      {/if}
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        {/if}
      </div>
    </div>

    <!-- ПРАВАЯ КОЛОНКА: GPON ПЛАТЫ -->
    <div class="flex flex-col min-h-0">
      <span class="text-[11px] font-semibold tracking-wider uppercase font-mono mb-2.5 block {isDark ? 'text-purple-400' : 'text-purple-600'}">
        ✂️ Обрывы оптики GPON LOS ({nestedGponIncidents.reduce((s, o) => s + o.totalCount, 0)})
      </span>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
        {#if nestedGponIncidents.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs py-8 {isDark ? 'text-slate-400' : 'text-slate-500'}">
            <span>✨ Обрывов оптики не зафиксировано</span>
          </div>
        {:else}
          {#each nestedGponIncidents as oltGroup}
            <div class="space-y-1.5">
              <div class="text-[10px] font-semibold font-mono px-1 uppercase tracking-wide {isDark ? 'text-indigo-300' : 'text-indigo-700'}">⚙ OLT: {oltGroup.oltIp}</div>

              {#each oltGroup.ports as portGroup}
                {@const portKey = `${oltGroup.oltIp}-${portGroup.portName}`}
                {@const isExpanded = expandedPortKey === portKey}

                <div class="rounded-xl border overflow-hidden transition-colors {isDark ? 'border-slate-700/60 bg-slate-800/60' : 'border-slate-200 bg-slate-50'}">
                  <button on:click={() => togglePort(portKey)}
                    class="w-full flex justify-between items-center p-2.5 text-left font-mono text-xs font-semibold select-none cursor-pointer
                    {isDark ? 'hover:bg-slate-700/60 text-slate-100' : 'hover:bg-slate-100 text-slate-900'}"
                  >
                    <div class="flex items-center gap-1.5">
                      <span class="text-purple-400 font-normal">Plata:</span>
                      <span class="{isDark ? 'text-slate-100' : 'text-slate-900'}">{portGroup.portName}</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="px-2 py-0.5 rounded-md text-[10px] bg-rose-500/15 text-rose-400 border border-rose-500/30 font-semibold">{portGroup.items.length} LOS</span>
                      <svg class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200 {isExpanded ? 'rotate-180 text-purple-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {#if isExpanded}
                    <div transition:slide={{duration: 150}} class="p-2 space-y-1.5 border-t border-dashed {isDark ? 'border-slate-700/60 bg-slate-900/60' : 'border-slate-200 bg-white'}">
                      {#each portGroup.items as item}
                        <div class="p-2.5 rounded-lg border flex justify-between items-center font-mono text-xs
                          {isDark ? 'bg-slate-800/80 border-slate-700/60 text-slate-100' : 'bg-slate-50 border-slate-200 text-slate-900'}"
                        >
                          <div class="min-w-0 pr-2">
                            <span class="font-bold text-[11px] block {isDark ? 'text-indigo-400' : 'text-indigo-600'}">#{item.id.split(':').pop()}</span>
                            <div class="font-sans text-xs font-semibold truncate mt-0.5 {isDark ? 'text-slate-200' : 'text-slate-800'}">
                              {item.contract.split('|')[0].trim()}
                            </div>
                          </div>
                          {#if item.los_time}
                            <span class="px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-400 border border-rose-500/30 text-[10px] shrink-0 font-medium font-mono">
                              ⏱ {formatLosTime(item.los_time, currentUnixTime)}
                            </span>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {/each}
        {/if}
      </div>
    </div>

  </div>
</div>