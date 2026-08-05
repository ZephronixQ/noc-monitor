<!-- frontend/src/components/common/Header.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { fade } from 'svelte/transition';
  import { 
    isPollingActive, 
    pollingProgress, 
    pollingStatusText, 
    pollingDetectedStats, 
    forceUpdate 
  } from '../../stores/networkStore.js';

  export let isDark = false;
  export let wsConnected = false;
  export let timeToNextUpdate = "00:00";
  export let isUpdating = false;
  export let activeTab = 'sw';

  const dispatch = createEventDispatcher();

  const navTabs = [
    { id: 'dash', label: 'ОБЗОР' },
    { id: 'olt', label: 'GPON' },
    { id: 'sw', label: 'КОММУТАТОРЫ' },
    { id: 'night', label: 'НОЧНОЙ АУДИТ' }
  ];

  function handleForceUpdate() {
    forceUpdate();
    dispatch('forceUpdate');
  }
</script>

<header class="h-16 shrink-0 flex items-center justify-between px-8 sticky top-0 z-40 backdrop-blur-xl border-b transition-colors duration-300 font-sans
  {isDark ? 'bg-[#1c283e]/90 border-slate-700/70 shadow-[0_4px_20px_rgba(0,0,0,0.3)]' : 'bg-white/90 border-slate-200/80 shadow-[0_4px_20px_rgba(99,102,241,0.03)]'}"
>
  <div class="flex items-center gap-8">
    <!-- Логотип -->
    <div class="flex items-center gap-3 select-none cursor-pointer group" on:click={() => dispatch('tabChange', 'dash')}>
      <div class="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 shadow-[0_0_15px_rgba(168,85,247,0.45)] font-black text-white text-sm tracking-wider group-hover:scale-105 transition-transform">
        N
      </div>
      <div class="flex flex-col">
        <div class="flex items-center gap-2">
          <span class="font-black tracking-wider text-sm leading-none {isDark ? 'text-white' : 'text-slate-900'}">
            NOC <span class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent font-extrabold">MONITOR</span>
          </span>
        </div>
        <div class="flex items-center gap-1.5 mt-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-[8px] font-mono font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-widest uppercase">
            ENTERPRISE 2026
          </span>
        </div>
      </div>
    </div>
    
    <!-- Переключатель вкладок -->
    <nav class="flex gap-1.5 p-1.5 rounded-2xl border transition-all duration-300 select-none shadow-inner
      {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-slate-100/90 border-slate-200/90'}"
    >
      {#each navTabs as tab}
        {@const isActive = activeTab === tab.id}
        
        <button 
          on:click={() => dispatch('tabChange', tab.id)} 
          class="relative px-5 py-2 rounded-xl text-xs font-mono font-bold tracking-wider transition-all duration-200 cursor-pointer flex items-center gap-2 overflow-hidden
          {isActive 
            ? (isDark 
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-2xs' 
                : 'bg-white text-indigo-600 border border-slate-200/80 shadow-xs') 
            : (isDark 
                ? 'text-slate-300 hover:text-white hover:bg-slate-700/50 border border-transparent' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/80 border border-transparent')}"
        >
          {#if isActive}
            <div class="absolute bottom-0 left-2 right-2 h-[2px] bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full"></div>
          {/if}

          <span>{tab.label}</span>
        </button>
      {/each}
    </nav>
  </div>
  
  <div class="flex items-center gap-3 select-none">
    {#if $isPollingActive}
      <div transition:fade={{ duration: 150 }}
        class="flex items-center gap-3 px-3.5 py-1.5 rounded-2xl border font-mono text-[10px] font-bold shadow-md
        {isDark ? 'bg-indigo-950/60 border-indigo-500/40 text-indigo-200' : 'bg-indigo-50 border-indigo-200 text-indigo-950'}"
      >
        <div class="flex items-center gap-2">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
          <span class="text-indigo-500 dark:text-indigo-400 font-extrabold">{$pollingProgress}%</span>
        </div>

        <span class="truncate max-w-[160px] font-sans text-[11px] font-medium">{$pollingStatusText}</span>

        {#if $pollingDetectedStats.los > 0 || $pollingDetectedStats.losi > 0}
          <div class="flex items-center gap-1 font-mono text-[8.5px] font-bold">
            <span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">{$pollingDetectedStats.los} LOS</span>
            <span class="px-1.5 py-0.5 rounded bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30">{$pollingDetectedStats.losi} LOSi</span>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Виджет статуса сети и таймера -->
    <div class="flex items-center gap-2 select-none p-1 rounded-2xl border shadow-2xs
      {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-slate-50 border-slate-200/90'}"
    >
      <div class="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-[10px] font-mono font-bold tracking-wider">
        <span class="relative flex h-2 w-2">
          {#if wsConnected}
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.9)]"></span>
          {:else}
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.9)]"></span>
          {/if}
        </span>
        <span class={wsConnected ? 'text-emerald-500 dark:text-emerald-400' : 'text-rose-500'}>
          {wsConnected ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>

      <div class="w-[1px] h-4 {isDark ? 'bg-slate-700/80' : 'bg-slate-200'}"></div>

      <div class="flex items-center gap-2 px-2 py-1">
        <div class="font-mono text-[10px] font-bold {isDark ? 'text-slate-200' : 'text-slate-600'}">
          ОПРОС: <span class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent font-extrabold">{timeToNextUpdate}</span>
        </div>
        
        <button 
          on:click={handleForceUpdate} 
          disabled={$isPollingActive || isUpdating}
          title="Принудительный опрос сети" 
          class="w-7 h-7 flex items-center justify-center rounded-lg transition-all duration-200 cursor-pointer
          {isDark 
            ? 'hover:bg-slate-700/80 text-slate-300 hover:text-white disabled:opacity-40' 
            : 'hover:bg-slate-200/80 text-slate-500 hover:text-indigo-600 disabled:opacity-40'}"
        >
          <svg class="w-3.5 h-3.5 {$isPollingActive || isUpdating ? 'animate-spin text-indigo-400' : ''}" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0H4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
        </button>
      </div>

      <div class="w-[1px] h-4 {isDark ? 'bg-slate-700/80' : 'bg-slate-200'}"></div>

      <button 
        on:click={() => dispatch('toggleTheme')} 
        class="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer
        {isDark 
          ? 'text-amber-400 hover:bg-slate-700/80' 
          : 'text-slate-600 hover:bg-slate-200/80 hover:text-slate-900'}"
        title={isDark ? "Светлая тема" : "Тёмная тема"}
      >
        {#if isDark}
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
        {:else}
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
        {/if}
      </button>

    </div>
  </div>
</header>