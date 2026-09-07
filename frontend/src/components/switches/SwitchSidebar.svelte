<!-- frontend/src/components/switches/SwitchSidebar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { slide } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;
  export let mode = 'main'; // 'main' | 'group'
  export let folders = [];
  export let selectedGroupName = null;
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();
  
  let expandedMap = {};
  $: {
    if (mode === 'main') {
      folders.forEach(f => {
        if (f.down > 0 && expandedMap[f.name] === undefined) {
          expandedMap[f.name] = true;
        }
      });
    }
  }

  let copied = null;

  function toggleExpand(name) {
    expandedMap[name] = !expandedMap[name];
  }

  function copy(e, ip) {
    e.stopPropagation();
    navigator.clipboard.writeText(ip);
    copied = ip;
    setTimeout(() => { copied = null; }, 1200);
  }

  $: totalDown = folders.reduce((s, g) => s + g.down, 0);
  $: troubledFolders = folders.filter(f => f.down > 0);
</script>

<div class="w-72 h-full flex flex-col rounded-2xl border transition-all duration-300 overflow-hidden shrink-0 select-none shadow-md
  {isDark ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200' : 'bg-white border-slate-200/90 text-slate-800'}"
>
  <!-- ШАПКА -->
  <div class="px-4 py-3 border-b flex items-center justify-between shrink-0
    {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'}">
    <div class="flex items-center gap-1.5">
      <span class="w-2 h-2 rounded-full {mode === 'main' ? (totalDown > 0 ? 'bg-rose-500 animate-ping' : 'bg-emerald-500') : (isDark ? 'bg-indigo-400' : 'bg-indigo-600')}"></span>
      <span class="text-xs font-bold uppercase tracking-wider font-mono {isDark ? 'text-slate-200' : 'text-slate-900'}">
        {mode === 'main' ? 'Активные аварии L2' : 'Кластеры & Дома'}
      </span>
    </div>

    <span class="font-mono font-bold text-[9px] px-2 py-0.5 rounded-md border
      {mode === 'main' 
        ? (totalDown > 0 
            ? (isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300')
            : (isDark ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'))
        : (isDark ? 'bg-[#293a52] text-indigo-300 border-slate-600/60' : 'bg-slate-200/70 text-indigo-800 border-slate-300')}">
      {mode === 'main' ? `${totalDown} DOWN` : `${folders.length} ГРУПП`}
    </span>
  </div>

  <!-- СПИСОК -->
  <div class="flex-1 p-2 overflow-y-auto space-y-1.5 min-h-0 always-visible-scroll">
    {#if mode === 'main'}
      
      <!-- РЕЖИМ 1: НА ГЛАВНОМ ЭКРАНЕ -->
      {#if troubledFolders.length === 0}
        <div class="h-full flex flex-col items-center justify-center text-center p-4 font-mono text-xs">
          <div class="w-10 h-10 rounded-2xl flex items-center justify-center mb-2 {isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-100 text-emerald-700'}">✓</div>
          <span class="font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Все узлы в онлайне</span>
          <span class="text-[10px] text-slate-400 mt-0.5">Аварийных коммутаторов нет</span>
        </div>
      {:else}
        {#each troubledFolders as f}
          {@const isExpanded = expandedMap[f.name]}
          {@const downSwitches = f.switches ? f.switches.filter(s => !['working', 'host is alive'].includes((s.state || '').trim().toLowerCase())) : []}

          <!-- КАРТОЧКА ГРУППЫ -->
          <div class="rounded-xl border transition-all duration-150 overflow-hidden
            {isDark ? 'bg-[#223046] border-slate-700/70' : 'bg-white border-slate-200 shadow-2xs'}">
            
            <div 
              on:click={() => toggleExpand(f.name)}
              class="w-full p-2.5 text-left flex items-center justify-between gap-2 cursor-pointer transition-colors select-none
              {isDark ? 'hover:bg-[#283852]' : 'hover:bg-slate-50'}"
            >
              <div class="min-w-0 flex-1 pl-1">
                <div class="text-xs font-bold truncate {isDark ? 'text-slate-100' : 'text-slate-900'}" title={f.name}>
                  {f.name}
                </div>
                <div class="text-[9.5px] font-mono mt-0.5 flex items-center gap-1.5 {isDark ? 'text-slate-400' : 'text-slate-600 font-semibold'}">
                  <span>{f.total} узлов</span>
                  <span>·</span>
                  <span class="text-rose-600 font-bold">{f.total - f.down}/{f.total} онлайн</span>
                </div>
              </div>

              <div class="flex items-center gap-1.5 shrink-0 font-mono">
                <span class="px-1.5 py-0.2 rounded text-[9px] font-extrabold border
                  {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                  {f.down} DOWN
                </span>

                <div class="p-1 text-slate-400 transition-transform duration-150 {isExpanded ? 'rotate-180' : ''}">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            <!-- РАСКРЫТЫЙ СПИСОК (МЯГКИЙ СВЕТЛЫЙ ФОН #223046 БЕЗ ТЕМНЫХ ПРОВАЛОВ) -->
            {#if isExpanded && downSwitches.length > 0}
              <div transition:slide={{duration: 140, easing: cubicOut}} class="p-2 space-y-1.5 border-t max-h-60 overflow-y-auto always-visible-scroll {isDark ? 'border-slate-700/60 bg-[#223046]' : 'border-slate-100 bg-slate-50/60'}">
                {#each downSwitches as sw}
                  {@const descParts = sw.contract ? sw.contract.split('|') : []}
                  {@const address = descParts[0] ? descParts[0].trim() : '—'}

                  <div class="p-2.5 rounded-lg border flex items-center justify-between font-mono text-xs
                    {isDark ? 'bg-[#2a3a52] border-slate-600/70 text-slate-200' : 'bg-white border-slate-200 text-slate-900 shadow-2xs'}">
                    
                    <div class="min-w-0 pr-1.5">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold text-[10.5px] text-rose-500">{sw.id}</span>
                        <button on:click={(e) => copy(e, sw.id)} class="text-[9px] text-slate-400 hover:text-white cursor-pointer" title="Копировать IP">
                          {copied === sw.id ? '✓' : '⧉'}
                        </button>
                      </div>
                      <div class="font-sans text-[10.5px] font-medium truncate {isDark ? 'text-slate-300' : 'text-slate-700'} mt-0.5" title={address}>
                        {address}
                      </div>
                    </div>

                    <div class="shrink-0 font-mono text-[9px] font-bold">
                      {#if sw.los_time}
                        <span class="px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 border border-rose-300">
                          {formatLosTime(sw.los_time, currentUnixTime)}
                        </span>
                      {:else}
                        <span class="px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 border border-rose-300">DOWN</span>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}

          </div>
        {/each}
      {/if}

    {:else}

      <!-- РЕЖИМ 2: ВНУТРИ ГРУППЫ -->
      {#each folders as f}
        {@const isSelected = selectedGroupName === f.name}
        {@const isTroubled = f.down > 0}

        <button 
          on:click={() => dispatch('selectFolder', f.name)}
          class="w-full px-3 py-2.5 rounded-xl text-left transition-all duration-150 flex items-center justify-between gap-2 cursor-pointer border relative overflow-hidden
          {isSelected 
            ? (isDark ? 'bg-[#2a3a52] text-white font-bold border-indigo-500/50 shadow-sm' : 'bg-indigo-50 text-indigo-950 font-bold border-indigo-200 shadow-2xs') 
            : (isTroubled
                ? (isDark ? 'bg-[#223046] hover:bg-[#283852] border-slate-700/60 text-slate-200' : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-900')
                : (isDark ? 'text-slate-300 hover:text-white hover:bg-[#24334a]/60 border-transparent' : 'text-slate-700 hover:text-slate-900 hover:bg-slate-50 border-transparent'))}"
        >
          {#if isSelected}
            <div class="absolute left-0 top-1.5 bottom-1.5 w-1 bg-indigo-500 rounded-r-full"></div>
          {/if}

          <div class="min-w-0 flex-1 pl-1">
            <div class="text-xs font-bold truncate {isSelected ? (isDark ? 'text-white' : 'text-indigo-950 font-black') : (isDark ? 'text-slate-200' : 'text-slate-900')}" title={f.name}>
              {f.name}
            </div>
            <div class="text-[9.5px] font-mono mt-0.5 flex items-center gap-1.5 {isDark ? 'text-slate-400' : 'text-slate-600 font-semibold'}">
              <span>{f.total} узлов</span>
              <span>·</span>
              <span class="{f.health >= 90 ? 'text-emerald-500' : 'text-rose-600'} font-bold">{f.total - f.down}/{f.total}</span>
            </div>
          </div>

          {#if isTroubled}
            <span class="px-1.5 py-0.2 rounded text-[9px] font-mono font-extrabold border shrink-0
              {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
              {f.down} DOWN
            </span>
          {:else}
            <span class="text-[9px] font-mono font-bold text-emerald-500 shrink-0">✓ OK</span>
          {/if}
        </button>
      {/each}

    {/if}
  </div>
</div>