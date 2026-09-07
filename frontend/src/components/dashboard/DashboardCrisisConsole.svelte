<!-- frontend/src/components/dashboard/DashboardCrisisConsole.svelte -->
<script>
  import { slide, fade } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { data } from '../../stores/networkStore.js';
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;

  const currentUnixTime = Math.floor(Date.now() / 1000);

  let activeTab = 'all'; // 'all' | 'sw' | 'gpon' | 'olt'
  let expandedGroupKey = null; 
  let expandedPortKey = null;
  let copiedText = null;

  function toggleGroup(key) {
    expandedGroupKey = expandedGroupKey === key ? null : key;
  }

  function togglePort(key) {
    expandedPortKey = expandedPortKey === key ? null : key;
  }

  function copy(val) {
    if (!val) return;
    navigator.clipboard.writeText(val);
    copiedText = val;
    setTimeout(() => { copiedText = null; }, 1400);
  }

  // 1. OLT OFFLINE
  $: offlineOlts = ($data || []).filter(d => !d.isSwitch && (!d.ports || d.ports.length === 0 || d.ports.every(p => !p.onus || p.onus.length === 0)));

  // 2. СБОР СЫРЫХ ДАННЫХ
  $: rawIncidents = (() => {
    let swList = [];
    let gponList = [];
    const raw = $data || [];

    // SW
    const swNode = raw.find(d => d && d.isSwitch);
    if (swNode?.ports) {
      swNode.ports.forEach(folder => {
        folder?.onus?.forEach(sw => {
          const st = (sw?.state || '').trim().toLowerCase();
          if (st !== 'working' && st !== 'host is alive') {
            swList.push({
              id: sw.id || 'SW-NODE',
              contract: sw.contract || '—',
              state: sw.state || 'DOWN',
              los_time: sw.los_time,
              location: folder.name || 'Общая'
            });
          }
        });
      });
    }

    // GPON
    raw.filter(d => !d.isSwitch).forEach(olt => {
      olt?.ports?.forEach(port => {
        port?.onus?.forEach(onu => {
          const st = (onu?.state || '').trim().toLowerCase();
          if (['los', 'down'].includes(st)) {
            gponList.push({
              id: onu.id || '',
              contract: onu.contract || '—',
              state: onu.state || 'DOWN',
              los_time: onu.los_time,
              oltIp: olt.ip || '',
              portName: port.name || ''
            });
          }
        });
      });
    });

    swList.sort((a, b) => (a.los_time || 0) - (b.los_time || 0));
    gponList.sort((a, b) => (a.los_time || 0) - (b.los_time || 0));

    return { swList, gponList };
  })();

  // Группировка SW по локациям/домам
  $: groupedSw = (() => {
    let groups = {};
    rawIncidents.swList.forEach(item => {
      const loc = item.location || 'Общие узлы';
      if (!groups[loc]) groups[loc] = [];
      groups[loc].push(item);
    });
    return Object.entries(groups).map(([name, items]) => ({ name, items }));
  })();

  // Группировка GPON по OLT и платам
  $: nestedGpon = (() => {
    let oltsMap = {};
    rawIncidents.gponList.forEach(item => {
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

  $: swCount = rawIncidents.swList.length;
  $: gponCount = rawIncidents.gponList.length;
  $: oltCount = offlineOlts.length;
  $: totalCount = swCount + gponCount + oltCount;
</script>

<div class="col-span-7 flex flex-col rounded-2xl border transition-all duration-300 relative isolate overflow-hidden h-full min-h-0
  {isDark 
    ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200 shadow-xl' 
    : 'bg-white border-slate-200/90 text-slate-800 shadow-sm'}"
>
  <!-- ШАПКА / ТАБЫ УПРАВЛЕНИЯ -->
  <div class="px-5 py-3.5 flex items-center justify-between gap-4 border-b {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'} select-none shrink-0">
    
    <!-- ТИТУЛ И ПУЛЬС-ИНДИКАТОР -->
    <div class="flex items-center gap-3">
      <div class="relative flex items-center justify-center w-7 h-7 rounded-xl transition-all duration-300
        {totalCount > 0 
          ? (isDark ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30' : 'bg-rose-100 text-rose-700 border border-rose-300') 
          : (isDark ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-100 text-emerald-700 border border-emerald-300')}">
        {#if totalCount > 0}
          <span class="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-rose-400 opacity-60"></span>
          <span class="relative inline-flex rounded-full h-1.5 w-1.5 {isDark ? 'bg-rose-500' : 'bg-rose-600'}"></span>
        {:else}
          <span class="relative inline-flex rounded-full h-1.5 w-1.5 {isDark ? 'bg-emerald-500' : 'bg-emerald-600'}"></span>
        {/if}
      </div>

      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-xs font-bold tracking-tight uppercase font-mono {isDark ? 'text-slate-100' : 'text-slate-900'}">
            Оперативная консоль реагирования
          </h2>
          <span class="text-[9px] font-mono px-2 py-0.5 rounded-md font-bold tracking-wide
            {isDark ? 'bg-[#293a52] text-slate-300 border border-slate-600/60' : 'bg-slate-200/70 text-slate-700 border border-slate-300'}">
            LIVE MATRIX
          </span>
        </div>
        <p class="text-[10px] font-mono {isDark ? 'text-slate-300/80' : 'text-slate-600 font-medium'} mt-0.5">
          {totalCount > 0 ? `Активных деградаций: ${totalCount}` : 'Все сетевые сегменты функционируют штатно'}
        </p>
      </div>
    </div>

    <!-- ТАБ-СЕЛЕКТОР (ЧЕТКИЙ КОНТРАСТ В LIGHT & DARK) -->
    <div class="flex items-center p-1 rounded-xl border transition-all
      {isDark ? 'bg-[#24334a] border-slate-600/60' : 'bg-slate-100 border-slate-300/80'}">
      
      <button 
        on:click={() => activeTab = 'all'}
        class="px-3 py-1 text-[11px] font-mono rounded-lg transition-all duration-150 cursor-pointer flex items-center gap-1.5
        {activeTab === 'all' 
          ? (isDark ? 'bg-[#334663] text-white shadow-xs font-bold' : 'bg-white text-slate-900 shadow-xs font-bold border border-slate-200') 
          : (isDark ? 'text-slate-300 hover:text-white' : 'text-slate-700 hover:text-slate-900 font-semibold')}"
      >
        <span>Все</span>
        <span class="text-[9px] opacity-75 tabular-nums">({totalCount})</span>
      </button>

      <button 
        on:click={() => activeTab = 'sw'}
        class="px-3 py-1 text-[11px] font-mono rounded-lg transition-all duration-150 cursor-pointer flex items-center gap-1.5
        {activeTab === 'sw' 
          ? (isDark ? 'bg-[#334663] text-white shadow-xs font-bold' : 'bg-white text-slate-900 shadow-xs font-bold border border-slate-200') 
          : (isDark ? 'text-slate-300 hover:text-white' : 'text-slate-700 hover:text-slate-900 font-semibold')}"
      >
        <span>Коммутаторы</span>
        <span class="text-[9px] {swCount > 0 ? (isDark ? 'text-rose-300 font-bold' : 'text-rose-700 font-bold') : 'opacity-75'} tabular-nums">({swCount})</span>
      </button>

      <button 
        on:click={() => activeTab = 'gpon'}
        class="px-3 py-1 text-[11px] font-mono rounded-lg transition-all duration-150 cursor-pointer flex items-center gap-1.5
        {activeTab === 'gpon' 
          ? (isDark ? 'bg-[#334663] text-white shadow-xs font-bold' : 'bg-white text-slate-900 shadow-xs font-bold border border-slate-200') 
          : (isDark ? 'text-slate-300 hover:text-white' : 'text-slate-700 hover:text-slate-900 font-semibold')}"
      >
        <span>Оптика GPON</span>
        <span class="text-[9px] {gponCount > 0 ? (isDark ? 'text-purple-300 font-bold' : 'text-purple-700 font-bold') : 'opacity-75'} tabular-nums">({gponCount})</span>
      </button>

      {#if oltCount > 0}
        <button 
          on:click={() => activeTab = 'olt'}
          class="px-2.5 py-1 text-[11px] font-mono font-bold rounded-lg transition-all duration-150 cursor-pointer flex items-center gap-1
          {activeTab === 'olt' 
            ? (isDark ? 'bg-rose-500/25 text-rose-300 border border-rose-500/40' : 'bg-rose-600 text-white shadow-xs') 
            : (isDark ? 'text-rose-400 hover:bg-rose-500/10' : 'text-rose-700 hover:bg-rose-100')}"
        >
          <span>OLT</span>
          <span class="text-[9px] tabular-nums font-bold">({oltCount})</span>
        </button>
      {/if}
    </div>
  </div>

  <!-- ИНЛАЙН-СТРИП OLT -->
  {#if offlineOlts.length > 0 && (activeTab === 'all' || activeTab === 'olt')}
    <div transition:slide={{duration: 160, easing: cubicOut}} class="px-5 py-2 border-b shrink-0 flex items-center justify-between gap-3 overflow-x-auto
      {isDark ? 'bg-[#222f44] border-slate-700/60' : 'bg-rose-50/70 border-rose-200/80'}">
      
      <div class="flex items-center gap-2 shrink-0">
        <span class="flex h-1.5 w-1.5 rounded-full {isDark ? 'bg-rose-400' : 'bg-rose-600'}"></span>
        <span class="text-[10px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-200' : 'text-rose-800'}">
          OLT Offline ({offlineOlts.length}):
        </span>
      </div>

      <div class="flex items-center gap-1.5 flex-wrap justify-end">
        {#each offlineOlts as olt}
          <button 
            on:click={() => copy(olt.ip)}
            title="Нажмите для копирования IP"
            class="group px-2 py-0.5 rounded-md border font-mono text-[10px] font-bold transition-all duration-150 flex items-center gap-1 cursor-pointer
            {isDark 
              ? 'bg-[#2a3a52] hover:bg-[#344866] border-slate-600/70 text-slate-200' 
              : 'bg-white hover:bg-rose-100 border-rose-300 text-rose-800 shadow-2xs'}"
          >
            <span>{olt.ip}</span>
            <span class="text-[8px] {isDark ? 'text-slate-400 group-hover:text-indigo-400' : 'text-rose-500'} transition-colors">
              {copiedText === olt.ip ? '✓' : '⧉'}
            </span>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- ОСНОВНОЙ КОНТЕНТ: СЕТКА ГРУПП НА ОДНОМ УРОВНЕ -->
  <div class="flex-1 p-4 overflow-y-auto min-h-0 always-visible-scroll">
    {#if totalCount === 0}
      <!-- EMPTY STATE -->
      <div class="h-full min-h-[220px] flex flex-col items-center justify-center text-center p-4" in:fade>
        <div class="w-10 h-10 rounded-2xl flex items-center justify-center mb-2.5 shadow-xs
          {isDark ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-100 text-emerald-700 border border-emerald-300'}">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 class="text-xs font-bold uppercase tracking-wider font-mono {isDark ? 'text-slate-200' : 'text-slate-800'}">
          Все сетевые сегменты в норме
        </h3>
        <p class="text-[11px] font-mono {isDark ? 'text-slate-400' : 'text-slate-600'} mt-0.5">Критических деградаций не зафиксировано</p>
      </div>

    {:else}
      <!-- ДВЕ СТРОГО ВЫРОВНЕННЫЕ КОЛОНКИ -->
      <div class="grid {activeTab === 'all' ? 'grid-cols-2 gap-4' : 'grid-cols-1 gap-2.5'} min-h-0 items-start">
        
        <!-- ================= КОЛОНКА 1: КОММУТАТОРЫ ================= -->
        {#if activeTab === 'all' || activeTab === 'sw'}
          <div class="flex flex-col min-h-0 space-y-2">
            
            <!-- ЕДИНЫЙ ЗАГОЛОВОК КОЛОНКИ -->
            {#if activeTab === 'all'}
              <div class="h-6 flex items-center justify-between px-1">
                <span class="text-[10px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-indigo-300' : 'text-indigo-700'}">
                  Коммутаторы ({swCount})
                </span>
              </div>
            {/if}

            {#if groupedSw.length === 0}
              <div class="p-6 text-center font-mono text-xs {isDark ? 'text-slate-400 border-slate-700/60 bg-[#222f44]/40' : 'text-slate-600 border-slate-200 bg-slate-50/70'} border rounded-2xl border-dashed">
                Коммутаторы работают штатно
              </div>
            {:else}
              {#each groupedSw as group}
                {@const isExpanded = expandedGroupKey === group.name}
                
                <div class="rounded-xl border transition-all duration-150 overflow-hidden
                  {isDark 
                    ? 'bg-[#223046] hover:bg-[#26374f] border-slate-700/60' 
                    : 'bg-white hover:bg-slate-50/80 border-slate-200 shadow-2xs'}"
                >
                  <button on:click={() => toggleGroup(group.name)}
                    class="w-full flex justify-between items-center p-3 text-left font-mono select-none cursor-pointer transition-colors
                    {isDark ? 'text-slate-200' : 'text-slate-900'}"
                  >
                    <div class="flex items-center gap-2.5 min-w-0 pr-2">
                      <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-indigo-400' : 'bg-indigo-600'} shrink-0"></span>
                      <span class="truncate font-sans font-semibold text-xs {isDark ? 'text-slate-200' : 'text-slate-900'}">{group.name}</span>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <span class="px-2 py-0.5 rounded-md text-[10px] font-bold tabular-nums
                        {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                        {group.items.length} DOWN
                      </span>
                      <svg class="w-3.5 h-3.5 {isDark ? 'text-slate-400' : 'text-slate-600'} transition-transform duration-150 {isExpanded ? 'rotate-180 text-indigo-500' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  <!-- РАСКРЫТЫЙ СПИСОК С КОНТРАСТНЫМ ТЕКСТОМ -->
                  {#if isExpanded}
                    <div transition:slide={{duration: 140, easing: cubicOut}} class="p-2 space-y-1.5 border-t {isDark ? 'border-slate-700/60 bg-[#223046]' : 'border-slate-100 bg-slate-50'}">
                      {#each group.items as item}
                        <div class="p-2.5 rounded-lg border flex justify-between items-center font-mono text-xs group transition-colors
                          {isDark ? 'bg-[#2a3a52] border-slate-600/70 text-slate-200' : 'bg-white border-slate-200 text-slate-900 shadow-2xs'}"
                        >
                          <div class="min-w-0 pr-2">
                            <div class="flex items-center gap-1.5">
                              <span class="font-bold text-[11px] {isDark ? 'text-indigo-300' : 'text-indigo-700'}">{item.id}</span>
                              <button 
                                on:click|stopPropagation={() => copy(item.id)}
                                class="opacity-0 group-hover:opacity-100 text-[10px] {isDark ? 'text-slate-400 hover:text-white' : 'text-slate-500 hover:text-slate-900'} transition-opacity cursor-pointer"
                                title="Копировать IP"
                              >
                                {copiedText === item.id ? '✓' : '⧉'}
                              </button>
                            </div>
                            <div class="font-sans text-[11px] font-medium {isDark ? 'text-slate-300/80' : 'text-slate-600'} truncate mt-0.5">
                              {item.contract.split('|')[0].trim()}
                            </div>
                          </div>
                          {#if item.los_time}
                            <span class="px-2.5 py-0.5 rounded-md text-[10px] font-bold font-mono tabular-nums shrink-0
                              {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
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
        {/if}

        <!-- ================= КОЛОНКА 2: GPON ПЛАТЫ ================= -->
        {#if activeTab === 'all' || activeTab === 'gpon'}
          <div class="flex flex-col min-h-0 space-y-2">
            
            <!-- ЕДИНЫЙ ЗАГОЛОВОК КОЛОНКИ -->
            {#if activeTab === 'all'}
              <div class="h-6 flex items-center justify-between px-1">
                <span class="text-[10px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-purple-300' : 'text-purple-700'}">
                  Оптика GPON ({gponCount})
                </span>
              </div>
            {/if}

            {#if nestedGpon.length === 0}
              <div class="p-6 text-center font-mono text-xs {isDark ? 'text-slate-400 border-slate-700/60 bg-[#222f44]/40' : 'text-slate-600 border-slate-200 bg-slate-50/70'} border rounded-2xl border-dashed">
                Оптические трассы в норме
              </div>
            {:else}
              {#each nestedGpon as oltGroup}
                {#each oltGroup.ports as portGroup}
                  {@const portKey = `${oltGroup.oltIp}-${portGroup.portName}`}
                  {@const isExpanded = expandedPortKey === portKey}

                  <div class="rounded-xl border transition-all duration-150 overflow-hidden
                    {isDark 
                      ? 'bg-[#223046] hover:bg-[#26374f] border-slate-700/60' 
                      : 'bg-white hover:bg-slate-50/80 border-slate-200 shadow-2xs'}"
                  >
                    <button on:click={() => togglePort(portKey)}
                      class="w-full flex justify-between items-center p-3 text-left font-mono select-none cursor-pointer transition-colors
                      {isDark ? 'text-slate-200' : 'text-slate-900'}"
                    >
                      <div class="flex items-center gap-2 min-w-0 pr-2">
                        <span class="{isDark ? 'text-purple-400' : 'text-purple-600'} text-xs shrink-0">⚡</span>
                        <span class="text-[10px] font-bold {isDark ? 'text-slate-400' : 'text-slate-600'} shrink-0 font-mono">{oltGroup.oltIp}</span>
                        <span class="text-slate-400 font-mono">/</span>
                        <span class="text-xs font-bold truncate {isDark ? 'text-slate-100' : 'text-slate-900'}">Плата {portGroup.portName}</span>
                      </div>

                      <div class="flex items-center gap-2 shrink-0">
                        <span class="px-2 py-0.5 rounded-md text-[10px] font-bold tabular-nums
                          {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                          {portGroup.items.length} LOS
                        </span>
                        <svg class="w-3.5 h-3.5 {isDark ? 'text-slate-400' : 'text-slate-600'} transition-transform duration-150 {isExpanded ? 'rotate-180 text-purple-500' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </button>

                    <!-- РАСКРЫТЫЙ СПИСОК ONU -->
                    {#if isExpanded}
                      <div transition:slide={{duration: 140, easing: cubicOut}} class="p-2 space-y-1.5 border-t {isDark ? 'border-slate-700/60 bg-[#223046]' : 'border-slate-100 bg-slate-50'}">
                        {#each portGroup.items as item}
                          <div class="p-2.5 rounded-lg border flex justify-between items-center font-mono text-xs group transition-colors
                            {isDark ? 'bg-[#2a3a52] border-slate-600/70 text-slate-200' : 'bg-white border-slate-200 text-slate-900 shadow-2xs'}"
                          >
                            <div class="min-w-0 pr-2">
                              <div class="flex items-center gap-1.5">
                                <span class="font-bold text-[11px] {isDark ? 'text-purple-300' : 'text-purple-700'}">
                                  #{item.id.split(':').pop()}
                                </span>
                                <button 
                                  on:click|stopPropagation={() => copy(item.contract.split('|')[0].trim())}
                                  class="opacity-0 group-hover:opacity-100 text-[10px] {isDark ? 'text-slate-400 hover:text-purple-300' : 'text-slate-500 hover:text-purple-700'} transition-opacity cursor-pointer"
                                  title="Копировать договор"
                                >
                                  {copiedText === item.contract.split('|')[0].trim() ? '✓' : '⧉'}
                                </button>
                              </div>
                              <div class="font-sans text-[11px] font-medium {isDark ? 'text-slate-300/80' : 'text-slate-600'} truncate mt-0.5">
                                {item.contract.split('|')[0].trim()}
                              </div>
                            </div>
                            {#if item.los_time}
                              <span class="px-2.5 py-0.5 rounded-md text-[10px] font-bold font-mono tabular-nums shrink-0
                                {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                                ⏱ {formatLosTime(item.los_time, currentUnixTime)}
                              </span>
                            {/if}
                          </div>
                        {/each}
                      </div>
                    {/if}
                  </div>
                {/each}
              {/each}
            {/if}
          </div>
        {/if}

      </div>
    {/if}
  </div>
</div>