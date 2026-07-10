<!-- frontend\src\components\Header.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let wsConnected = false;
  export let timeToNextUpdate = "00:00";
  export let isUpdating = false;
  export let activeTab = 'dash';

  const dispatch = createEventDispatcher();
</script>

<header class="h-16 shrink-0 flex items-center justify-between px-8 sticky top-0 z-40 backdrop-blur-xl border-b transition-colors duration-300 
  {isDark ? 'bg-[#161f33]/90 border-slate-800 shadow-[0_1px_10px_rgba(0,0,0,0.2)]' : 'bg-white/80 border-slate-200/80 shadow-[0_1px_10px_rgba(0,0,0,0.02)]'}"
>
  
  <div class="flex items-center gap-10">
    <div class="flex items-center gap-3 select-none">
      <div class="w-9 h-9 rounded-xl flex items-center justify-center font-black text-white bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 shadow-[0_4px_20px_rgba(99,102,241,0.45)] text-sm tracking-wider">N</div>
      <span class="font-bold tracking-wider text-base {isDark ? 'text-white' : 'text-slate-900'}">
        NOC <span class="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent font-extrabold">MONITOR</span>
      </span>
    </div>
    
    <nav class="flex gap-1 p-1 rounded-full transition-all border {isDark ? 'bg-black/20 border-slate-800' : 'bg-slate-100/80 border-slate-200'}">
      <button on:click={() => dispatch('tabChange', 'dash')} 
        class="px-5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 
        {activeTab === 'dash' 
          ? 'bg-indigo-500 text-white shadow-[0_4px_12px_rgba(99,102,241,0.3)]' 
          : 'text-slate-400 hover:text-indigo-400'}"
      >
        ОБЗОР
      </button>
      <button on:click={() => dispatch('tabChange', 'olt')} 
        class="px-5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 
        {activeTab === 'olt' 
          ? 'bg-indigo-500 text-white shadow-[0_4px_12px_rgba(99,102,241,0.3)]' 
          : 'text-slate-400 hover:text-indigo-400'}"
      >
        GPON
      </button>
      <button on:click={() => dispatch('tabChange', 'sw')} 
        class="px-5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 
        {activeTab === 'sw' 
          ? 'bg-indigo-500 text-white shadow-[0_4px_12px_rgba(99,102,241,0.3)]' 
          : 'text-slate-400 hover:text-indigo-400'}"
      >
        КОММУТАТОРЫ
      </button>
      <button on:click={() => dispatch('tabChange', 'night')} 
        class="px-5 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 
        {activeTab === 'night' 
          ? 'bg-indigo-500 text-white shadow-[0_4px_12px_rgba(99,102,241,0.3)]' 
          : 'text-slate-400 hover:text-indigo-400'}"
      >
        НОЧНОЙ АУДИТ
      </button>
    </nav>
  </div>
  
  <div class="flex items-center gap-5 relative">
    
    <!-- Переключатель цветовой темы -->
    <button on:click={() => dispatch('toggleTheme')} 
      class="w-9 h-9 rounded-xl flex items-center justify-center border transition-all duration-250
      {isDark ? 'bg-white/[0.03] border-slate-700 text-amber-400 hover:bg-white/[0.08]' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'}"
    >
      {#if isDark}
        <svg class="w-4.5 h-4.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
        </svg>
      {:else}
        <svg class="w-4.5 h-4.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
        </svg>
      {/if}
    </button>
    
    <div class="flex items-center gap-4 border-l pl-4 {isDark ? 'border-slate-800' : 'border-slate-200'}">
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl border {isDark ? 'bg-black/20 border-slate-800' : 'bg-slate-50 border-slate-100'}" title={wsConnected ? 'Connected' : 'Disconnected'}>
        <span class="relative flex h-2 w-2">
          {#if wsConnected}
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          {:else}
            <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
          {/if}
        </span>
        <span class="text-[10px] font-bold tracking-wider {wsConnected ? 'text-emerald-500' : 'text-rose-500'}">
          {wsConnected ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
      
      <div class="flex items-center rounded-xl border overflow-hidden {isDark ? 'bg-[#161f33] border-slate-800' : 'bg-slate-50 border-slate-200'}">
        <div class="px-3 py-1.5 font-mono text-[10px] font-bold {isDark ? 'text-slate-400' : 'text-slate-500'}">
          ОПРОС: <span class="text-indigo-400">{timeToNextUpdate}</span>
        </div>
        <button on:click={() => dispatch('forceUpdate')} 
          disabled={isUpdating}
          title="Принудительный опрос" 
          class="w-8 h-8 flex items-center justify-center border-l transition-all duration-200
          {isDark ? 'border-slate-800 hover:bg-white/[0.04] text-slate-400 hover:text-white' : 'border-slate-200 hover:bg-slate-100 text-slate-500 hover:text-indigo-600'}"
        >
          <svg class="w-3.5 h-3.5 {isUpdating ? 'animate-spin' : ''}" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
        </button>
      </div>

    </div>
  </div>
</header>