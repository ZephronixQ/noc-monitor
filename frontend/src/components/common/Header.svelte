<!-- frontend/src/components/common/Header.svelte -->
<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
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
  export let activeTab = 'dash';

  const dispatch = createEventDispatcher();

  let currentUser = { username: 'Оператор', role: 'Оператор NOC', is_staff: false };
  let isLogoutModalOpen = false;

  function loadUser() {
    if (typeof window !== 'undefined') {
      try {
        const u = localStorage.getItem('noc_user');
        if (u) currentUser = JSON.parse(u);
      } catch (e) {}
    }
  }

  onMount(loadUser);

  function confirmLogout() {
    localStorage.removeItem('noc_token');
    localStorage.removeItem('noc_token_expires_at');
    localStorage.removeItem('noc_user');
    window.location.reload();
  }

  const navTabs = [
    { 
      id: 'dash', 
      label: 'ОБЗОР',
      icon: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z'
    },
    { 
      id: 'olt', 
      label: 'GPON',
      icon: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z'
    },
    { 
      id: 'sw', 
      label: 'КОММУТАТОРЫ',
      icon: 'M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.75 5.1a1.5 1.5 0 011.2-.6h10.1a1.5 1.5 0 011.2.6l2.1 3.45a4.5 4.5 0 01.9 2.7'
    },
    { 
      id: 'night', 
      label: 'НОЧНОЙ АУДИТ',
      icon: 'M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z'
    }
  ];

  function handleForceUpdate() {
    forceUpdate();
    dispatch('forceUpdate');
  }
</script>

<header class="h-16 shrink-0 flex items-center justify-between px-6 sticky top-0 z-50 backdrop-blur-2xl border-b transition-all duration-300 font-sans select-none
  {isDark 
    ? 'bg-[#162032]/90 border-slate-700/60 shadow-[0_4px_30px_rgba(0,0,0,0.35)]' 
    : 'bg-white/90 border-slate-200/90 shadow-[0_4px_20px_rgba(0,0,0,0.02)]'}"
>
  <!-- ЛОГОТИП + ВКЛАДКИ -->
  <div class="flex items-center gap-8">
    <div class="flex items-center gap-3 cursor-pointer group" on:click={() => dispatch('tabChange', 'dash')}>
      <div class="w-8 h-8 rounded-xl flex items-center justify-center font-mono font-black text-xs text-white shadow-sm transition-transform duration-200 group-hover:scale-105 border
        {isDark ? 'bg-indigo-600 border-indigo-400/40 shadow-indigo-500/20' : 'bg-indigo-600 border-indigo-500 shadow-indigo-500/20'}">
        N
      </div>

      <div class="flex items-center gap-1.5 font-mono">
        <span class="font-extrabold text-sm tracking-tight {isDark ? 'text-white' : 'text-slate-900'}">
          NOC<span class="{isDark ? 'text-indigo-400' : 'text-indigo-600'}">MONITOR</span>
        </span>
        <span class="text-[9px] font-bold px-1.5 py-0.2 rounded border
          {isDark ? 'bg-[#1f2b40] text-slate-400 border-slate-700' : 'bg-slate-100 text-slate-600 border border-slate-200'}">
          ENTERPRISE
        </span>
      </div>
    </div>

    <nav class="flex items-center p-1 rounded-xl border transition-all
      {isDark ? 'bg-[#1e2a3e] border-slate-700/70' : 'bg-slate-100/90 border-slate-200/90'}">
      {#each navTabs as tab}
        {@const isActive = activeTab === tab.id}
        
        <button 
          on:click={() => dispatch('tabChange', tab.id)} 
          class="px-3.5 py-1.5 rounded-lg text-[11px] font-mono font-bold tracking-wider transition-all duration-150 cursor-pointer flex items-center gap-2
          {isActive 
            ? (isDark 
                ? 'bg-[#2d3f59] text-white shadow-xs border border-slate-600/80 font-black' 
                : 'bg-white text-slate-900 shadow-xs border border-slate-200 font-black') 
            : (isDark 
                ? 'text-slate-300 hover:text-white hover:bg-slate-700/40' 
                : 'text-slate-600 hover:text-slate-900')}"
        >
          <svg class="w-3.5 h-3.5 shrink-0 opacity-80" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d={tab.icon} />
          </svg>
          <span>{tab.label}</span>
        </button>
      {/each}
    </nav>
  </div>
  
  <!-- ПРАВАЯ ПАНЕЛЬ: ИНДИКАТОРЫ, АДМИНКА, ПРОФИЛЬ, ВЫХОД -->
  <div class="flex items-center gap-2.5 font-mono">
    
    <!-- СТАТУС WEBSOCKET -->
    <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[10px] font-bold tracking-wider shadow-2xs
      {isDark ? 'bg-[#24334a] border-slate-700 text-emerald-400' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}">
      <span class="relative flex h-2 w-2">
        {#if wsConnected}
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        {:else}
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
        {/if}
      </span>
      <span>{wsConnected ? 'ONLINE' : 'OFFLINE'}</span>
    </div>

    <!-- ТАЙМЕР ОПРОСА -->
    <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl border shadow-2xs
      {isDark ? 'bg-[#24334a] border-slate-700' : 'bg-slate-50 border-slate-200'}">
      <div class="text-[10px] font-bold text-slate-400">
        ОПРОС: <span class="{isDark ? 'text-white' : 'text-slate-900'} font-black tabular-nums">{timeToNextUpdate}</span>
      </div>

      <button 
        on:click={handleForceUpdate} 
        disabled={$isPollingActive || isUpdating}
        title="Принудительный опрос сети" 
        class="w-5 h-5 flex items-center justify-center rounded transition-all cursor-pointer
        {isDark ? 'hover:bg-slate-700 text-slate-400 hover:text-white' : 'hover:bg-slate-200 text-slate-500 hover:text-slate-900'}"
      >
        <svg class="w-3.5 h-3.5 {$isPollingActive || isUpdating ? 'animate-spin text-indigo-400' : ''}" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0H4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
      </button>
    </div>

    <!-- КНОПКА DJANGO ADMIN: АВТОМАТИЧЕСКИ РАБОТАЕТ НА БЕЛОМ IP ЧЕРЕЗ NGINX -->
    {#if currentUser.is_staff || currentUser.is_superuser}
      <a 
        href={typeof window !== 'undefined' && window.location.port === '5173' ? 'http://localhost:8000/admin/' : '/admin/'} 
        target="_blank"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[10px] font-bold transition-all shadow-xs active:scale-95
        {isDark ? 'bg-indigo-600/25 border-indigo-500/50 text-indigo-300 hover:bg-indigo-600/40 hover:text-white' : 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100'}"
        title="Панель управления коммутаторами и OLT"
      >
        <span>⚙️ Управление сетью</span>
        <span class="opacity-60 text-[9px]">↗</span>
      </a>
    {/if}

    <!-- ПОЛЬЗОВАТЕЛЬ И ВЫХОД -->
    <div class="flex items-center gap-2 pl-1">
      <div class="hidden sm:flex flex-col text-right leading-tight">
        <span class="text-xs font-black {isDark ? 'text-white' : 'text-slate-900'}">{currentUser.username}</span>
        <span class="text-[9px] font-semibold {isDark ? 'text-indigo-400' : 'text-indigo-600'}">{currentUser.role}</span>
      </div>

      <button 
        on:click={() => isLogoutModalOpen = true}
        class="w-9 h-9 rounded-xl border flex items-center justify-center transition-all cursor-pointer shadow-2xs active:scale-95
        {isDark 
          ? 'bg-[#24334a] hover:bg-rose-500/20 border-slate-700 text-slate-300 hover:text-rose-400 hover:border-rose-500/30' 
          : 'bg-white hover:bg-rose-50 border-slate-200 text-slate-600 hover:text-rose-600 hover:border-rose-200'}"
        title="Завершить сессию оператора"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
        </svg>
      </button>
    </div>

    <!-- ПЕРЕКЛЮЧАТЕЛЬ ТЕМЫ -->
    <button 
      on:click={() => dispatch('toggleTheme')} 
      class="w-9 h-9 rounded-xl border flex items-center justify-center transition-all cursor-pointer shadow-2xs
      {isDark 
        ? 'bg-[#24334a] border-slate-700 text-amber-400 hover:bg-slate-700' 
        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900'}"
      title={isDark ? "Светлая тема" : "Тёмная тема"}
    >
      {#if isDark}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
        </svg>
      {:else}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
        </svg>
      {/if}
    </button>

  </div>
</header>

<!-- МОДАЛЬНОЕ ОКНО ПОДТВЕРЖДЕНИЯ ВЫХОДА -->
{#if isLogoutModalOpen}
  <div 
    class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-md font-sans select-none"
    in:fade={{ duration: 120 }}
  >
    <div 
      class="w-full max-w-sm p-6 rounded-3xl border shadow-2xl transition-all overflow-hidden relative
      {isDark ? 'bg-[#1b2537] border-slate-700/80 text-slate-100 shadow-black/80' : 'bg-white border-slate-200 text-slate-900'}"
      in:scale={{ start: 0.95, duration: 150 }}
    >
      <div class="w-11 h-11 mx-auto mb-3.5 rounded-2xl flex items-center justify-center text-lg border
        {isDark ? 'bg-rose-500/15 border-rose-500/30 text-rose-400' : 'bg-rose-50 border-rose-200 text-rose-600'}">
        🚪
      </div>

      <h3 class="text-center font-bold text-sm {isDark ? 'text-white' : 'text-slate-900'}">
        Завершить сессию?
      </h3>

      <p class="text-center text-xs text-slate-400 mt-1 font-mono leading-relaxed">
        Вы уверены, что хотите выйти из аккаунта <strong class="{isDark ? 'text-slate-200' : 'text-slate-800'} font-bold">[{currentUser.username}]</strong>?
      </p>

      <div class="grid grid-cols-2 gap-2.5 mt-5 font-mono text-xs font-bold">
        <button 
          on:click={() => isLogoutModalOpen = false}
          class="py-2.5 rounded-xl border transition-all cursor-pointer active:scale-95
          {isDark ? 'bg-[#24334a] hover:bg-slate-700 border-slate-600/80 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700'}"
        >
          Отмена
        </button>

        <button 
          on:click={confirmLogout}
          class="py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white transition-all cursor-pointer shadow-md shadow-rose-600/25 active:scale-95"
        >
          Да, выйти
        </button>
      </div>
    </div>
  </div>
{/if}