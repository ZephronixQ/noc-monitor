<!-- frontend\src\components\SwitchesTab.svelte -->
<script context="module">
  // Сохраняем состояние фильтрации Коммутаторов в модульной памяти
  let savedGlobalSwLosFilter = false;
  let savedSwitchSearchQuery = '';
  let savedActiveFolderIndex = 0;
</script>

<script>
  import { slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  import { getDotColor, formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;
  export let switchFolders = [];
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();

  // Инициализация из сохраненного состояния модуля
  let activeFolderIndex = savedActiveFolderIndex;
  let switchSearchQuery = savedSwitchSearchQuery; 
  let globalSwLosFilter = savedGlobalSwLosFilter;

  $: savedActiveFolderIndex = activeFolderIndex;
  $: savedSwitchSearchQuery = switchSearchQuery;
  $: savedGlobalSwLosFilter = globalSwLosFilter;

  $: filteredSwitchFolders = switchFolders.filter(folder => {
    if (!globalSwLosFilter) return true;
    return folder.onus.some(sw => !['working', 'host is alive'].includes((sw.state||'').trim().toLowerCase()));
  });

  $: if (activeFolderIndex >= filteredSwitchFolders.length) activeFolderIndex = 0;
  $: currentSwitchFolder = filteredSwitchFolders[activeFolderIndex] || { onus: [] };
  $: allSwitchesFlat = switchFolders.flatMap(folder => folder.onus || []);

  $: displayedSwitches = switchSearchQuery 
    ? allSwitchesFlat.filter(sw => sw.id.toLowerCase().includes(switchSearchQuery.toLowerCase()) || (sw.contract || '').toLowerCase().includes(switchSearchQuery.toLowerCase()))
    : (currentSwitchFolder.onus || []).filter(sw => !globalSwLosFilter || !['working', 'host is alive'].includes((sw.state||'').trim().toLowerCase()));
</script>

<div class="flex gap-6 h-full overflow-hidden min-h-0">
  
  <!-- Левая колонка: Локации (Облегченный плоский UI-дизайн) -->
  {#if !switchSearchQuery}
    <div class="w-64 h-full flex flex-col gap-1 overflow-y-auto pr-3 pb-4 always-visible-scroll min-h-0" transition:slide={{ axis: 'x', duration: 200 }}>
      
      <!-- Выделенный заголовок "Локации" с GPS-иконкой -->
      <div class="flex items-center gap-2.5 px-1.5 mb-3 shrink-0 select-none">
        <svg class="w-3.5 h-3.5 text-indigo-400 animate-pulse" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
        </svg>
        <span class="text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-md shadow-sm
          {isDark 
            ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20' 
            : 'bg-indigo-50 text-indigo-600 border border-indigo-100'}">
          Локации
        </span>
      </div>
      
      {#if filteredSwitchFolders.length === 0}
        <div class="text-xs font-bold text-slate-400 text-center mt-10">Все коммутаторы в сети</div>
      {/if}

      {#each filteredSwitchFolders as folder, i}
        {@const downs = folder.onus.filter(s => !['working', 'host is alive'].includes((s.state||'').trim().toLowerCase())).length}
        
        <button on:click={() => activeFolderIndex = i} 
          class="p-4 shrink-0 rounded-2xl border text-left transition-all duration-200 relative overflow-hidden flex flex-col justify-between min-h-[78px] gap-2
          {activeFolderIndex === i 
            ? (isDark 
                ? 'bg-indigo-600/15 border-indigo-500/40 text-white shadow-[0_4px_16px_rgba(99,102,241,0.12)]' 
                : 'bg-indigo-50 border-indigo-200 text-indigo-900 shadow-sm') 
            : (isDark 
                ? 'bg-[#1c2333]/30 border-slate-800/40 hover:bg-[#1c2333]/60 text-slate-300' 
                : 'bg-slate-100/30 border-slate-200/50 hover:bg-white text-slate-700')}"
        >
          <!-- Активная вертикальная линия слева -->
          {#if activeFolderIndex === i}
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-indigo-500 shadow-[1px_0_8px_rgba(99,102,241,0.6)]"></div>
          {/if}

          <!-- Диод аварии -->
          {#if folder.is_mass_outage} 
            <div class="absolute top-3 right-3 w-1.5 h-1.5 bg-rose-500 rounded-full animate-ping"></div>
            <div class="absolute top-3 right-3 w-1.5 h-1.5 bg-rose-500 rounded-full shadow-md"></div> 
          {/if}
          
          <div class="font-bold text-sm truncate pr-4">{folder.name}</div>
          
          <div class="flex justify-between items-center w-full">
            <span class="text-[10px] font-bold opacity-75 uppercase tracking-wider">{folder.onus.length} узлов</span>
            
            {#if folder.is_mass_outage} 
              <span class="text-[8px] font-black px-1.5 py-0.5 rounded bg-rose-500 text-white shadow-[0_0_8px_rgba(239,68,68,0.4)] animate-pulse">АВАРИЯ</span>
            {:else if downs > 0} 
              <span class="text-[8px] font-black px-1.5 py-0.5 rounded {isDark ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-rose-50 text-rose-600 border border-rose-100'}">{downs} DOWN</span>
            {:else} 
              <span class="text-[8px] font-black px-1.5 py-0.5 rounded {isDark ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-emerald-50 text-emerald-600 border border-emerald-100'}">ОК</span> 
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}

  <!-- Правая колонка: Поиск и Сетка коммутаторов -->
  <div class="flex-1 flex flex-col gap-4 h-full min-w-0 min-h-0">
    
    <!-- Панель поиска -->
    <div class="flex gap-3 shrink-0">
      <input type="text" bind:value={switchSearchQuery} placeholder="Поиск по IP или адресу..." 
        class="flex-1 rounded-2xl px-6 py-3 shadow-sm outline-none transition-all font-semibold text-sm border 
        {isDark 
          ? 'bg-[#1c2333] text-slate-200 placeholder-slate-500 border-slate-800/80 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30' 
          : 'bg-white border-slate-200/80 focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400/20 text-slate-900'}" 
      />
      <button on:click={() => globalSwLosFilter = !globalSwLosFilter} 
        class="px-6 rounded-2xl font-bold text-xs tracking-wider transition-all duration-200 border
        {globalSwLosFilter 
          ? 'bg-rose-500 text-white border-rose-500 shadow-[0_4px_14px_rgba(239,68,68,0.35)]' 
          : (isDark 
              ? 'bg-[#1c2333] text-slate-400 border-slate-800/80 hover:bg-[#1e273a] hover:text-slate-200' 
              : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50')}"
      >
        ТОЛЬКО LOS
      </button>
    </div>
    
    <!-- Сетка из 4-х колонок -->
    <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-y-auto pr-2 pb-4 content-start always-visible-scroll min-h-0">
      {#each displayedSwitches as sw}
        {@const isUp = ['working', 'host is alive'].includes((sw.state||'').trim().toLowerCase())}
        {@const descParts = sw.contract ? sw.contract.split('|') : []}
        {@const address = descParts[0] ? descParts[0].trim() : '—'}
        {@const deviceModel = descParts[1] ? descParts[1].trim() : ''}

        <!-- Вернули компактные ячейки коммутаторов -->
        <div class="p-3.5 rounded-2xl border shadow-sm flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[120px] relative overflow-hidden group
          {isDark 
            ? 'bg-[#1c2333] hover:bg-[#20293d] hover:shadow-lg' 
            : 'bg-white hover:shadow-md'}
          {isUp 
            ? (isDark ? 'border-slate-800/80 border-l-4 border-l-emerald-500 hover:border-slate-700' : 'border-slate-200/70 border-l-4 border-l-emerald-500 hover:border-slate-300') 
            : (isDark ? 'border-slate-800 border-l-4 border-l-rose-500 hover:border-slate-700' : 'border-slate-200 border-l-4 border-l-rose-500 hover:border-slate-300')}"
          on:click={() => dispatch('openHistory', { contract: sw.contract, id: sw.id })}
        >
          <!-- Верхний блок -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="font-mono font-bold text-[10px] tracking-tight px-2 py-0.5 rounded shadow-inner transition-all
                {isDark 
                  ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20' 
                  : 'bg-indigo-50 text-indigo-600 border border-indigo-100'}">
                {sw.id}
              </span>
              <div class="w-2 h-2 rounded-full {getDotColor(sw.state)}"></div>
            </div>

            <div class="text-[11px] font-bold leading-normal line-clamp-1 {isDark ? 'text-slate-100' : 'text-slate-800'}" title={address}>
              {address}
            </div>

            {#if deviceModel}
              <div class="text-[9px] font-bold text-slate-400 dark:text-slate-500 font-mono uppercase tracking-wider truncate mt-1 flex items-center gap-1 select-none">
                <span class="text-indigo-400 opacity-80">⑂</span> {deviceModel}
              </div>
            {/if}
          </div>
          
          <!-- Нижний ряд -->
          <div class="flex justify-between items-center mt-2.5 pt-1.5 border-t border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'}">
            {#if isUp}
              <span class="text-[8px] font-extrabold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/10">WORKING</span>
            {:else}
              <span class="text-[8px] font-extrabold tracking-wider px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/10">{sw.state ? sw.state.toUpperCase() : 'DOWN'}</span>
            {/if}
            
            {#if !isUp && sw.los_time}
              <div class="text-[9px] font-bold text-rose-400 flex items-center gap-1 select-none">
                <span class="text-[10px]">⏱</span> {formatLosTime(sw.los_time, currentUnixTime)}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>