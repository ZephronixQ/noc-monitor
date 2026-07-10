<!-- frontend\src\components\GponOltSidebar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let olts = [];
  export let activeOltIp = ""; // ИСПРАВЛЕНО: связываем OLT по IP
  export let globalLosFilter = false;
  export let globalLosiFilter = false;

  const dispatch = createEventDispatcher();

  $: filteredOlts = olts.filter(olt => {
    const ports = olt.ports || [];
    if (globalLosFilter) return ports.some(p => (p.onus || []).some(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())));
    if (globalLosiFilter) return ports.some(p => (p.onus || []).some(o => (o.state||'').trim().toLowerCase() === 'losi'));
    return true;
  });

  // Если текущий IP не найден в отфильтрованном списке, выбираем первый доступный
  $: if (filteredOlts.length > 0 && !filteredOlts.some(o => o.ip === activeOltIp)) {
    activeOltIp = filteredOlts[0].ip;
  }
</script>

<div class="w-64 h-full flex flex-col gap-2.5 overflow-y-auto pr-3 pb-4 always-visible-scroll min-h-0 select-none">
  
  <div class="flex items-center gap-2.5 px-1.5 mb-3 shrink-0">
    <svg class="w-3.5 h-3.5 text-indigo-400 animate-pulse" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9s2.015-9 4.5-9m0 0a9.003 9.003 0 018.716 5.253M12 3a9.003 9.003 0 00-8.716 5.253" />
    </svg>
    <span class="text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md shadow-sm
      {isDark 
        ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20' 
        : 'bg-indigo-50 text-indigo-600 border border-indigo-100'}">
      Список OLT
    </span>
  </div>
  
  {#if filteredOlts.length === 0}
    <div class="text-xs font-bold text-slate-400 text-center mt-10">Все OLT работают нормально</div>
  {/if}

  {#each filteredOlts as olt}
    {@const allOnus = (olt.ports || []).flatMap(p => p.onus || [])}
    {@const onlineCount = allOnus.filter(o => (o.state||'').trim().toLowerCase() === 'working').length}
    {@const losCount = allOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length}
    {@const losiCount = allOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length}
    {@const hasMass = (olt.ports || []).some(p => p.is_mass_outage)}
    
    <button on:click={() => dispatch('select', olt.ip)}
      class="p-4 shrink-0 rounded-2xl border text-left transition-all duration-200 relative overflow-hidden flex flex-col gap-2.5
      {activeOltIp === olt.ip 
        ? (isDark 
            ? 'bg-indigo-600/15 border-indigo-500/40 text-white shadow-[0_4px_20px_rgba(99,102,241,0.12)]' 
              : 'bg-indigo-50 border-indigo-200 text-indigo-900 shadow-sm') 
        : (isDark 
            ? 'bg-[#1c2333]/40 border-slate-800/80 hover:bg-[#1c2333]/75 text-slate-300' 
            : 'bg-slate-100/50 border-slate-200/80 hover:bg-white text-slate-700')}"
    >
      {#if activeOltIp === olt.ip}
        <div class="absolute left-0 top-0 bottom-0 w-1 bg-indigo-500 shadow-[1px_0_8px_rgba(99,102,241,0.6)]"></div>
      {/if}

      {#if hasMass}
        <div class="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full animate-ping"></div>
        <div class="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full shadow-md"></div>
      {/if}
      
      <div class="flex justify-between items-start w-full">
        <div class="font-mono font-bold text-sm tracking-tight {activeOltIp === olt.ip ? 'text-indigo-400 dark:text-indigo-300' : ''}">{olt.ip}</div>
        
        <div class="flex gap-1 items-end select-none font-mono">
          {#if losCount > 0}
            <span class="text-[8px] font-black bg-rose-500/10 border border-rose-500/20 text-rose-400 px-1.5 py-0.5 rounded-md whitespace-nowrap">{losCount} LOS</span>
          {/if}
          {#if losiCount > 0}
            <span class="text-[8px] font-black bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-400 px-1.5 py-0.5 rounded-md whitespace-nowrap">{losiCount} LOSi</span>
          {/if}
        </div>
      </div>
      
      <div class="flex justify-between mt-0.5 items-center w-full">
        <div class="flex-1 h-1 bg-slate-200/30 rounded-full overflow-hidden {isDark ? 'bg-slate-700' : ''}">
          <div class="bg-indigo-500 h-full transition-all duration-300" style="width: {allOnus.length > 0 ? (onlineCount/allOnus.length)*100 : 0}%"></div>
        </div>
        <span class="text-[9px] font-black opacity-75 whitespace-nowrap ml-3 font-mono">
          {onlineCount}/{allOnus.length}
        </span>
      </div>
    </button>
  {/each}
</div>