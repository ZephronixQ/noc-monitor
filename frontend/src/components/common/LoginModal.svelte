<!-- frontend/src/components/common/LoginModal.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { BACKEND_URL } from '../../stores/networkStore.js';

  export let isDark = false;
  const dispatch = createEventDispatcher();

  let password = '';
  let errorMsg = '';
  let isLoading = false;

  async function handleLogin() {
    if (!password) return;
    isLoading = true;
    errorMsg = '';

    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('noc_token', data.token);
        dispatch('authenticated');
      } else {
        errorMsg = data.detail || 'Ошибка авторизации';
      }
    } catch (e) {
      errorMsg = 'Сервер недоступен';
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xl font-sans">
  <div class="w-full max-w-md p-8 rounded-3xl border shadow-2xl transition-colors
    {isDark ? 'bg-[#1e2a40] border-slate-700/70 text-white' : 'bg-white border-slate-200 text-slate-900'}"
  >
    <div class="text-center mb-6">
      <div class="w-12 h-12 mx-auto mb-3 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-black text-xl">
        🔒
      </div>
      <h2 class="text-xl font-bold">NOC Monitor Access</h2>
      <p class="text-xs text-slate-300 font-mono mt-1">Введите пароль доступа смены</p>
    </div>

    {#if errorMsg}
      <div class="mb-4 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs font-mono text-center font-bold">
        {errorMsg}
      </div>
    {/if}

    <form on:submit|preventDefault={handleLogin} class="space-y-4">
      <div>
        <input 
          type="password" 
          bind:value={password}
          placeholder="Введите пароль..."
          disabled={isLoading}
          class="w-full px-4 py-3 rounded-xl border text-center font-mono text-lg tracking-widest outline-none transition-all
          {isDark ? 'bg-[#131d30] border-slate-700 text-white focus:border-indigo-500' : 'bg-slate-50 border-slate-200 text-slate-900 focus:border-indigo-500'}"
        />
      </div>

      <button 
        type="submit" 
        disabled={isLoading}
        class="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-mono font-bold text-xs uppercase tracking-wider transition-all cursor-pointer shadow-lg shadow-indigo-500/25"
      >
        {isLoading ? 'Проверка...' : 'Войти в систему'}
      </button>
    </form>
  </div>
</div>