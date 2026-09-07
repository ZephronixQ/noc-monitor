<!-- frontend/src/components/common/LoginModal.svelte -->
<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { BACKEND_URL } from '../../stores/networkStore.js';

  export let isDark = false;
  const dispatch = createEventDispatcher();

  let username = '';
  let password = '';
  let showPassword = false;
  let errorMsg = '';
  let isLoading = false;
  let usernameInputEl;

  // 1 год в миллисекундах (365 дней)
  const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;

  onMount(() => {
    if (usernameInputEl) usernameInputEl.focus();
  });

  async function handleLogin() {
    if (!username || !password) {
      errorMsg = 'Заполните логин и пароль';
      return;
    }

    isLoading = true;
    errorMsg = '';

    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username: username.trim(), 
          password 
        })
      });

      const data = await res.json();

      if (res.ok) {
        // Фиксируем срок сессии ровно на 1 год вперед без плавающего автопродления
        const expiresAt = Date.now() + ONE_YEAR_MS;

        localStorage.setItem('noc_token', data.token || 'authenticated_session');
        localStorage.setItem('noc_token_expires_at', String(expiresAt));
        if (data.user) {
          localStorage.setItem('noc_user', JSON.stringify(data.user));
        }

        dispatch('authenticated');
      } else {
        errorMsg = data.detail || 'Неверный логин или пароль';
      }
    } catch (e) {
      errorMsg = 'Сервер мониторинга недоступен';
    } finally {
      isLoading = false;
    }
  }
</script>

<div 
  class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md font-sans select-none"
  in:fade={{ duration: 150 }}
>
  <div 
    class="w-full max-w-sm p-7 rounded-3xl border transition-all shadow-2xl overflow-hidden relative
    {isDark ? 'bg-[#1b2537] border-slate-700/70 text-slate-100 shadow-black/80' : 'bg-white border-slate-200 text-slate-900 shadow-2xl'}"
    in:scale={{ start: 0.95, duration: 180 }}
  >
    <!-- АКЦЕНТНАЯ СВЕТОВАЯ ФАСКА -->
    <div class="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>

    <!-- ШАПКА АВТОРИЗАЦИИ -->
    <div class="text-center mb-6">
      <div class="w-10 h-10 mx-auto mb-3 rounded-2xl flex items-center justify-center font-mono font-black text-xs text-white border shadow-md
        {isDark ? 'bg-indigo-600 border-indigo-400/40 shadow-indigo-500/20' : 'bg-indigo-600 border-indigo-500 shadow-indigo-500/20'}">
        N
      </div>

      <h2 class="text-base font-black tracking-tight font-mono {isDark ? 'text-white' : 'text-slate-900'}">
        NOC MONITOR <span class="{isDark ? 'text-indigo-400' : 'text-indigo-600'}">ENTERPRISE</span>
      </h2>
      <p class="text-[11px] text-slate-400 font-mono mt-0.5">Сессия инженера (доступ на 1 год)</p>
    </div>

    <!-- СООБЩЕНИЕ ОБ ОШИБКЕ -->
    {#if errorMsg}
      <div class="mb-4 p-2.5 rounded-xl border text-xs font-mono text-center font-bold flex items-center justify-center gap-2
        {isDark ? 'bg-rose-500/15 text-rose-300 border-rose-500/30' : 'bg-rose-50 text-rose-700 border-rose-200'}">
        <span>⚠</span>
        <span>{errorMsg}</span>
      </div>
    {/if}

    <!-- ФОРМА ВХОДА -->
    <form on:submit|preventDefault={handleLogin} class="space-y-3.5 font-mono">
      
      <!-- ПОЛЕ ЛОГИНА -->
      <div class="space-y-1">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Имя пользователя / Login</label>
        <div class="relative flex items-center h-10 rounded-xl border overflow-hidden
          {isDark ? 'bg-[#141c2b] border-slate-700 text-white focus-within:border-indigo-500' : 'bg-slate-50 border-slate-300 text-slate-900 focus-within:border-indigo-500'}">
          <div class="pl-3 pr-2 text-slate-400">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <input 
            bind:this={usernameInputEl}
            type="text" 
            bind:value={username}
            placeholder="operator_noc"
            disabled={isLoading}
            class="w-full bg-transparent h-full pr-3 text-xs font-semibold outline-none placeholder:text-slate-400 font-sans"
          />
        </div>
      </div>

      <!-- ПОЛЕ ПАРОЛЯ -->
      <div class="space-y-1">
        <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Пароль / Password</label>
        <div class="relative flex items-center h-10 rounded-xl border overflow-hidden
          {isDark ? 'bg-[#141c2b] border-slate-700 text-white focus-within:border-indigo-500' : 'bg-slate-50 border-slate-300 text-slate-900 focus-within:border-indigo-500'}">
          <div class="pl-3 pr-2 text-slate-400">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          
          {#if showPassword}
            <input 
              type="text" 
              bind:value={password}
              placeholder="••••••••"
              disabled={isLoading}
              class="w-full bg-transparent h-full pr-8 text-xs font-semibold outline-none placeholder:text-slate-400 font-sans"
            />
          {:else}
            <input 
              type="password" 
              bind:value={password}
              placeholder="••••••••"
              disabled={isLoading}
              class="w-full bg-transparent h-full pr-8 text-xs font-semibold outline-none placeholder:text-slate-400 font-sans"
            />
          {/if}

          <!-- ГЛАЗОК -->
          <button 
            type="button"
            on:click={() => showPassword = !showPassword}
            class="absolute right-2.5 text-slate-400 hover:text-white text-xs cursor-pointer"
          >
            {showPassword ? '👁' : '👁‍🗨'}
          </button>
        </div>
      </div>

      <!-- КНОПКА ВХОДА -->
      <button 
        type="submit" 
        disabled={isLoading}
        class="w-full mt-3 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider transition-all cursor-pointer shadow-md shadow-indigo-500/25 active:scale-[0.98] disabled:opacity-50"
      >
        {isLoading ? 'Проверка...' : 'Войти в панель →'}
      </button>
    </form>
  </div>
</div>