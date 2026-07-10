<script>
  import { slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  import { data } from '../../stores/networkStore.js'; 
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;
  export let selectedDay = 10;
  export let monthName = "";
  export let shiftFilter = 'night';
  export let switchIncidents = []; 
  export let gponHierarchy = [];   
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();

  let activeGponPortKey = null;
  let activeSwitchFolderKey = null;
  let expandedClusters = new Set();

  // Динамический маппинг IP -> Локация из БД $data
  $: swLocationMap = (() => {
    let map = new Map();
    const rawData = $data || [];
    const swNode = rawData.find(d => d.isSwitch);
    if (swNode && swNode.ports) {
      swNode.ports.forEach(folder => {
        if (folder.onus) {
          folder.onus.forEach(sw => {
            if (sw && sw.id) {
              map.set(sw.id, folder.name || 'Общие узлы');
            }
          });
        }
      });
    }
    return map;
  })();

  function clusterSwitches(events) {
    let groups = {};
    events.forEach(e => {
      if (!groups[e.id]) groups[e.id] = [];
      groups[e.id].push(e);
    });

    return Object.entries(groups).map(([id, list]) => {
      list.sort((a, b) => a.los_time - b.los_time);

      if (list.length === 1) {
        return { isCluster: false, ...list[0] };
      } else {
        const first = list[0];
        const last = list[list.length - 1];
        const totalDuration = list.reduce((sum, e) => sum + e.durationSec, 0);

        return {
          isCluster: true,
          id: first.id,
          contract: first.contract,
          type: 'sw',
          timeStart: first.timeStart,
          timeEnd: last.timeEnd,
          durationSec: totalDuration,
          state: first.state,
          los_time: first.los_time,
          location: swLocationMap.get(first.id) || 'Общие узлы',
          history: list.map(item => ({
            start: item.timeStart,
            end: item.timeEnd,
            duration: item.durationSec
          }))
        };
      }
    });
  }

  $: groupedSwitches = (() => {
    const clustered = clusterSwitches(switchIncidents);
    let groups = {};
    clustered.forEach(item => {
      const loc = swLocationMap.get(item.id) || 'Общие узлы';
      if (!groups[loc]) groups[loc] = [];
      groups[loc].push(item);
    });
    return Object.entries(groups).map(([folderName, items]) => ({
      folderName,
      items
    }));
  })();

  function toggleSwitchFolder(folderName) {
    activeSwitchFolderKey = activeSwitchFolderKey === folderName ? null : folderName;
  }

  function toggleGponPort(oltIp, portName) {
    const key = `${oltIp}-${portName}`;
    activeGponPortKey = activeGponPortKey === key ? null : key;
  }

  function toggleCluster(id) {
    if (expandedClusters.has(id)) {
      expandedClusters.delete(id);
    } else {
      expandedClusters.add(id);
    }
    expandedClusters = expandedClusters; 
  }

  // Реактивный подсчет общего числа аварий LOS на GPON (полностью исключая LOSi)
  $: gponLosCount = gponHierarchy.reduce((acc, o) => 
    acc + o.ports.reduce((sum, p) => 
      sum + (p.onus || []).filter(onu => (onu.state || '').trim().toLowerCase() !== 'losi').length, 
    0), 
  0);
</script>

<div class="flex-1 p-6 rounded-[24px] border shadow-sm flex flex-col overflow-hidden
  {isDark ? 'bg-[#161f33] border-slate-800/80 shadow-md' : 'bg-white border-slate-200/60 shadow-sm'}"
>
  <!-- Панель управления -->
  <div class="pb-3 border-b border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'} flex justify-between items-center select-none shrink-0 mb-4">
    <span class="text-[11px] font-black uppercase tracking-wider {isDark ? 'text-slate-300' : 'text-slate-700'}">
      Инциденты за: {selectedDay} {monthName}
    </span>
    
    <div class="flex items-center gap-1 p-1 rounded-full border transition-all duration-300 select-none
      {isDark ? 'bg-[#0d121f] border-slate-800/80 shadow-[inset_0_2px_6px_rgba(0,0,0,0.4)]' : 'bg-slate-100 border-slate-200/60 shadow-[inset_0_1px_3px_rgba(0,0,0,0.03)]'}"
    >
      <button on:click={() => { shiftFilter = 'night'; activeGponPortKey = null; activeSwitchFolderKey = null; }}
        class="px-4.5 py-1.5 rounded-full text-[9px] font-black uppercase tracking-wider transition-all duration-300
        {shiftFilter === 'night' 
          ? (isDark 
              ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-[0_2px_10px_rgba(99,102,241,0.35)]' 
              : 'bg-white text-indigo-650 border border-slate-200/40 shadow-[0_2px_8px_rgba(0,0,0,0.06)]') 
          : (isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800')}"
      >
        Ночь (17:00 - 09:00)
      </button>
      <button on:click={() => { shiftFilter = 'all'; activeGponPortKey = null; activeSwitchFolderKey = null; }}
        class="px-4.5 py-1.5 rounded-full text-[9px] font-black uppercase tracking-wider transition-all duration-300
        {shiftFilter === 'all' 
          ? (isDark 
              ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-[0_2px_10px_rgba(99,102,241,0.35)]' 
              : 'bg-white text-indigo-650 border border-slate-200/40 shadow-[0_2px_8px_rgba(0,0,0,0.06)]') 
          : (isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800')}"
      >
        Все за сутки
      </button>
    </div>
  </div>

  <!-- Две вертикальные колонки по 50% ширины -->
  <div class="flex-1 grid grid-cols-2 gap-6 min-h-0">
    
    <!-- Левая колонка: Коммутаторы -->
    <div class="flex flex-col min-h-0 border-r border-dashed {isDark ? 'border-slate-800/80' : 'border-slate-100'} pr-3">
      <h3 class="text-[10px] font-black tracking-wider uppercase text-blue-500 dark:text-blue-400 select-none px-1 mb-3 shrink-0">
        🔌 Сбои коммутаторов ({switchIncidents.length})
      </h3>
      
      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-3">
        {#if switchIncidents.length === 0}
          <div class="p-8 text-center rounded-2xl border border-dashed opacity-45 text-[10px] font-bold uppercase tracking-wider {isDark ? 'border-slate-800 text-slate-500' : 'border-slate-200 text-slate-400'}">
            Сбоев не найдено
          </div>
        {:else}
          {#each groupedSwitches as folder}
            {@const isFolderExpanded = activeSwitchFolderKey === folder.folderName}
            
            <div class="rounded-xl border overflow-hidden {isDark ? 'border-slate-800 bg-[#121724]/20' : 'border-slate-200 bg-white shadow-sm'}">
              <button on:click={() => toggleSwitchFolder(folder.folderName)}
                class="w-full flex justify-between items-center p-3 text-left font-mono text-[10px] font-bold select-none
                {isDark ? 'hover:bg-white/[0.02]' : 'hover:bg-slate-50'}"
              >
                <div class="flex items-center gap-1.5">
                  <span class="text-indigo-400">◆ Локация:</span>
                  <span class="{isDark ? 'text-slate-300' : 'text-slate-800'}">{folder.folderName}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-1.5 py-0.5 rounded text-[8px] bg-blue-500/10 text-blue-400 border border-blue-500/20">{folder.items.length} устр.</span>
                  <span class="text-slate-500 transition-transform duration-200 {isFolderExpanded ? 'rotate-90' : ''}">▶</span>
                </div>
              </button>

              <!-- ИСПРАВЛЕНО: Для темной темы применен глубокий сапфировый оттенок индиго bg-indigo-950/20 вместо черного -->
              {#if isFolderExpanded}
                <div transition:slide={{duration: 200}} class="border-t border-dashed {isDark ? 'border-slate-800' : 'border-slate-200'} p-2.5 space-y-2 {isDark ? 'bg-indigo-950/20' : 'bg-slate-50/50'}">
                  {#each folder.items as event}
                    <div class="p-3 rounded-xl border flex flex-col gap-2 transition-all duration-200
                      {isDark ? 'bg-[#121724]/40 border-slate-800/80 shadow-sm' : 'bg-white border-slate-200/80 shadow-sm'}"
                    >
                      <div class="flex items-center justify-between gap-4">
                        <div class="min-w-0">
                          <div class="flex items-center gap-1.5 mb-0.5 flex-wrap select-none">
                            <span class="font-mono font-extrabold text-[9px] px-1.5 py-0.5 rounded shadow-sm {isDark ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20' : 'bg-indigo-50 text-indigo-600 border border-indigo-100'}">
                              {event.id}
                            </span>
                            
                            {#if event.isCluster}
                              <button on:click|stopPropagation={() => toggleCluster(event.id)}
                                class="text-[8px] font-black bg-amber-500/10 text-amber-400 border border-amber-500/25 px-1.5 py-0.5 rounded uppercase font-mono animate-pulse hover:bg-amber-500/20"
                              >
                                ⚠️ Дребезг: {event.history.length} сбоев
                              </button>
                            {:else}
                              <span class="text-[8px] font-black bg-blue-500/10 text-blue-400 px-1 py-0.5 rounded uppercase font-mono">свитч</span>
                            {/if}
                          </div>
                          
                          <div class="text-[11px] font-bold leading-normal truncate {isDark ? 'text-slate-100' : 'text-slate-855'}" title={event.contract.split('|')[0].trim()}>
                            {event.contract.split('|')[0].trim()}
                          </div>
                        </div>

                        <div class="flex items-center gap-3 shrink-0 select-none">
                          <div class="text-right font-mono text-[9px] leading-tight">
                            <span class="text-slate-500 font-bold uppercase tracking-wider text-[7px] block">зарегистрирован</span>
                            <span class="text-rose-400 font-bold block">{event.timeStart}</span>
                            <span class="text-slate-400 block font-semibold text-[8px]">({event.timeEnd})</span>
                          </div>
                          <button on:click={() => dispatch('openHistory', { contract: event.contract, id: event.id, type: 'sw' })}
                            class="px-2.5 py-1 rounded-lg border text-[9px] font-bold font-mono transition-all duration-150 {isDark ? 'bg-slate-900 border-slate-800 text-indigo-400 hover:text-indigo-300 hover:border-slate-700' : 'bg-white border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
                          >
                            Логи
                          </button>
                        </div>
                      </div>

                      {#if event.isCluster && expandedClusters.has(event.id)}
                        <div transition:slide={{duration: 200}} class="mt-1 p-2 rounded-lg border border-dashed text-[9px] font-mono
                          {isDark ? 'bg-black/25 border-slate-800 text-slate-400' : 'bg-slate-50 border-slate-200 text-slate-600'}"
                        >
                          <span class="font-extrabold uppercase text-[7px] text-amber-500 block mb-1">Хронология падений за смену:</span>
                          <div class="space-y-1">
                            {#each event.history as item, idx}
                              <div class="flex justify-between border-b border-white/[0.01] last:border-0 py-0.5">
                                <span>Падение #{idx + 1}: <strong class="text-rose-400">{item.start} - {item.end}</strong></span>
                                <span class="font-bold text-slate-500">({formatLosTime(0, item.duration)})</span>
                              </div>
                            {/each}
                          </div>
                        </div>
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

    <!-- Правая колонка: GPON (LOS) -->
    <div class="flex flex-col min-h-0 pl-1">
      <h3 class="text-[10px] font-black tracking-wider uppercase text-purple-600 dark:text-purple-400 select-none px-1 mb-3 shrink-0">
        ✂️ Сбои оптики GPON LOS ({gponHierarchy.reduce((acc, o) => acc + o.ports.reduce((sum, p) => sum + p.onus.length, 0), 0)})
      </h3>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-3">
        {#if gponHierarchy.length === 0}
          <div class="p-8 text-center rounded-2xl border border-dashed opacity-45 text-[10px] font-bold uppercase tracking-wider {isDark ? 'border-slate-800 text-slate-500' : 'border-slate-200 text-slate-400'}">
            Обрывов оптики не найдено
          </div>
        {:else}
          {#each gponHierarchy as oltGroup}
            <div class="space-y-1.5">
              <!-- Уровень 1: OLT -->
              <div class="flex items-center gap-2 py-1 px-2.5 rounded-lg border select-none text-[9px]
                {isDark ? 'bg-slate-950/40 border-slate-800/40' : 'bg-slate-50 border-slate-200/80'}"
              >
                <span class="text-indigo-500 dark:text-indigo-400 font-extrabold text-[10px]">⚙ OLT:</span>
                <span class="font-mono font-bold {isDark ? 'text-slate-200' : 'text-slate-855'}">{oltGroup.oltIp}</span>
              </div>

              <!-- Уровень 2: Порты -->
              <div class="space-y-1.5 pl-2.5 border-l border-dashed {isDark ? 'border-white/[0.03]' : 'border-slate-200'}">
                {#each oltGroup.ports as port}
                  <!-- Локальная реактивная дедупликация и фильтрация LOSi на уровне рендеринга -->
                  {@const rawOnus = (port.onus || []).filter(onu => (onu.state || '').trim().toLowerCase() !== 'losi')}
                  {@const activeOnus = rawOnus.filter((onu, index, self) =>
                    index === self.findIndex(t => t.id === onu.id && t.timeStart === onu.timeStart)
                  )}
                  {@const isExpanded = activeGponPortKey === `${oltGroup.oltIp}-${port.portName}`}
                  
                  {#if activeOnus.length > 0}
                    <div class="rounded-xl border overflow-hidden {isDark ? 'border-slate-800 bg-[#121724]/20' : 'border-slate-200 bg-white shadow-sm'}">
                      <button on:click={() => toggleGponPort(oltGroup.oltIp, port.portName)}
                        class="w-full flex justify-between items-center p-2.5 text-left font-mono text-[9px] font-bold select-none
                        {isDark ? 'hover:bg-white/[0.02]' : 'hover:bg-slate-50'}"
                      >
                        <div class="flex items-center gap-1.5">
                          <!-- ИСПРАВЛЕНО: Опечатка text-indigo-555 заменена на валидный адаптивный класс цвета -->
                          <span class="{isDark ? 'text-indigo-400' : 'text-indigo-600'} font-bold">◆ Platа:</span>
                          <!-- ИСПРАВЛЕНО: Ошибка text-slate-350 заменена на валидный класс цвета высокого контраста -->
                          <span class="{isDark ? 'text-slate-200' : 'text-slate-900'}">{port.portName}</span>
                        </div>
                        <div class="flex items-center gap-1.5">
                          <span class="px-1 py-0.5 rounded text-[7px] bg-rose-500/10 text-rose-400 border border-rose-500/20">{activeOnus.length} LOS</span>
                          <span class="text-slate-500 transition-transform duration-200 {isExpanded ? 'rotate-90' : ''}">▶</span>
                        </div>
                      </button>

                      <!-- Уровень 3: Конечные договоры ONU -->
                      <!-- ИСПРАВЛЕНО: Для темной темы применен глубокий сапфировый оттенок индиго bg-indigo-950/20 вместо черного -->
                      {#if isExpanded}
                        <div transition:slide={{duration: 200}} class="border-t border-dashed {isDark ? 'border-slate-800' : 'border-slate-200'} p-2 space-y-1.5 {isDark ? 'bg-indigo-950/20' : 'bg-slate-50/50'}">
                          {#each activeOnus as onu}
                            <div class="p-2.5 rounded-xl border flex items-center justify-between gap-3
                              {isDark ? 'bg-[#121724]/40 border-slate-800/80 shadow-sm' : 'bg-white border-slate-200/80 shadow-sm'}"
                            >
                              <div class="min-w-0">
                                <div class="flex items-center gap-1.5 mb-0.5 flex-wrap select-none">
                                  <span class="font-mono font-bold text-[9px] text-indigo-400">#{onu.id}</span>
                                  <span class="text-[7px] font-black bg-rose-500/10 text-rose-400 px-1 py-0.5 rounded uppercase font-mono">{onu.state}</span>
                                </div>
                                <div class="text-[11px] font-bold leading-normal truncate {isDark ? 'text-slate-100' : 'text-slate-855'}" title={onu.contract.split('|')[0].trim()}>
                                  {onu.contract.split('|')[0].trim()}
                                </div>
                              </div>

                              <div class="flex items-center gap-3 shrink-0 select-none">
                                <div class="text-right font-mono text-[9px] leading-tight">
                                  <span class="text-rose-400 font-bold block">{onu.timeStart}</span>
                                  <span class="text-slate-400 block text-[8px]">({onu.timeEnd})</span>
                                </div>
                                <button on:click={() => dispatch('openHistory', { contract: onu.contract, id: `${oltGroup.oltIp}:${port.portName}:${onu.id}`, type: 'onu' })}
                                  class="px-2 py-1 rounded-lg border text-[9px] font-bold font-mono transition-all duration-150 {isDark ? 'bg-slate-900 border-slate-800 text-indigo-400 hover:text-indigo-300 hover:border-slate-700' : 'bg-white border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
                                >
                                  Логи
                                </button>
                              </div>
                            </div>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/if}
                {/each}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>

  </div>
</div>