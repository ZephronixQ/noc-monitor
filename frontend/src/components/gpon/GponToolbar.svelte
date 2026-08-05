<!-- frontend/src/components/gpon/GponToolbar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let searchQuery = '';
  export let globalLosFilter = false;
  export let globalLosiFilter = false;
  export let portSortField = 'default';
  export let portSortDirection = 'desc';

  const dispatch = createEventDispatcher();
</script>

<div class="flex gap-3 shrink-0 select-none items-center pt-2 mt-1 pb-1 font-sans">
  
  <div class="relative flex-1 group">
    <div class="absolute -inset-[2px] rounded-2xl animate-rainbow"></div>

    <!-- Обновленный мягкий фон поисковика (#1c273e) -->
    <div class="relative flex items-center h-12 rounded-[13.5px] overflow-hidden transition-colors duration-200 z-10
      {isDark ? 'bg-[#1c273e] text-slate-100' : 'bg-white text-slate-900'}"
    >
      <div class="pl-4 pr-2 flex items-center shrink-0 pointer-events-none text-purple-400">
        <svg class="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
      </div>

      <input 
        type="text" 
        bind:value={searchQuery} 
        placeholder="Поиск по интерфейсу или договору ONU..." 
        class="w-full bg-transparent h-full pr-4 text-xs font-semibold outline-none placeholder-slate-400 font-sans tracking-wide" 
      />
    </div>
  </div>

  <div class="flex items-center gap-1 p-1 h-12 rounded-2xl border shrink-0 font-mono text-[10px] font-black shadow-2xs select-none
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    <button on:click={() => dispatch('changeSort', 'default')}
      class="px-3.5 py-2 rounded-xl transition-all duration-150 cursor-pointer flex items-center gap-1
      {portSortField === 'default' 
        ? (isDark ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-xs' : 'bg-indigo-50 text-indigo-950 border border-indigo-200 shadow-xs') 
        : (isDark ? 'text-slate-300 hover:text-white' : 'text-slate-600 hover:text-slate-900')}"
    >
      <span>По авариям</span>
      {#if portSortField === 'default'}
        <span class="text-[9px] text-indigo-400">{portSortDirection === 'desc' ? '▼' : '▲'}</span>
      {/if}
    </button>

    <button on:click={() => dispatch('changeSort', 'name')}
      class="px-3.5 py-2 rounded-xl transition-all duration-150 cursor-pointer flex items-center gap-1
      {portSortField === 'name' 
        ? (isDark ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-xs' : 'bg-indigo-50 text-indigo-950 border border-indigo-200 shadow-xs') 
        : (isDark ? 'text-slate-300 hover:text-white' : 'text-slate-600 hover:text-slate-900')}"
    >
      <span>По плате</span>
      {#if portSortField === 'name'}
        <span class="text-[9px] text-indigo-400">{portSortDirection === 'asc' ? '▲' : '▼'}</span>
      {/if}
    </button>
  </div>

  <button 
    on:click={() => dispatch('toggleLos')} 
    class="relative h-12 rounded-2xl px-5 font-mono font-black text-xs tracking-wider uppercase transition-all duration-200 flex items-center gap-2 shrink-0 border cursor-pointer select-none active:scale-95 shadow-none
    {globalLosFilter 
      ? 'bg-rose-500 text-white border-rose-600' 
      : (isDark 
          ? 'bg-[#1e2a40] text-slate-300 border-slate-700/70 hover:border-slate-600 hover:text-white' 
          : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:text-slate-900')}"
  >
    <span class="w-2 h-2 rounded-full shrink-0 {globalLosFilter ? 'bg-white' : 'bg-rose-500'}"></span>
    <span>ТОЛЬКО LOS</span>
  </button>

  <button 
    on:click={() => dispatch('toggleLosi')} 
    class="relative h-12 rounded-2xl px-5 font-mono font-black text-xs tracking-wider uppercase transition-all duration-200 flex items-center gap-2 shrink-0 border cursor-pointer select-none active:scale-95 shadow-none
    {globalLosiFilter 
      ? 'bg-fuchsia-600 text-white border-fuchsia-700' 
      : (isDark 
          ? 'bg-[#1e2a40] text-slate-300 border-slate-700/70 hover:border-slate-600 hover:text-white' 
          : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:text-slate-900')}"
  >
    <span class="w-2 h-2 rounded-full shrink-0 {globalLosiFilter ? 'bg-white' : 'bg-fuchsia-500'}"></span>
    <span>ТОЛЬКО LOSi</span>
  </button>

</div>

<style>
  @keyframes rainbowAnimation {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  .animate-rainbow {
    background-size: 300% 300%;
    background-image: linear-gradient(
      115deg,
      #6366f1, #a855f7, #ec4899, #f43f5e, #ff7000, #eab308, #10b981, #06b6d4, #6366f1
    );
    animation: rainbowAnimation 8s ease infinite;
  }
</style>