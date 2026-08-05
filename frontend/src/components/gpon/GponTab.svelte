<!-- frontend/src/components/gpon/GponTab.svelte -->
<script context="module">
  let savedActiveOltIp = ''; 
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

  $: if (!activeOltIp && olts.length > 0) {
    activeOltIp = olts[0].ip;
  }

  $: savedActiveOltIp = activeOltIp;
  $: savedSearchQuery = searchQuery;
  $: savedGlobalLosFilter = globalLosFilter;
  $: savedGlobalLosiFilter = globalLosiFilter;
  $: savedActivePort = activePort;
  $: savedCurrentPage = currentPage;
  $: savedPortSortField = portSortField;
  $: savedPortSortDirection = portSortDirection;

  $: currentOlt = olts.find(o => o.ip === activeOltIp) || { ports: [] };

  $: filteredPorts = (currentOlt.ports || [])
    .filter(port => {
      const onus = port.onus || [];
      const hasLos = onus.some(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase()));
      const hasLosi = onus.some(o => (o.state||'').trim().toLowerCase() === 'losi');
      
      if (globalLosFilter && !hasLos) return false;
      if (globalLosiFilter && !hasLosi) return false;
      
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return port.name.toLowerCase().includes(q) || onus.some(o => (o.contract || '').toLowerCase().includes(q));
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

  $: paginatedPorts = filteredPorts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  $: totalPages = Math.ceil(filteredPorts.length / itemsPerPage);
</script>

<div class="flex gap-6 h-full overflow-hidden min-h-0">
  
  <GponOltSidebar 
    {isDark} 
    {olts} 
    bind:activeOltIp 
    {globalLosFilter} 
    {globalLosiFilter} 
    on:select={(e) => { activeOltIp = e.detail; currentPage = 1; scrollToPortTop(); }}
    on:openOltHistory={(e) => dispatch('openHistory', e.detail)}
  />

  <div class="flex-1 flex flex-col gap-2 h-full min-w-0 min-h-0">
    
    <GponToolbar 
      {isDark}
      bind:searchQuery
      bind:globalLosFilter
      bind:globalLosiFilter
      bind:portSortField
      {portSortDirection}
      on:toggleLos={() => { globalLosFilter = !globalLosFilter; globalLosiFilter = false; currentPage = 1; scrollToPortTop(); }}
      on:toggleLosi={() => { globalLosiFilter = !globalLosiFilter; globalLosFilter = false; currentPage = 1; scrollToPortTop(); }}
      on:changeSort={handleSortChange}
    />

    <div bind:this={portsContainerRef} class="flex-1 overflow-y-auto space-y-3 pr-2 pb-4 always-visible-scroll min-h-0">
      {#if paginatedPorts.length === 0}
        <div class="p-12 text-center rounded-2xl border border-dashed text-slate-400 font-mono text-xs
          {isDark ? 'border-slate-700/60 bg-[#1e2a40]' : 'border-slate-200 bg-white'}"
        >
          На выбранной OLT станции нет плат или устройств с совпадающими условиями поиска.
        </div>
      {:else}
        {#each paginatedPorts as port}
          <GponPortCard 
            {isDark}
            {port}
            currentOltIp={currentOlt.ip}
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
    
    {#if totalPages > 1}
      <div class="shrink-0 flex items-center justify-center gap-2 pt-1 select-none font-mono text-[10px]">
        <button
          on:click={() => handlePortPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          class="px-3 py-1.5 rounded-xl font-bold transition-all disabled:opacity-30 border cursor-pointer
            {isDark ? 'bg-[#1e2a40] text-slate-300 border-slate-700/70 hover:bg-slate-700' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}"
        >
          ← НАЗАД
        </button>

        <span class="font-bold px-2 {isDark ? 'text-slate-300' : 'text-slate-500'}">
          {currentPage} / {totalPages} · {filteredPorts.length} портов
        </span>

        <button
          on:click={() => handlePortPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          class="px-3 py-1.5 rounded-xl font-bold transition-all disabled:opacity-30 border cursor-pointer
            {isDark ? 'bg-[#1e2a40] text-slate-300 border-slate-700/70 hover:bg-slate-700' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}"
        >
          ВПЕРЁД →
        </button>
      </div>
    {/if}
  </div>

</div>