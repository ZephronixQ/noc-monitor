<!-- frontend/src/components/gpon/GponTab.svelte -->
<script context="module">
  let savedActiveOltIp = null; 
  let savedSearchQuery = ''; 
  let savedGlobalLosFilter = false;
  let savedGlobalLosiFilter = false;
  let savedActivePort = null;
  let savedCurrentPage = 1;
  let savedPortSortField = 'default';
  let savedPortSortDirection = 'desc';
</script>

<script>
  import { createEventDispatcher, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import GponOltSidebar from './GponOltSidebar.svelte';
  import GponToolbar from './GponToolbar.svelte';
  import GponPortCard from './GponPortCard.svelte';

  export let isDark = false;
  export let olts = [];
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();

  let activeOltIp = savedActiveOltIp; 
  let searchQuery = savedSearchQuery; 
  let globalLosFilter = savedGlobalLosFilter;
  let globalLosiFilter = savedGlobalLosiFilter;
  let activePort = savedActivePort;
  let currentPage = savedCurrentPage;
  const itemsPerPage = 16;

  let portSortField = savedPortSortField; 
  let portSortDirection = savedPortSortDirection;
  let portsContainerRef;

  async function scrollToPortTop() {
    await tick();
    if (portsContainerRef) {
      portsContainerRef.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function handlePortPageChange(newPage) {
    currentPage = newPage;
    scrollToPortTop();
  }

  function handleSortChange(e) {
    const targetField = e.detail;
    if (portSortField === targetField) {
      portSortDirection = portSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      portSortField = targetField;
      portSortDirection = targetField === 'name' ? 'asc' : 'desc';
    }
    currentPage = 1;
    scrollToPortTop();
  }

  async function handleTogglePort(e) {
    const { name, event } = e.detail;
    const isExpanding = activePort !== name;
    activePort = isExpanding ? name : null;

    if (isExpanding) {
      await tick();
      const targetCard = event.currentTarget.closest('.rounded-2xl');
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  // Натуральная сортировка IP по возрастанию (2.11, 2.12, 2.13...)
  function sortIpAsc(a, b) {
    const numA = (a.ip || '').split('.').map(Number);
    const numB = (b.ip || '').split('.').map(Number);
    for (let i = 0; i < Math.max(numA.length, numB.length); i++) {
      const nA = numA[i] || 0;
      const nB = numB[i] || 0;
      if (nA !== nB) return nA - nB;
    }
    return 0;
  }

  $: savedActiveOltIp = activeOltIp;
  $: savedSearchQuery = searchQuery;
  $: savedGlobalLosFilter = globalLosFilter;
  $: savedGlobalLosiFilter = globalLosiFilter;
  $: savedActivePort = activePort;
  $: savedCurrentPage = currentPage;
  $: savedPortSortField = portSortField;
  $: savedPortSortDirection = portSortDirection;

  // Расчет общих метрик всей сети GPON
  $: allOnusFlat = (olts || []).flatMap(o => (o.ports || []).flatMap(p => p.onus || []));
  $: totalOnus = allOnusFlat.length;
  $: onlineOnus = allOnusFlat.filter(o => ['working', 'host is alive'].includes((o.state||'').trim().toLowerCase())).length;
  $: losCount = allOnusFlat.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length;
  $: losiCount = allOnusFlat.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length;

  // Обогащенные станции OLT со всеми статусами для спектральной полосы
  $: enrichedOlts = (olts || []).map(o => {
    const all = (o.ports || []).flatMap(p => p.onus || []);
    const los = all.filter(onu => ['los', 'down'].includes((onu.state||'').trim().toLowerCase())).length;
    const losi = all.filter(onu => (onu.state||'').trim().toLowerCase() === 'losi').length;
    const dying = all.filter(onu => (onu.state||'').trim().toLowerCase() === 'dyinggasp').length;
    const online = all.filter(onu => ['working', 'host is alive'].includes((onu.state||'').trim().toLowerCase())).length;
    const total = all.length;
    const offline = Math.max(0, total - online - los - losi - dying);
    const health = total > 0 ? ((online / total) * 100) : 0;
    return {
      ip: o.ip,
      ports: o.ports || [],
      los,
      losi,
      dying,
      offline,
      online,
      total,
      health
    };
  }).sort(sortIpAsc);

  // Фильтр OLT на главном экране
  $: visibleOlts = enrichedOlts.filter(o => {
    if (globalLosFilter && o.los === 0) return false;
    if (globalLosiFilter && o.losi === 0) return false;
    
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      return (o.ports || []).some(port => {
        const matchPort = port.name.toLowerCase().includes(q);
        const matchOnu = (port.onus || []).some(onu => (onu.contract || '').toLowerCase().includes(q) || (onu.id || '').toLowerCase().includes(q));
        return matchPort || matchOnu;
      });
    }

    return true;
  });

  // Текущая открытая станция
  $: currentOlt = activeOltIp ? olts.find(o => o.ip === activeOltIp) || null : null;

  // Фильтрация портов выбранной станции
  $: filteredPorts = (currentOlt?.ports || [])
    .filter(port => {
      const onus = port.onus || [];
      const hasLos = onus.some(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase()));
      const hasLosi = onus.some(o => (o.state||'').trim().toLowerCase() === 'losi');
      
      if (globalLosFilter && !hasLos) return false;
      if (globalLosiFilter && !hasLosi) return false;
      
      if (!searchQuery.trim()) return true;
      const q = searchQuery.trim().toLowerCase();
      return port.name.toLowerCase().includes(q) || onus.some(o => (o.contract || '').toLowerCase().includes(q) || (o.id || '').toLowerCase().includes(q));
    })
    .sort((a, b) => {
      const onusA = a.onus || [];
      const onusB = b.onus || [];

      if (portSortField === 'default') {
        if (a.is_mass_outage && !b.is_mass_outage) return -1;
        if (!a.is_mass_outage && b.is_mass_outage) return 1;

        const losA = onusA.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length;
        const losiA = onusA.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length;
        const scoreA = (losA * 10000) + losiA;

        const losB = onusB.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length;
        const losiB = onusB.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length;
        const scoreB = (losB * 10000) + losiB;

        return portSortDirection === 'desc' ? scoreB - scoreA : scoreA - scoreB;
      } 
      else if (portSortField === 'name') {
        const partsA = (a.name || "").split('/').map(Number);
        const partsB = (b.name || "").split('/').map(Number);
        for (let i = 0; i < Math.max(partsA.length, partsB.length); i++) {
          const numA = partsA[i] || 0;
          const numB = partsB[i] || 0;
          if (numA !== numB) {
            return portSortDirection === 'asc' ? numA - numB : numB - numA;
          }
        }
        return 0;
      }
      return 0;
    });

  // Авто-раскрытие найденной платы при поиске
  $: {
    if (searchQuery.trim() && filteredPorts.length > 0) {
      activePort = filteredPorts[0].name;
    }
  }

  $: paginatedPorts = filteredPorts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  $: totalPages = Math.ceil(filteredPorts.length / itemsPerPage);
</script>

<div class="flex-1 flex flex-col gap-3.5 h-full overflow-hidden min-h-0 font-sans" in:fade={{ duration: 150 }}>
  
  <!-- 1. ТУЛБАР GPON -->
  <GponToolbar 
    {isDark}
    {totalOnus}
    {onlineOnus}
    {losCount}
    {losiCount}
    selectedOltIp={activeOltIp}
    bind:searchQuery
    bind:globalLosFilter
    bind:globalLosiFilter
    bind:portSortField
    {portSortDirection}
    on:backToGrid={() => activeOltIp = null}
    on:toggleLos={() => { globalLosFilter = !globalLosFilter; globalLosiFilter = false; }}
    on:toggleLosi={() => { globalLosiFilter = !globalLosiFilter; globalLosFilter = false; }}
    on:changeSort={handleSortChange}
  />

  <!-- 2. ОСНОВНОЙ КОНТЕНТ -->
  {#if !activeOltIp}
    
    <!-- РЕЖИМ 1: СЕТКА СТАНЦИЙ OLT СО СПЕКТРАЛЬНЫМИ ПОЛОСАМИ -->
    <div class="flex-1 rounded-2xl border p-3.5 overflow-y-auto transition-colors min-h-0 always-visible-scroll shadow-md
      {isDark ? 'bg-[#1e2a3e] border-slate-700/70' : 'bg-white border-slate-200/90'}">
      
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5 content-start">
        {#each visibleOlts as olt}
          {@const isTroubled = olt.los > 0 || olt.losi > 0 || olt.total === 0}

          <button 
            on:click={() => { activeOltIp = olt.ip; currentPage = 1; scrollToPortTop(); }}
            class="p-4 rounded-2xl border text-left transition-all duration-150 flex flex-col justify-between gap-3 cursor-pointer group relative overflow-hidden select-none transform hover:-translate-y-1 hover:shadow-lg
            {isDark 
              ? 'bg-[#223046]/80 hover:bg-[#283952] border-slate-700/60 hover:border-indigo-500/50' 
              : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-indigo-300 shadow-2xs'}"
          >
            <!-- ВЕРХ КАРТОЧКИ OLT: IP + ЧИПЫ LOS / LOSI -->
            <div class="flex items-center justify-between gap-2 font-mono">
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-2 h-2 rounded-full shrink-0 
                  {olt.total === 0 ? 'bg-rose-500 animate-pulse' : (olt.los > 0 ? 'bg-rose-500 animate-ping' : (olt.losi > 0 ? 'bg-purple-400' : 'bg-emerald-500'))}">
                </span>
                <h3 class="text-sm font-bold tracking-tight truncate {isDark ? 'text-white' : 'text-slate-900'} group-hover:text-indigo-600 transition-colors">
                  {olt.ip}
                </h3>
              </div>

              <div class="flex items-center gap-1 text-[10px] font-extrabold shrink-0">
                {#if olt.los > 0}
                  <span class="px-2 py-0.5 rounded-lg border {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                    {olt.los} LOS
                  </span>
                {/if}
                {#if olt.losi > 0}
                  <span class="px-2 py-0.5 rounded-lg border {isDark ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' : 'bg-purple-100 text-purple-800 border border-purple-300'}">
                    {olt.losi} LOSi
                  </span>
                {/if}
                {#if olt.los === 0 && olt.losi === 0 && olt.total > 0}
                  <span class="text-emerald-500 font-bold">✓ 100%</span>
                {/if}
              </div>
            </div>

            <!-- ПОЛНОЦЕННАЯ МУЛЬТИСЕГМЕНТНАЯ СПЕКТРАЛЬНАЯ ШКАЛА СТАНЦИИ -->
            <div class="w-full h-[3px] rounded-full overflow-hidden flex {isDark ? 'bg-slate-700/60' : 'bg-slate-200'}">
              {#if olt.total === 0}
                <div class="h-full w-full bg-rose-500"></div>
              {:else}
                <!-- 1. Онлайн (зеленый) -->
                {#if olt.online > 0}
                  <div 
                    class="h-full {isDark ? 'bg-emerald-400' : 'bg-emerald-500'} transition-all duration-300" 
                    style="width: {(olt.online / olt.total) * 100}%" 
                    title="Онлайн: {olt.online}">
                  </div>
                {/if}

                <!-- 2. DyingGasp (желтый) -->
                {#if olt.dying > 0}
                  <div 
                    class="h-full bg-amber-400 transition-all duration-300" 
                    style="width: {(olt.dying / olt.total) * 100}%" 
                    title="DyingGasp: {olt.dying}">
                  </div>
                {/if}

                <!-- 3. LOSi (фиолетовый) -->
                {#if olt.losi > 0}
                  <div 
                    class="h-full bg-purple-500 transition-all duration-300" 
                    style="width: {(olt.losi / olt.total) * 100}%" 
                    title="LOSi: {olt.losi}">
                  </div>
                {/if}

                <!-- 4. LOS (красный с пульсацией) -->
                {#if olt.los > 0}
                  <div 
                    class="h-full bg-rose-500 animate-pulse transition-all duration-300" 
                    style="width: {(olt.los / olt.total) * 100}%" 
                    title="LOS: {olt.los}">
                  </div>
                {/if}

                <!-- 5. Offline (серый) -->
                {#if olt.offline > 0}
                  <div 
                    class="h-full bg-slate-400/80 transition-all duration-300" 
                    style="width: {(olt.offline / olt.total) * 100}%" 
                    title="Offline: {olt.offline}">
                  </div>
                {/if}
              {/if}
            </div>

            <!-- НИЗ: ЕМКОСТЬ + ПЛАТЫ -->
            <div class="flex justify-between items-center text-xs font-mono {isDark ? 'text-slate-400 border-slate-700/50' : 'text-slate-600 border-slate-100'} pt-1 border-t">
              <span>{olt.ports.length} плат · {olt.total} ONU</span>
              <span class="text-[11px] font-bold text-indigo-400 group-hover:translate-x-1 transition-transform">
                Платы →
              </span>
            </div>
          </button>
        {/each}
      </div>
    </div>

  {:else}

    <!-- РЕЖИМ 2: ОТКРЫТАЯ СТАНЦИЯ OLT -->
    <div class="flex-1 flex gap-5 min-h-0 overflow-hidden">
      
      <!-- САЙДБАР OLT СТАНЦИЙ СЛЕВА -->
      <GponOltSidebar 
        {isDark} 
        olts={olts} 
        bind:activeOltIp 
        {globalLosFilter} 
        {globalLosiFilter} 
        on:select={(e) => { activeOltIp = e.detail; currentPage = 1; scrollToPortTop(); }}
        on:openOltHistory={(e) => dispatch('openHistory', e.detail)}
      />

      <!-- ПРАВАЯ ЧАСТЬ: ЛЕНТА ПЛАТ ЭТОЙ СТАНЦИИ -->
      <div class="flex-1 flex flex-col min-w-0 min-h-0">
        <div bind:this={portsContainerRef} class="flex-1 overflow-y-auto space-y-2.5 pr-1 pb-4 always-visible-scroll min-h-0">
          {#if paginatedPorts.length === 0}
            <div class="p-12 text-center rounded-2xl border border-dashed font-mono text-xs
              {isDark ? 'border-slate-700/60 bg-[#1e2a3e] text-slate-400' : 'border-slate-200 bg-white text-slate-500'}"
            >
              На выбранной OLT станции нет плат или устройств с совпадающими условиями поиска.
            </div>
          {:else}
            {#each paginatedPorts as port}
              <GponPortCard 
                {isDark}
                {port}
                currentOltIp={currentOlt?.ip}
                {currentUnixTime}
                {activePort}
                {globalLosFilter}
                {globalLosiFilter}
                on:togglePort={handleTogglePort}
                on:openHistory={(e) => dispatch('openHistory', e.detail)}
              />
            {/each}
          {/if}
        </div>
        
        <!-- ПАГИНАЦИЯ -->
        {#if totalPages > 1}
          <div class="shrink-0 flex items-center justify-center gap-2 pt-1 select-none font-mono text-[10px]">
            <button
              on:click={() => handlePortPageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              class="px-3 py-1.5 rounded-xl font-bold transition-all disabled:opacity-30 border cursor-pointer
                {isDark ? 'bg-[#1e2a3e] text-slate-300 border-slate-700/70 hover:bg-slate-700' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'}"
            >
              ← НАЗАД
            </button>

            <span class="font-bold px-2 {isDark ? 'text-slate-300' : 'text-slate-600'}">
              {currentPage} / {totalPages} · {filteredPorts.length} портов
            </span>

            <button
              on:click={() => handlePortPageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              class="px-3 py-1.5 rounded-xl font-bold transition-all disabled:opacity-30 border cursor-pointer
                {isDark ? 'bg-[#1e2a3e] text-slate-300 border-slate-700/70 hover:bg-slate-700' : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'}"
            >
              ВПЕРЁД →
            </button>
          </div>
        {/if}
      </div>

    </div>

  {/if}

</div>