<!-- frontend/src/components/admin/AdminHeader.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  export let isDark = false;
  
  const dispatch = createEventDispatcher();

  function goToMain() {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  }

  function handleAdminLogout() {
    localStorage.removeItem('noc_admin_token');
    window.location.reload();
  }
</script>

<header class="h-16 shrink-0 flex items-center justify-between px-8 sticky top-0 z-40 backdrop-blur-xl border-b transition-colors duration-300 font-sans
  {isDark ? 'bg-[#1c283e]/95 border-slate-700/70 shadow-[0_4px_20px_rgba(0,0,0,0.4)]' : 'bg-white/95 border-slate-200/80 shadow-[0_4px_20px_rgba(99,102,241,0.03)]'}"
>
  <!-- Логотип админки -->
  <div class="flex items-center gap-3 select-none">
    <div class="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-500 via-purple-500 to-indigo-500 shadow-md font-black text-white text-sm">
      🛡️
    </div>
    <div class="flex flex-col">
      <span class="font-extrabold tracking-wider text-sm leading-none {isDark ? 'text-white' : 'text-slate-900'}">
        NOC <span class="text-rose-500 font-extrabold">SECURITY CENTER</span>
      </span>
      <span class="text-[9px] font-mono font-bold text-slate-300 mt-1 uppercase tracking-widest">
        Центр управления сессиями и безопасностью (/sessions)
      </span>
    </div>
  </div>

  <!-- Кнопки управления -->
  <div class="flex items-center gap-3 select-none">
    <button 
      on:click={goToMain}
      class="px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all duration-200 cursor-pointer flex items-center gap-2 border shadow-2xs
      {isDark ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/25' : 'bg-indigo-50 text-indigo-700 border-indigo-100 hover:bg-indigo-100'}"
    >
      <span>← Вернуться к мониторингу</span>
    </button>

    <div class="w-[1px] h-4 {isDark ? 'bg-slate-700/80' : 'bg-slate-200'}"></div>

    <!-- Переключатель Темы -->
    <button 
      on:click={() => dispatch('toggleTheme')} 
      class="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer
      {isDark ? 'text-amber-400 hover:bg-slate-800' : 'text-slate-600 hover:bg-slate-100'}"
      title={isDark ? "Светлая тема" : "Тёмная тема"}
    >
      {#if isDark}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
      {:else}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
      {/if}
    </button>

    <button 
      on:click={handleAdminLogout}
      class="px-3.5 py-2 rounded-xl text-xs font-mono font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 border border-rose-500/30 bg-rose-500/10 text-rose-400 hover:bg-rose-500 hover:text-white"
      title="Закрыть доступ к админке"
    >
      <span>🔒 Выйти</span>
    </button>
  </div>
</header>