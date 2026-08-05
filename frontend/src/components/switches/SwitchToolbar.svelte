<!-- frontend/src/components/switches/SwitchToolbar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let switchSearchQuery = '';
  export let globalSwLosFilter = false;

  const dispatch = createEventDispatcher();
</script>

<div class="flex gap-3 shrink-0 select-none items-center pt-2 mt-1 pb-1">
  
  <!-- Радужный поисковый блок -->
  <div class="relative flex-1 group">
    <div class="absolute -inset-[2px] rounded-2xl animate-rainbow"></div>

    <div class="relative flex items-center h-12 rounded-[13.5px] overflow-hidden transition-colors duration-200 z-10
      {isDark ? 'bg-slate-800 text-slate-100' : 'bg-white text-slate-900'}"
    >
      <div class="pl-4 pr-2 flex items-center shrink-0 pointer-events-none text-purple-500">
        <svg class="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
      </div>

      <input 
        type="text" 
        bind:value={switchSearchQuery} 
        placeholder="Поиск по IP, адресу или модели..." 
        class="w-full bg-transparent h-full pr-4 text-xs font-semibold outline-none placeholder-slate-400 font-sans tracking-wide" 
      />
    </div>
  </div>

  <!-- КНОПКА «ТОЛЬКО LOS» (УВЕЛИЧЕНА ВЫСОТА ДО h-[52px] И ОТСТУПЫ ДО px-7) -->
  <button 
    on:click={() => globalSwLosFilter = !globalSwLosFilter} 
    class="relative h-[52px] rounded-2xl px-7 font-mono font-bold text-xs tracking-wider uppercase transition-all duration-200 flex items-center gap-2.5 shrink-0 border cursor-pointer select-none active:scale-95 shadow-xs
    {globalSwLosFilter 
      ? 'bg-rose-500 text-white border-rose-600 shadow-rose-500/20' 
      : (isDark 
          ? 'bg-slate-800 text-slate-300 border-slate-700/80 hover:border-slate-600 hover:text-white' 
          : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:text-slate-900')}"
  >
    <span class="w-2.5 h-2.5 rounded-full shrink-0 transition-colors {globalSwLosFilter ? 'bg-white' : 'bg-rose-500'}"></span>
    <span>ТОЛЬКО LOS</span>
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