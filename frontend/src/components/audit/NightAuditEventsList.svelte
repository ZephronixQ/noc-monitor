<!-- frontend/src/components/audit/NightAuditEventsList.svelte -->
<script>
  import { slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  import NightAuditSwitchItem from './NightAuditSwitchItem.svelte';

  export let isDark = false;
  export let selectedDay = 10;
  export let monthName = "";
  export let shiftFilter = 'night';
  export let switchIncidents = []; 
  export let gponHierarchy = [];   
  export let isLoading = false;

  const dispatch = createEventDispatcher();

  let activeOltKey = null;
  let activeGponPortKey = null;
  let activeSwitchFolderKey = null;

  function toggleOlt(oltIp) {
    activeOltKey = activeOltKey === oltIp ? null : oltIp;
  }

  function toggleSwitchFolder(folderName) {
    activeSwitchFolderKey = activeSwitchFolderKey === folderName ? null : folderName;
  }

  function toggleGponPort(oltIp, portName) {
    const key = `${oltIp}-${portName}`;
    activeGponPortKey = activeGponPortKey === key ? null : key;
  }

  $: totalSwitchCount = switchIncidents.reduce((s, f) => s + (f.items ? f.items.length : 0), 0);
  $: totalGponCount = gponHierarchy.reduce((acc, o) => acc + (o.ports || []).reduce((sum, p) => sum + (p.onus ? p.onus.length : 0), 0), 0);
</script>

<div class="flex-1 p-5 rounded-2xl border shadow-xs flex flex-col overflow-hidden font-sans transition-colors
  {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
>
  <div class="pb-3 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} flex justify-between items-center select-none shrink-0 mb-4">
    <div class="flex items-center gap-2">
      <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-200' : 'text-slate-700'}">
        Инциденты за: {selectedDay} {monthName}
      </span>
      {#if isLoading}
        <span class="text-[10px] font-mono text-indigo-400 animate-pulse">● Считывание SQLite...</span>
      {/if}
    </div>
    
    <div class="flex items-center gap-1 p-1 rounded-full border transition-all select-none
      {isDark ? 'bg-[#18253f] border-slate-700/60' : 'bg-slate-100 border-slate-200'}"
    >
      <button on:click={() => { shiftFilter = 'night'; activeOltKey = null; activeGponPortKey = null; activeSwitchFolderKey = null; }}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider transition-all cursor-pointer
        {shiftFilter === 'night' 
          ? 'bg-indigo-500 text-white shadow-2xs' 
          : (isDark ? 'text-slate-300 hover:text-slate-100' : 'text-slate-600 hover:text-slate-900')}"
      >
        Ночь (17:00 - 09:00)
      </button>
      <button on:click={() => { shiftFilter = 'all'; activeOltKey = null; activeGponPortKey = null; activeSwitchFolderKey = null; }}
        class="px-4 py-1.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider transition-all cursor-pointer
        {shiftFilter === 'all' 
          ? 'bg-indigo-500 text-white shadow-2xs' 
          : (isDark ? 'text-slate-300 hover:text-slate-100' : 'text-slate-600 hover:text-slate-900')}"
      >
        Все за сутки
      </button>
    </div>
  </div>

  <div class="flex-1 grid grid-cols-2 gap-5 min-h-0">
    
    <!-- Коммутаторы -->
    <div class="flex flex-col min-h-0 border-r border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} pr-3">
      <h3 class="text-[11px] font-bold tracking-wider uppercase font-mono text-indigo-400 select-none px-1 mb-2.5 shrink-0">
        🔌 Сбои коммутаторов ({totalSwitchCount})
      </h3>
      
      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
        {#if switchIncidents.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs py-8 text-slate-400">
            <span>✨ Сбоев коммутаторов не зафиксировано</span>
          </div>
        {:else}
          {#each switchIncidents as folder}
            {@const folderName = folder.folder_name || folder.folderName}
            {@const isFolderExpanded = activeSwitchFolderKey === folderName}
            
            <div class="rounded-xl border overflow-hidden transition-colors {isDark ? 'border-slate-700/60 bg-[#18253f]' : 'border-slate-200 bg-slate-50'}">
              <button on:click={() => toggleSwitchFolder(folderName)}
                class="w-full flex justify-between items-center p-2.5 text-left font-mono text-xs font-semibold select-none cursor-pointer
                {isDark ? 'hover:bg-slate-700/60 text-slate-100' : 'hover:bg-slate-100 text-slate-900'}"
              >
                <div class="flex items-center gap-1.5 min-w-0 pr-2">
                  <span class="text-indigo-400 shrink-0">◆ Локация:</span>
                  <span class="truncate {isDark ? 'text-slate-100' : 'text-slate-900'}">{folderName}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded-md text-[10px] bg-rose-500/15 text-rose-400 border border-rose-500/30 font-bold">{folder.items.length} устр.</span>
                  <svg class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200 {isFolderExpanded ? 'rotate-180 text-indigo-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {#if isFolderExpanded}
                <div transition:slide={{duration: 150}} class="p-2 space-y-1.5 border-t border-dashed {isDark ? 'border-slate-700/60 bg-[#141f33]' : 'border-slate-200 bg-white'}">
                  {#each folder.items as event}
                    <NightAuditSwitchItem {event} {isDark} on:openHistory />
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        {/if}
      </div>
    </div>

    <!-- GPON -->
    <div class="flex flex-col min-h-0">
      <h3 class="text-[11px] font-bold tracking-wider uppercase font-mono text-purple-400 select-none px-1 mb-2.5 shrink-0">
        ✂️ Сбои оптики GPON LOS ({totalGponCount})
      </h3>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
        {#if gponHierarchy.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs py-8 text-slate-400">
            <span>✨ Обрывов оптики GPON не зафиксировано</span>
          </div>
        {:else}
          {#each gponHierarchy as oltGroup}
            {@const oltIp = oltGroup.olt_ip || oltGroup.oltIp}
            {@const losCount = oltGroup.los_count ?? oltGroup.losCount ?? 0}
            {@const isOltExpanded = activeOltKey === oltIp}

            <div class="rounded-xl border overflow-hidden transition-colors {isDark ? 'border-slate-700/60 bg-[#18253f]' : 'border-slate-200 bg-slate-50'}">
              <button on:click={() => toggleOlt(oltIp)}
                class="w-full flex justify-between items-center p-2.5 text-left font-mono text-xs font-semibold select-none cursor-pointer
                {isDark ? 'hover:bg-slate-700/60 text-slate-100' : 'hover:bg-slate-100 text-slate-900'}"
              >
                <div class="flex items-center gap-2 min-w-0 pr-2">
                  <span class="text-indigo-400 font-bold shrink-0">⚙ OLT:</span>
                  <span class="truncate font-bold {isDark ? 'text-slate-100' : 'text-slate-900'}">{oltIp}</span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded-md text-[10px] bg-rose-500/15 text-rose-400 border border-rose-500/30 font-bold">{losCount} LOS</span>
                  <svg class="w-3.5 h-3.5 text-slate-400 transition-transform duration-200 {isOltExpanded ? 'rotate-180 text-indigo-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {#if isOltExpanded}
                <div transition:slide={{duration: 150}} class="p-2 space-y-1.5 border-t border-dashed {isDark ? 'border-slate-700/60 bg-[#141f33]' : 'border-slate-200 bg-white'}">
                  {#each oltGroup.ports as port}
                    {@const portName = port.port_name || port.portName}
                    {@const portKey = `${oltIp}-${portName}`}
                    {@const isPortExpanded = activeGponPortKey === portKey}

                    <div class="rounded-lg border overflow-hidden transition-colors {isDark ? 'border-slate-700/60 bg-[#1c273e]' : 'border-slate-200 bg-slate-50/80'}">
                      <button on:click|stopPropagation={() => toggleGponPort(oltIp, portName)}
                        class="w-full flex justify-between items-center p-2 text-left font-mono text-[11px] font-semibold select-none cursor-pointer
                        {isDark ? 'hover:bg-slate-700/80 text-slate-100' : 'hover:bg-slate-100 text-slate-900'}"
                      >
                        <div class="flex items-center gap-1.5">
                          <span class="text-purple-400 font-normal">Plata:</span>
                          <span class="font-semibold">{portName}</span>
                        </div>
                        <div class="flex items-center gap-2">
                          <span class="px-1.5 py-0.5 rounded text-[9.5px] bg-rose-500/15 text-rose-400 border border-rose-500/30 font-bold">{port.onus.length} LOS</span>
                          <svg class="w-3 h-3 text-slate-400 transition-transform duration-200 {isPortExpanded ? 'rotate-180 text-purple-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      </button>

                      {#if isPortExpanded}
                        <div transition:slide={{duration: 150}} class="p-2 space-y-1.5 border-t border-dashed {isDark ? 'border-slate-700/60 bg-[#162238]' : 'border-slate-200 bg-white'}">
                          {#each port.onus as onu}
                            {@const timeStart = onu.time_start || onu.timeStart}
                            {@const timeEnd = onu.time_end || onu.timeEnd}
                            {@const contract = onu.contract || '—'}
                            
                            <div class="p-2 rounded-lg border flex items-center justify-between gap-3 font-mono text-xs
                              {isDark ? 'bg-[#1a263c] border-slate-700/60 text-slate-100' : 'bg-slate-50 border-slate-200 text-slate-900'}"
                            >
                              <div class="min-w-0 pr-2">
                                <div class="flex items-center gap-1.5 mb-0.5 flex-wrap select-none">
                                  <span class="font-bold text-[11px] text-indigo-400">#{onu.id}</span>
                                  <span class="text-[9px] font-bold bg-rose-500/15 text-rose-400 px-1.5 py-0.2 rounded uppercase border border-rose-500/20">LOS</span>
                                </div>
                                <div class="font-sans text-xs font-semibold truncate mt-0.5 {isDark ? 'text-slate-200' : 'text-slate-800'}" title={contract.split('|')[0].trim()}>
                                  {contract.split('|')[0].trim()}
                                </div>
                              </div>

                              <div class="flex items-center gap-3 shrink-0 select-none">
                                <div class="text-right font-mono text-[10px] leading-tight">
                                  <span class="text-rose-500 font-bold block">{timeStart}</span>
                                  <span class="text-slate-400 block text-[9px]">({timeEnd})</span>
                                </div>
                                <button on:click={() => dispatch('openHistory', { contract: contract, id: `${oltIp}:${portName}:${onu.id}`, type: 'onu' })}
                                  class="px-2 py-1 rounded-lg border text-[10px] font-bold font-mono transition-colors cursor-pointer
                                  {isDark ? 'bg-[#152033] border-slate-700 text-indigo-400 hover:text-indigo-300' : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
                                >
                                  Логи
                                </button>
                              </div>
                            </div>
                          {/each}
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

  </div>
</div>