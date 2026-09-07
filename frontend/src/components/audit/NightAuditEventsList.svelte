<!-- frontend/src/components/audit/NightAuditEventsList.svelte -->
<script>
  import { slide } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { createEventDispatcher } from 'svelte';
  import NightAuditSwitchItem from './NightAuditSwitchItem.svelte';

  export let isDark = false;
  export let selectedDay = 3;
  export let monthName = "";
  export let shiftFilter = 'night';
  export let switchIncidents = []; 
  export let oltIncidents = [];
  export let gponHierarchy = [];   
  export let isLoading = false;

  const dispatch = createEventDispatcher();

  let activeOltKey = null;
  let activeGponPortKey = null;
  let activeSwitchFolderKey = null;
  let copiedText = null;

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

  function copy(val) {
    if (!val || val === '—') return;
    navigator.clipboard.writeText(val);
    copiedText = val;
    setTimeout(() => { copiedText = null; }, 1200);
  }

  $: totalSwitchCount = switchIncidents.reduce((s, f) => s + (f.items ? f.items.length : 0), 0);
  $: totalOltCount = oltIncidents.length;
  $: totalGponCount = gponHierarchy.reduce((acc, o) => acc + (o.ports || []).reduce((sum, p) => sum + (p.onus ? p.onus.length : 0), 0), 0);
</script>

<div class="flex-1 rounded-2xl border shadow-md flex flex-col overflow-hidden font-sans transition-colors min-h-0
  {isDark ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200' : 'bg-white border-slate-200/90 text-slate-800'}"
>
  <!-- ЗАГОЛОВОК СПИСКА -->
  <div class="px-4 py-3 border-b flex items-center justify-between shrink-0 select-none
    {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'}">
    
    <div class="flex items-center gap-2">
      <span class="text-xs font-bold font-mono uppercase tracking-wider {isDark ? 'text-white' : 'text-slate-900'}">
        Инциденты смены: {selectedDay} {monthName}
      </span>
      <span class="text-[10px] font-mono px-2 py-0.5 rounded-md border font-bold
        {isDark ? 'bg-[#223046] text-indigo-300 border-slate-600/70' : 'bg-white text-indigo-800 border-slate-200'}">
        {shiftFilter === 'night' ? 'Ночная смена (17:00–09:00)' : 'Полные сутки (24 часа)'}
      </span>
    </div>

    {#if isLoading}
      <span class="text-[9.5px] font-mono font-bold text-indigo-400 animate-pulse flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
        Считывание SQLite базы...
      </span>
    {/if}
  </div>

  <!-- ДВЕ КОЛОНКИ: КОММУТАТОРЫ L2 СЛЕВА, GPON + АВАРИИ OLT СПРАВА -->
  <div class="flex-1 grid grid-cols-2 gap-4 p-4 min-h-0 overflow-hidden">
    
    <!-- ================= КОЛОНКА 1: КОММУТАТОРЫ L2 ================= -->
    <div class="flex flex-col min-h-0 border-r {isDark ? 'border-slate-700/60' : 'border-slate-200'} pr-3">
      
      <div class="flex items-center justify-between mb-2.5 shrink-0 px-1 font-mono">
        <div class="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider {isDark ? 'text-indigo-400' : 'text-indigo-700'}">
          <span class="w-2 h-2 rounded-full {isDark ? 'bg-indigo-400' : 'bg-indigo-600'}"></span>
          <span>Коммутаторы L2 ({totalSwitchCount})</span>
        </div>
      </div>
      
      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
        {#if switchIncidents.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs py-8 text-slate-400">
            <div class="w-10 h-10 rounded-2xl flex items-center justify-center mb-2 {isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-100 text-emerald-700'}">✓</div>
            <span class="font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Сбоев коммутаторов нет</span>
            <span class="text-[10px] text-slate-400 mt-0.5">В эту смену оборудование работало стабильно</span>
          </div>
        {:else}
          {#each switchIncidents as folder}
            {@const folderName = folder.folder_name || folder.folderName}
            {@const isFolderExpanded = activeSwitchFolderKey === folderName}
            
            <div class="rounded-xl border overflow-hidden transition-all duration-150
              {isDark ? 'border-slate-700/70 bg-[#223046]/90' : 'border-slate-200 bg-white shadow-2xs'}">
              
              <button 
                on:click={() => toggleSwitchFolder(folderName)}
                class="w-full flex justify-between items-center p-3 text-left font-mono text-xs select-none cursor-pointer transition-colors
                {isDark ? 'hover:bg-[#283952] text-slate-100' : 'hover:bg-slate-50 text-slate-900'}"
              >
                <div class="flex items-center gap-2 min-w-0 pr-2">
                  <span class="text-indigo-400 font-bold">📁</span>
                  <span class="font-sans font-bold text-xs truncate {isDark ? 'text-slate-100' : 'text-slate-900'}">{folderName}</span>
                </div>

                <div class="flex items-center gap-2 shrink-0">
                  <span class="px-2 py-0.5 rounded-md text-[10px] font-bold border tabular-nums
                    {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                    {folder.items.length} узел(-ов)
                  </span>
                  <svg class="w-3.5 h-3.5 text-slate-400 transition-transform duration-150 {isFolderExpanded ? 'rotate-180 text-indigo-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {#if isFolderExpanded}
                <div transition:slide={{duration: 140, easing: cubicOut}} class="p-2 space-y-1.5 border-t {isDark ? 'border-slate-700/70 bg-[#223046]' : 'border-slate-100 bg-slate-50'}">
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

    <!-- ================= КОЛОНКА 2: GPON (АВАРИИ OLT + СТРОГО КРАСНЫЙ LOS) ================= -->
    <div class="flex flex-col min-h-0 pl-1 space-y-3">
      
      <!-- 2.1 БЛОК АВАРИЙ ГОЛОВНЫХ СТАНЦИЙ OLT -->
      {#if totalOltCount > 0}
        <div class="shrink-0 flex flex-col gap-2">
          <div class="flex items-center justify-between px-1 font-mono">
            <div class="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider {isDark ? 'text-rose-400' : 'text-rose-600'}">
              <span class="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
              <span>Аварии станций OLT ({totalOltCount})</span>
            </div>
            <span class="text-[9px] font-mono font-bold px-2 py-0.5 rounded border
              {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-50 text-rose-700 border-rose-200'}">
              CRITICAL
            </span>
          </div>

          <div class="space-y-1.5">
            {#each oltIncidents as oltEvent}
              {@const timeStart = oltEvent.time_start || oltEvent.timeStart || ''}
              {@const timeEnd = oltEvent.time_end || oltEvent.timeEnd || ''}
              
              <div class="p-3 rounded-xl border flex items-center justify-between gap-3 transition-all
                {isDark 
                  ? 'bg-[#2a3a52] border-rose-500/40 shadow-sm' 
                  : 'bg-white border-slate-200 border-l-4 border-l-rose-500 shadow-2xs hover:border-slate-300'}">
                
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 mb-0.5 font-mono">
                    <span class="font-black text-xs px-2 py-0.5 rounded-lg border
                      {isDark ? 'bg-[#1e2a3e] text-purple-300 border-purple-500/40' : 'bg-slate-100 text-purple-800 border-slate-200'}">
                      {oltEvent.id}
                    </span>
                    <span class="text-[9px] font-black px-1.5 py-0.2 rounded border uppercase
                      {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-50 text-rose-700 border-rose-200'}">
                      OLT OFFLINE
                    </span>
                  </div>
                  <div class="font-sans text-xs font-bold truncate {isDark ? 'text-white' : 'text-slate-900'} mt-1">
                    Головная OLT станция GPON
                  </div>
                </div>

                <div class="flex items-center gap-2.5 shrink-0 select-none">
                  <div class="text-right font-mono text-[10px] leading-tight">
                    <span class="text-slate-400 font-bold text-[8px] uppercase tracking-wider block">период</span>
                    <span class="text-rose-500 font-bold block">{timeStart}</span>
                    <span class="text-slate-400 block text-[9px]">({timeEnd})</span>
                  </div>

                  <button 
                    on:click={() => dispatch('openHistory', { contract: `OLT Станция ${oltEvent.id}`, id: oltEvent.id, type: 'olt' })}
                    class="px-2.5 py-1 rounded-lg border text-[9.5px] font-bold font-mono transition-all cursor-pointer shadow-2xs active:scale-95
                    {isDark ? 'bg-[#223046] border-slate-500/70 text-indigo-300 hover:bg-[#283852] hover:text-white' : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-slate-100'}"
                  >
                    Логи OLT
                  </button>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- 2.2 ОБРЫВЫ АБОНЕНТСКОЙ ОПТИКИ GPON (СТРОГО КРАСНЫЙ ДЛЯ АВАРИЙ LOS) -->
      <div class="flex-1 flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-2.5 shrink-0 px-1 font-mono">
          <div class="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider {isDark ? 'text-rose-400' : 'text-rose-600'}">
            <span class="w-2 h-2 rounded-full {isDark ? 'bg-rose-500' : 'bg-rose-600'}"></span>
            <span>Оптика GPON ({totalGponCount} LOS)</span>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
          {#if gponHierarchy.length === 0}
            <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs py-8 text-slate-400">
              <div class="w-10 h-10 rounded-2xl flex items-center justify-center mb-2 {isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-100 text-emerald-700'}">✓</div>
              <span class="font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Обрывов оптики не зафиксировано</span>
              <span class="text-[10px] text-slate-400 mt-0.5">В выбранную смену физических сбоев LOS не было</span>
            </div>
          {:else}
            {#each gponHierarchy as oltGroup}
              {@const oltIp = oltGroup.olt_ip || oltGroup.oltIp}
              {@const losCount = oltGroup.los_count ?? oltGroup.losCount ?? 0}
              {@const isOltExpanded = activeOltKey === oltIp}

              <div class="rounded-xl border overflow-hidden transition-all duration-150
                {isDark ? 'border-slate-700/70 bg-[#223046]/90' : 'border-slate-200 bg-white shadow-2xs'}">
                
                <!-- УРОВЕНЬ 1: OLT СТАНЦИЯ (КРАСНЫЙ ИНДИКАТОР АВАРИИ) -->
                <button 
                  on:click={() => toggleOlt(oltIp)}
                  class="w-full flex justify-between items-center p-3 text-left font-mono text-xs select-none cursor-pointer transition-colors
                  {isDark ? 'hover:bg-[#283952] text-slate-100' : 'hover:bg-slate-50 text-slate-900'}"
                >
                  <div class="flex items-center gap-2 min-w-0 pr-2">
                    <span class="w-2 h-2 rounded-full bg-rose-500 shrink-0"></span>
                    <span class="text-xs font-bold {isDark ? 'text-rose-400' : 'text-rose-600'}">OLT:</span>
                    <span class="truncate font-black text-xs {isDark ? 'text-white' : 'text-slate-900'}">{oltIp}</span>
                  </div>

                  <div class="flex items-center gap-2 shrink-0">
                    <span class="px-2 py-0.5 rounded-md text-[10px] font-bold border tabular-nums
                      {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                      {losCount} LOS
                    </span>
                    <svg class="w-3.5 h-3.5 text-slate-400 transition-transform duration-150 {isOltExpanded ? 'rotate-180 text-rose-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                <!-- УРОВЕНЬ 2: ПЛАТЫ OLT -->
                {#if isOltExpanded}
                  <div transition:slide={{duration: 140, easing: cubicOut}} class="p-2 space-y-1.5 border-t {isDark ? 'border-slate-700/70 bg-[#223046]' : 'border-slate-100 bg-slate-50'}">
                    {#each oltGroup.ports as port}
                      {@const portName = port.port_name || port.portName}
                      {@const portKey = `${oltIp}-${portName}`}
                      {@const isPortExpanded = activeGponPortKey === portKey}

                      <div class="rounded-xl border overflow-hidden transition-colors
                        {isDark ? 'border-slate-600/70 bg-[#283852]' : 'border-slate-200 bg-white shadow-2xs'}">
                        
                        <button 
                          on:click|stopPropagation={() => toggleGponPort(oltIp, portName)}
                          class="w-full flex justify-between items-center p-2.5 text-left font-mono text-[11px] select-none cursor-pointer transition-colors
                          {isDark ? 'hover:bg-[#2e405e] text-slate-100' : 'hover:bg-slate-50 text-slate-900'}"
                        >
                          <div class="flex items-center gap-1.5">
                            <span class="{isDark ? 'text-rose-400' : 'text-rose-600'} font-bold">⚡ Плата</span>
                            <span class="font-extrabold text-xs">{portName}</span>
                          </div>

                          <div class="flex items-center gap-2">
                            <span class="px-1.5 py-0.5 rounded text-[9.5px] font-bold border
                              {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                              {port.onus.length} LOS
                            </span>
                            <svg class="w-3 h-3 text-slate-400 transition-transform duration-150 {isPortExpanded ? 'rotate-180 text-rose-400' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </button>

                        <!-- УРОВЕНЬ 3: АБОНЕНТЫ ONU -->
                        {#if isPortExpanded}
                          <div transition:slide={{duration: 130}} class="p-2 space-y-1.5 border-t {isDark ? 'border-slate-600/60 bg-[#24334a]' : 'border-slate-100 bg-slate-50/70'}">
                            {#each port.onus as onu}
                              {@const timeStart = onu.time_start || onu.timeStart}
                              {@const timeEnd = onu.time_end || onu.timeEnd}
                              {@const contract = onu.contract || '—'}
                              {@const rawAddress = contract.split('|')[0]?.trim()}
                              {@const address = (rawAddress && rawAddress !== '—') ? rawAddress : 'Узел без описания в биллинге'}
                              
                              <div class="p-2.5 rounded-lg border flex items-center justify-between gap-3 font-mono text-xs transition-colors group
                                {isDark ? 'bg-[#2a3a52] border-slate-600/70 text-slate-100 hover:border-slate-500' : 'bg-white border-slate-200 text-slate-900 shadow-2xs'}"
                              >
                                <div class="min-w-0 pr-2">
                                  <div class="flex items-center gap-1.5 mb-1">
                                    <span class="font-black text-[11px] {isDark ? 'text-indigo-300' : 'text-indigo-700'}">#{onu.id}</span>
                                    <span class="text-[8.5px] font-extrabold px-1.5 py-0.2 rounded border
                                      {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                                      LOS
                                    </span>
                                    <button 
                                      on:click|stopPropagation={() => copy(address)}
                                      class="opacity-0 group-hover:opacity-100 text-[10px] text-slate-400 hover:text-white transition-opacity p-0.5 cursor-pointer"
                                      title="Копировать адрес"
                                    >
                                      {copiedText === address ? '✓' : '⧉'}
                                    </button>
                                  </div>
                                  <div class="font-sans text-xs font-semibold truncate {isDark ? 'text-slate-200' : 'text-slate-800'} {address === 'Узел без описания в биллинге' ? 'opacity-60 italic text-[11px]' : ''}" title={address}>
                                    {address}
                                  </div>
                                </div>

                                <div class="flex items-center gap-2.5 shrink-0 select-none">
                                  <div class="text-right font-mono text-[10px] leading-tight">
                                    <span class="text-rose-500 font-bold block">{timeStart}</span>
                                    <span class="text-slate-400 block text-[9px]">({timeEnd})</span>
                                  </div>
                                  <button 
                                    on:click={() => dispatch('openHistory', { contract: contract, id: `${oltIp}:${portName}:${onu.id}`, type: 'onu' })}
                                    class="px-2.5 py-1 rounded-lg border text-[9.5px] font-bold font-mono transition-all cursor-pointer shadow-2xs active:scale-95
                                    {isDark ? 'bg-[#223046] border-slate-500/70 text-indigo-300 hover:bg-[#283852] hover:text-white' : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-slate-100'}"
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
</div>