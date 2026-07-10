<!-- frontend\src\components\GponTab.svelte -->
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
  import { slide } from 'svelte/transition';
  import { createEventDispatcher, tick } from 'svelte'; // ИСПРАВЛЕНО: Добавлен импорт tick
  
  import GponOltSidebar from './GponOltSidebar.svelte';
  import GponOnuTable from './GponOnuTable.svelte';

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

  function exportPortCsv(port) {
    if (!port) return;
    const onus = port.onus || [];
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "ID,Договор/Адрес,Статус\n";
    onus.forEach(onu => {
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

  function togglePortSort(field) {
    if (portSortField === field) {
      portSortDirection = portSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      portSortField = field;
      portSortDirection = 'asc';
    }
    currentPage = 1;
  }

  // ИСПРАВЛЕНО: Плавная интеллектуальная прокрутка страницы для центрирования раскрытой платы
  async function togglePort(portName, event) {
    const isExpanding = activePort !== portName;
    activePort = isExpanding ? portName : null;

    if (isExpanding) {
      await tick(); // Дожидаемся перерисовки Svelte и появления таблицы абонентов на экране
      
      const targetCard = event.currentTarget.closest('.rounded-2xl');
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
        const badA = onusA.filter(o => ['los', 'down', 'losi'].includes((o.state||'').trim().toLowerCase())).length;
        const badB = onusB.filter(o => ['los', 'down', 'losi'].includes((o.state||'').trim().toLowerCase())).length;
        return portSortDirection === 'desc' ? badB - badA : badA - badB;
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
    on:select={(e) => { activeOltIp = e.detail; currentPage = 1; }}
  />

  <div class="flex-1 flex flex-col gap-4 h-full min-w-0 min-h-0">
    <div class="flex gap-3 shrink-0 select-none items-center">
      <input type="text" bind:value={searchQuery} placeholder="Поиск по интерфейсу или договору..." 
        class="flex-1 rounded-2xl px-6 py-3 shadow-sm outline-none transition-all font-semibold text-sm border 
        {isDark 
          ? 'bg-[#1c2333] text-slate-200 placeholder-slate-500 border-slate-800/80 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30' 
          : 'bg-white border-slate-200/80 focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400/20 text-slate-900'}" 
      />
      
      <div class="flex items-center gap-1 p-1 rounded-xl border shrink-0 font-mono text-[10px] font-bold
        {isDark ? 'bg-black/30 border-slate-800' : 'bg-slate-100 border-slate-200'}"
      >
        <button on:click={() => { portSortField = 'default'; portSortDirection = 'desc'; }}
          class="px-2.5 py-1 rounded-lg transition-all
          {portSortField === 'default' 
            ? 'bg-indigo-500 text-white shadow-sm' 
            : (isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800')}"
        >
          По авариям
        </button>
        <button on:click={() => togglePortSort('name')}
          class="px-2.5 py-1 rounded-lg transition-all flex items-center gap-1
          {portSortField === 'name' 
            ? 'bg-indigo-500 text-white shadow-sm' 
            : (isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800')}"
        >
          По имени платы
          {#if portSortField === 'name'}
            <span>{portSortDirection === 'asc' ? '▲' : '▼'}</span>
          {/if}
        </button>
      </div>
      
      <button on:click={() => {globalLosFilter = !globalLosFilter; globalLosiFilter = false; currentPage = 1;}} 
        class="px-6 py-3 rounded-2xl font-bold text-xs tracking-wider transition-all duration-200 border shrink-0
        {globalLosFilter 
          ? 'bg-rose-500 text-white border-rose-500 shadow-[0_4px_14px_rgba(239,68,68,0.35)]' 
          : (isDark ? 'bg-[#1c2333] text-slate-400 border-slate-800/80 hover:bg-[#1e273a] hover:text-slate-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50')}"
      >
        ТОЛЬКО LOS
      </button>
      
      <button on:click={() => {globalLosiFilter = !globalLosiFilter; globalLosFilter = false; currentPage = 1;}} 
        class="px-6 py-3 rounded-2xl font-bold text-xs tracking-wider transition-all duration-200 border shrink-0
        {globalLosiFilter 
          ? 'bg-fuchsia-500 text-white border-fuchsia-500 shadow-[0_4px_14px_rgba(217,70,239,0.35)]' 
          : (isDark ? 'bg-[#1c2333] text-slate-400 border-slate-800/80 hover:bg-[#1e273a] hover:text-slate-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50')}"
      >
        ТОЛЬКО LOSi
      </button>
    </div>

    <div class="flex-1 overflow-y-auto space-y-3 pr-2 pb-4 always-visible-scroll min-h-0">
      {#each paginatedPorts as port}
        {@const pOnus = port.onus || []}
        {@const strictLosCount = pOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length}
        {@const losiCount = pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length}
        
        <div class="rounded-2xl shrink-0 shadow-sm border overflow-hidden transition-all duration-200
          {port.is_mass_outage 
            ? (isDark ? 'border-rose-900/60 bg-[#291b2c]' : 'border-rose-300 bg-rose-50/50') 
            : (isDark ? 'bg-[#1c2333] border-slate-800/80' : 'bg-white border-slate-200/60')}"
        >
          <!-- ИСПРАВЛЕНО: Клик по шапке переведен на функцию togglePort с плавным центрированием -->
          <div class="flex items-center justify-between pr-5 cursor-pointer hover:opacity-90 select-none" 
            on:click={(e) => togglePort(port.name, e)}
          >
            <div class="flex-1 flex items-center gap-6 p-4.5">
              <span class="font-mono font-black w-14 text-base {isDark ? 'text-indigo-400' : 'text-slate-900'}">{port.name}</span>
              
              {#if port.is_mass_outage}
                <span class="px-2.5 py-0.5 text-[8px] font-black rounded bg-rose-500 text-white shadow-md animate-pulse uppercase tracking-widest">Авария порта</span>
              {:else}
                <div class="w-64 h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-800' : 'bg-slate-100'}">
                  <div class="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full" style="width: {pOnus.length > 0 ? ((pOnus.length - (strictLosCount + losiCount))/pOnus.length)*100 : 0}%"></div>
                </div>
              {/if}
              
              <div class="text-[11px] font-bold flex gap-2 font-mono">
                {#if strictLosCount > 0}<span class="text-rose-500">{strictLosCount} LOS</span>{/if}
                {#if losiCount > 0}<span class="text-fuchsia-500">{losiCount} LOSi</span>{/if}
                {#if strictLosCount === 0 && losiCount === 0}<span class={isDark ? 'text-slate-500' : 'text-slate-400'}>0 проблем</span>{/if}
                <span class="text-slate-400 select-none">/ {pOnus.length} ONU</span>
              </div>
            </div>
            
            <button on:click|stopPropagation={() => exportPortCsv(port)} 
              class="text-[9px] px-2.5 py-1 rounded-md font-bold transition-all border
              {isDark ? 'bg-white/[0.03] border-slate-700 text-slate-300 hover:text-white hover:bg-indigo-500 hover:border-indigo-500' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 hover:border-slate-300'}"
            >
              CSV
            </button>
          </div>

          {#if activePort === port.name}
            <GponOnuTable 
              {isDark} 
              {pOnus} 
              currentOltIp={currentOlt.ip} 
              {currentUnixTime} 
              subFilter={globalLosFilter ? 'los' : (globalLosiFilter ? 'losi' : 'all')}
              on:openHistory
            />
          {/if}
        </div>
      {/each}
    </div>
    
    {#if totalPages > 1}
      <div class="shrink-0 flex items-center justify-center gap-2 pt-2 select-none">
        <button
          on:click={() => currentPage = Math.max(1, currentPage - 1)}
          disabled={currentPage === 1}
          class="px-4 py-2 rounded-xl font-bold text-[10px] tracking-wider transition-all disabled:opacity-30 border
            {isDark ? 'bg-[#1c2333] text-slate-300 border-slate-800 hover:bg-[#1e273a] hover:text-white' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}"
        >
          ← НАЗАД
        </button>

        <div class="flex gap-1">
          {#each Array(totalPages) as _, i}
            {#if totalPages <= 7 || i === 0 || i === totalPages - 1 || Math.abs(i + 1 - currentPage) <= 1}
              <button
                on:click={() => currentPage = i + 1}
                class="w-8 h-8 rounded-xl font-bold text-[10px] transition-all border
                  {currentPage === i + 1
                    ? 'bg-indigo-500 text-white shadow-[0_2px_8px_rgba(99,102,241,0.35)]'
                    : (isDark ? 'bg-[#1c2333] text-slate-400 border-slate-800/80 hover:bg-[#1e273a] hover:text-slate-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50')}"
              >
                {i + 1}
              </button>
            {:else if Math.abs(i + 1 - currentPage) === 2}
              <span class="w-8 h-8 flex items-center justify-center text-slate-400 font-bold">…</span>
            {/if}
          {/each}
        </div>

        <button
          on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
          disabled={currentPage === totalPages}
          class="px-4 py-2 rounded-xl font-bold text-[10px] tracking-wider transition-all disabled:opacity-30 border
            {isDark ? 'bg-[#1c2333] text-slate-300 border-slate-800 hover:bg-[#1e273a] hover:text-white' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}"
        >
          ВПЕРЁД →
        </button>

        <span class="text-[10px] font-bold ml-2 {isDark ? 'text-slate-400' : 'text-slate-500'}">
          {currentPage} / {totalPages} · {filteredPorts.length} портов
        </span>
      </div>
    {/if}
  </div>
</div>