<!-- frontend/src/components/gpon/GponToolbar.svelte -->
<script>
  import { createEventDispatcher, onMount } from 'svelte';
  const dispatch = createEventDispatcher();

  export let isDark = false;
  export let totalOnus = 0;
  export let onlineOnus = 0;
  export let losCount = 0;
  export let losiCount = 0;
  export let searchQuery = '';
  export let globalLosFilter = false;
  export let globalLosiFilter = false;
  export let selectedOltIp = null;
  export let portSortField = 'default';
  export let portSortDirection = 'desc';

  let searchInputEl;

  $: downCount = totalOnus - onlineOnus;
  $: healthPercent = totalOnus > 0 ? ((onlineOnus / totalOnus) * 100).toFixed(1) : '100.0';

  function handleInput(e) {
    let val = e.target.value;
    if (val.includes(' ')) {
      val = val.replace(/\s+/g, '/');
      val = val.replace(/\/+/g, '/');
    }
    searchQuery = val;
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape') {
      if (searchQuery) {
        searchQuery = '';
      } else if (selectedOltIp) {
        dispatch('backToGrid');
      }
      return;
    }

    if (
      !e.ctrlKey && !e.metaKey && !e.altKey &&
      e.key.length === 1 &&
      document.activeElement !== searchInputEl &&
      !['input', 'textarea', 'select'].includes(document.activeElement?.tagName?.toLowerCase())
    ) {
      if (searchInputEl) {
        searchInputEl.focus();
      }
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });
</script>

<div class="p-3.5 rounded-2xl border transition-all duration-300 flex flex-col lg:flex-row items-center justify-between gap-4 shrink-0 select-none shadow-sm font-sans
  {isDark ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200 shadow-xl' : 'bg-white border-slate-200/90 text-slate-800'}"
>
  <!-- ЛЕВАЯ ЧАСТЬ: ВЫВЕРЕННЫЙ ХАБ ТЕЛЕМЕТРИИ GPON -->
  <div class="flex items-center gap-5 min-w-0 w-full lg:w-auto">
    
    {#if selectedOltIp}
      <button 
        on:click={() => dispatch('backToGrid')}
        class="h-10 px-3.5 rounded-xl border font-mono text-xs font-bold transition-all flex items-center gap-2 cursor-pointer active:scale-95 shrink-0 shadow-xs
        {isDark ? 'bg-[#24334a] hover:bg-[#2d3f59] border-slate-600 text-indigo-300' : 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-indigo-900'}"
      >
        <span>←</span>
        <span>К станциям <kbd class="opacity-60 text-[10px] font-normal ml-1">ESC</kbd></span>
      </button>
      <span class="text-slate-400 font-mono hidden sm:inline">/</span>
    {/if}

    <div class="flex items-center gap-5 font-mono">
      
      <!-- ЧИСТЫЙ ПРОЦЕНТ И ПОДПИСЬ БЕЗ ДУБЛЯ 3 LOS -->
      <div class="flex flex-col">
        <span class="text-2xl font-black {isDark ? 'text-white' : 'text-slate-900'} tracking-tight leading-none">
          {healthPercent}<span class="text-xs font-bold text-slate-400">%</span>
        </span>
        <div class="text-[9.5px] font-bold text-slate-400 uppercase tracking-wider mt-1">GPON Fleet Health</div>
      </div>

      <!-- МОДУЛЬ ШКАЛЫ + UP / DOWN + LOS / LOSi -->
      <div class="p-1 rounded-xl border flex items-center gap-2.5 {isDark ? 'bg-[#182335] border-slate-700/80' : 'bg-slate-50 border-slate-200'}">
        
        <!-- ШКАЛА ДОСТУПНОСТИ -->
        <div class="w-32 xl:w-44 h-2 rounded-md overflow-hidden flex {isDark ? 'bg-slate-800 border border-slate-700' : 'bg-slate-200 border border-slate-300'} p-[1px]">
          <div 
            class="h-full rounded-xs transition-all duration-700 ease-out {isDark ? 'bg-emerald-500' : 'bg-emerald-600'}" 
            style="width: {healthPercent}%" 
            title="Онлайн: {onlineOnus}">
          </div>
          {#if downCount > 0}
            <div 
              class="h-full rounded-xs transition-all duration-700 ease-out bg-rose-500 ml-0.5 animate-pulse" 
              style="width: {100 - Number(healthPercent)}%" 
              title="Аварии: {downCount}">
            </div>
          {/if}
        </div>

        <!-- ЧЕТКИЕ БЕЙДЖИ: UP, DOWN, LOS, LOSi -->
        <div class="flex items-center gap-1.5 text-[11px] font-bold pr-1">
          <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}">
            {onlineOnus} UP
          </span>
          
          <span class="px-2 py-0.5 rounded-md {downCount > 0 ? (isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300') : (isDark ? 'bg-slate-800 text-slate-500' : 'bg-slate-100 text-slate-400')}">
            {downCount} DOWN
          </span>

          {#if losCount > 0}
            <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-rose-500/25 text-rose-300 border border-rose-500/40' : 'bg-rose-600 text-white shadow-2xs'}">
              {losCount} LOS
            </span>
          {/if}

          {#if losiCount > 0}
            <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-purple-500/25 text-purple-300 border border-purple-500/40' : 'bg-purple-600 text-white shadow-2xs'}">
              {losiCount} LOSi
            </span>
          {/if}
        </div>

      </div>

    </div>
  </div>

  <!-- ПРАВАЯ ЧАСТЬ: ПОИСК (ПРОБЕЛ = /) + СОРТИРОВКА + ФИЛЬТРЫ -->
  <div class="flex flex-wrap items-center gap-2.5 w-full lg:w-auto justify-end flex-1 max-w-xl">
    
    <div class="relative flex-1 min-w-[200px]">
      <div class="relative flex items-center h-10 rounded-xl border transition-all duration-200 overflow-hidden shadow-xs
        {isDark ? 'bg-[#182335] border-slate-700/80 text-slate-100 focus-within:border-indigo-500' : 'bg-slate-50 border-slate-300 text-slate-900 focus-within:border-indigo-500 shadow-2xs'}">
        <div class="pl-3.5 pr-2 text-slate-400">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>
        <input 
          bind:this={searchInputEl}
          type="text" 
          value={searchQuery}
          on:input={handleInput}
          placeholder="Плата (1 15 2) или договор..." 
          class="w-full bg-transparent h-full pr-3 text-xs font-semibold outline-none placeholder:text-slate-400 font-sans tracking-wide" 
        />
        
        <div class="pr-2.5 flex items-center gap-1.5">
          {#if searchQuery}
            <button on:click={() => searchQuery = ''} class="text-slate-400 hover:text-white text-xs font-mono font-bold cursor-pointer">✕</button>
          {:else}
            <kbd class="hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono font-bold rounded-md border
              {isDark ? 'bg-[#24334a] text-slate-400 border-slate-600/60' : 'bg-slate-200/80 text-slate-600 border-slate-300'}">
              /
            </kbd>
          {/if}
        </div>
      </div>
    </div>

    {#if selectedOltIp}
      <div class="flex items-center p-1 h-10 rounded-xl border font-mono text-[10px] font-bold select-none
        {isDark ? 'bg-[#182335] border-slate-700/80' : 'bg-slate-100 border-slate-200'}">
        
        <button on:click={() => dispatch('changeSort', 'default')}
          class="px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1
          {portSortField === 'default' 
            ? (isDark ? 'bg-[#2d3f59] text-white shadow-xs font-bold' : 'bg-white text-slate-900 shadow-xs font-bold border border-slate-200') 
            : (isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900')}"
        >
          <span>По авариям</span>
          {#if portSortField === 'default'}
            <span class="text-[9px] text-indigo-400">{portSortDirection === 'desc' ? '▼' : '▲'}</span>
          {/if}
        </button>

        <button on:click={() => dispatch('changeSort', 'name')}
          class="px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1
          {portSortField === 'name' 
            ? (isDark ? 'bg-[#2d3f59] text-white shadow-xs font-bold' : 'bg-white text-slate-900 shadow-xs font-bold border border-slate-200') 
            : (isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900')}"
        >
          <span>По плате</span>
          {#if portSortField === 'name'}
            <span class="text-[9px] text-indigo-400">{portSortDirection === 'asc' ? '▲' : '▼'}</span>
          {/if}
        </button>
      </div>
    {/if}

    <button 
      on:click={() => dispatch('toggleLos')} 
      class="h-10 rounded-xl px-3 font-mono font-bold text-xs tracking-wider uppercase transition-all duration-150 flex items-center gap-1.5 shrink-0 border cursor-pointer active:scale-95 shadow-xs
      {globalLosFilter 
        ? (isDark ? 'bg-rose-500/25 text-rose-300 border-rose-500/40 shadow-sm' : 'bg-rose-600 text-white border-rose-600') 
        : (isDark ? 'bg-[#182335] text-slate-300 border-slate-700 hover:border-slate-500 hover:text-white' : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400')}"
    >
      <span class="w-2 h-2 rounded-full shrink-0 {globalLosFilter ? (isDark ? 'bg-rose-400' : 'bg-white') : 'bg-rose-500'}"></span>
      <span>LOS</span>
    </button>

    <button 
      on:click={() => dispatch('toggleLosi')} 
      class="h-10 rounded-xl px-3 font-mono font-bold text-xs tracking-wider uppercase transition-all duration-150 flex items-center gap-1.5 shrink-0 border cursor-pointer active:scale-95 shadow-xs
      {globalLosiFilter 
        ? (isDark ? 'bg-purple-500/25 text-purple-300 border-purple-500/40 shadow-sm' : 'bg-purple-600 text-white border-purple-600') 
        : (isDark ? 'bg-[#182335] text-slate-300 border-slate-700 hover:border-slate-500 hover:text-white' : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400')}"
    >
      <span class="w-2 h-2 rounded-full shrink-0 {globalLosiFilter ? (isDark ? 'bg-purple-400' : 'bg-white') : 'bg-purple-500'}"></span>
      <span>LOSi</span>
    </button>
  </div>

</div>