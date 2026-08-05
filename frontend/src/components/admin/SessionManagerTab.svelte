<!-- frontend/src/components/admin/SessionManagerTab.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { BACKEND_URL } from '../../stores/networkStore.js';

  export let isDark = false;

  let sessions = [];
  let bans = [];
  let logs = [];

  let isLoading = false;
  let customBanIp = '';
  let customBanReason = 'Ручной бан администратора';
  let statusMsg = '';
  let pollInterval = null;

  async function fetchSecurityData() {
    const adminToken = localStorage.getItem('noc_admin_token');
    if (!adminToken) return;

    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/security`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      });

      if (res.ok) {
        const data = await res.json();
        sessions = data.sessions || [];
        bans = data.bans || [];
        logs = data.logs || [];
      }
    } catch (e) {
      console.error("Ошибка загрузки безопасности:", e);
    }
  }

  async function sendAdminAction(url, body = {}) {
    const adminToken = localStorage.getItem('noc_admin_token');
    if (!adminToken) return false;

    isLoading = true;
    try {
      const res = await fetch(`${BACKEND_URL}${url}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        // МГНОВЕННЫЙ ПЕРЕЗАПРОС СВЕЖИХ ДАННЫХ ДЛЯ ОБНОВЛЕНИЯ UI
        await fetchSecurityData();
        return true;
      } else {
        const err = await res.json();
        statusMsg = err.detail || 'Ошибка выполнения действия';
        setTimeout(() => statusMsg = '', 3000);
      }
    } catch (e) {
      statusMsg = 'Ошибка соединения с сервером';
      setTimeout(() => statusMsg = '', 3000);
    } finally {
      isLoading = false;
    }
    return false;
  }

  // 1. Выбить сессию
  async function handleKillSession(session_id) {
    await sendAdminAction('/api/admin/session/kill', { session_id });
  }

  // 2. Заблокировать IP
  async function handleBanIp(ip, reason = 'Заблокирован админом') {
    if (!ip) return;
    const success = await sendAdminAction('/api/admin/ip/ban', { ip, reason });
    if (success) {
      customBanIp = '';
    }
  }

  // 3. Разблокировать IP
  async function handleUnbanIp(ip) {
    await sendAdminAction('/api/admin/ip/unban', { ip });
  }

  // 4. Очистить выбитые и неактивные сессии
  async function handleClearInactiveSessions() {
    await sendAdminAction('/api/admin/sessions/clear-inactive');
  }

  // 5. Очистить логи аудита
  async function handleClearLogs() {
    await sendAdminAction('/api/admin/logs/clear');
  }

  function formatTime(ts) {
    if (!ts) return '—';
    return new Date(ts * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function formatDate(ts) {
    if (!ts) return '—';
    return new Date(ts * 1000).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  onMount(() => {
    fetchSecurityData();
    pollInterval = setInterval(fetchSecurityData, 3000); // Авто-обновление каждые 3 секунды
  });

  onDestroy(() => {
    if (pollInterval) clearInterval(pollInterval);
  });
</script>

<div class="flex-1 flex flex-col gap-5 overflow-hidden min-h-0 font-sans z-10 relative" in:fade={{ duration: 150 }}>
  
  <!-- Верхняя панель быстрого бана IP -->
  <div class="p-5 rounded-2xl border shadow-xs flex items-center justify-between gap-4 shrink-0 transition-colors
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-rose-500/15 text-rose-400 border border-rose-500/20 flex items-center justify-center text-lg font-black shrink-0">
        🛡️
      </div>
      <div>
        <h2 class="text-sm font-bold {isDark ? 'text-slate-100' : 'text-slate-800'}">Центр управления доступом</h2>
        <p class="text-xs text-slate-400 font-mono mt-0.5">Аннулирование сессий, перманентный бан IP-адресов и аудит безопасности</p>
      </div>
    </div>

    {#if statusMsg}
      <div class="px-3 py-1.5 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-400 font-mono text-xs font-bold animate-pulse">
        {statusMsg}
      </div>
    {/if}

    <form on:submit|preventDefault={() => handleBanIp(customBanIp, customBanReason)} class="flex items-center gap-2">
      <input 
        type="text" 
        bind:value={customBanIp}
        placeholder="Введите IP (напр. 192.168.1.50)..."
        class="px-4 py-2 rounded-xl border font-mono text-xs outline-none transition-all w-64
        {isDark ? 'bg-[#141f33] border-slate-700/80 text-white placeholder-slate-500 focus:border-rose-500' : 'bg-slate-50 border-slate-200 text-slate-900 placeholder-slate-400 focus:border-rose-500'}"
      />
      <button 
        type="submit"
        disabled={isLoading || !customBanIp}
        class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-mono font-bold text-xs uppercase tracking-wider transition-all cursor-pointer shadow-xs disabled:opacity-40"
      >
        Забанить IP ⛔
      </button>
    </form>
  </div>

  <!-- Трёхколоночная сетка -->
  <div class="flex-1 grid grid-cols-3 gap-5 min-h-0">
    
    <!-- Колонка 1: Подключенные устройства / Сессии -->
    <div class="p-5 rounded-2xl border shadow-xs flex flex-col overflow-hidden transition-colors
      {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
    >
      <div class="pb-3 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} flex justify-between items-center shrink-0 mb-3 select-none">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-200' : 'text-slate-700'}">
            Подключенные устройства ({sessions.length})
          </span>
        </div>

        <button 
          on:click={handleClearInactiveSessions}
          disabled={isLoading}
          class="text-[9.5px] font-mono font-bold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-2xs
          {isDark ? 'bg-[#152033] border-slate-700 text-amber-400 hover:bg-amber-500/20' : 'bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100'}"
          title="Удалить неактивные и выбитые сессии из списка"
        >
          🧹 Очистить старые
        </button>
      </div>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2.5">
        {#if sessions.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs text-slate-400 py-10">
            <span>Нет активных сессий</span>
          </div>
        {:else}
          {#each sessions as s}
            <div class="p-3 rounded-xl border flex flex-col gap-2 transition-all font-mono text-xs
              {s.is_active 
                ? (isDark ? 'bg-[#162238] border-slate-700/60' : 'bg-slate-50 border-slate-200/80') 
                : (isDark ? 'bg-slate-900/40 border-slate-800/40 opacity-50' : 'bg-slate-100 border-slate-200 opacity-50')}"
            >
              <div class="flex justify-between items-start gap-2">
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-extrabold text-xs {s.is_online ? 'text-emerald-400' : (s.is_active ? 'text-indigo-400' : 'text-slate-400')}">
                      IP: {s.ip}
                    </span>
                    
                    {#if s.is_online}
                      <span class="px-1.5 py-0.2 rounded text-[8px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase font-black">
                        В сети
                      </span>
                    {:else if s.is_active}
                      <span class="px-1.5 py-0.2 rounded text-[8px] bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 uppercase font-bold">
                        Активна
                      </span>
                    {:else}
                      <span class="px-1.5 py-0.2 rounded text-[8px] bg-rose-500/15 text-rose-400 border border-rose-500/30 uppercase font-bold">
                        Выбит / Закрыт
                      </span>
                    {/if}
                  </div>

                  <div class="text-[9.5px] font-sans text-slate-400 truncate mt-1" title={s.user_agent}>
                    {s.user_agent || 'Неизвестный браузер'}
                  </div>
                </div>

                {#if s.is_active}
                  <div class="flex items-center gap-1.5 shrink-0">
                    <button 
                      on:click={() => handleKillSession(s.session_id)}
                      class="px-2 py-1 rounded-lg bg-amber-500/15 hover:bg-amber-500 text-amber-400 hover:text-white border border-amber-500/30 text-[9px] font-bold font-mono transition-all cursor-pointer"
                      title="Принудительно разжаловать сессию"
                    >
                      Выбить
                    </button>
                    <button 
                      on:click={() => handleBanIp(s.ip, 'Заблокирован из списка сессий')}
                      class="px-2 py-1 rounded-lg bg-rose-500/15 hover:bg-rose-500 text-rose-400 hover:text-white border border-rose-500/30 text-[9px] font-bold font-mono transition-all cursor-pointer"
                      title="Заблокировать данный IP навсегда"
                    >
                      Забанить
                    </button>
                  </div>
                {/if}
              </div>

              <div class="flex justify-between items-center text-[9px] text-slate-400 pt-1.5 border-t border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-200'}">
                <span>Вход: <strong class="text-slate-300">{formatTime(s.created_at)}</strong></span>
                <span>Активность: <strong class="text-indigo-400">{formatTime(s.last_seen)}</strong></span>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>

    <!-- Колонка 2: Заблокированные IP -->
    <div class="p-5 rounded-2xl border shadow-xs flex flex-col overflow-hidden transition-colors
      {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
    >
      <div class="pb-3 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} flex justify-between items-center shrink-0 mb-3 select-none">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
          <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-200' : 'text-slate-700'}">
            Заблокировано ({bans.length})
          </span>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2.5">
        {#if bans.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs text-slate-400 py-10">
            <span>✨ Заблокированных IP нет</span>
          </div>
        {:else}
          {#each bans as b}
            <div class="p-3 rounded-xl border flex flex-col gap-2 font-mono text-xs transition-all
              {isDark ? 'bg-[#162238] border-rose-500/30' : 'bg-rose-50/50 border-rose-200'}"
            >
              <div class="flex justify-between items-center gap-2">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="font-extrabold text-xs text-rose-400">IP: {b.ip}</span>
                  <span class="px-1.5 py-0.2 rounded text-[8px] bg-rose-500/20 text-rose-400 border border-rose-500/30 uppercase font-black">
                    {b.ban_type === 'permanent' ? 'НАВСЕГДА' : 'ВРЕМЕННО'}
                  </span>
                </div>

                <button 
                  on:click={() => handleUnbanIp(b.ip)}
                  class="px-2.5 py-1 rounded-lg bg-emerald-500/15 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500/30 text-[9px] font-bold transition-all cursor-pointer"
                >
                  Разбанить
                </button>
              </div>

              <div class="text-[10px] font-sans text-slate-300">
                Причина: <strong class="text-rose-300 font-mono">{b.reason}</strong>
              </div>

              <div class="text-[8.5px] text-slate-400 text-right">
                Дата бана: {formatDate(b.created_at)} {formatTime(b.created_at)}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>

    <!-- Колонка 3: История аудита -->
    <div class="p-5 rounded-2xl border shadow-xs flex flex-col overflow-hidden transition-colors
      {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
    >
      <div class="pb-3 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} flex justify-between items-center shrink-0 mb-3 select-none">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
          <span class="text-[11px] font-mono font-bold uppercase tracking-wider {isDark ? 'text-slate-200' : 'text-slate-700'}">
            История Аудита ({logs.length})
          </span>
        </div>

        <button 
          on:click={handleClearLogs}
          disabled={isLoading}
          class="text-[9.5px] font-mono font-bold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-2xs
          {isDark ? 'bg-[#152033] border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'}"
          title="Очистить историю аудита безопасности"
        >
          🗑️ Очистить логи
        </button>
      </div>

      <div class="flex-1 overflow-y-auto pr-1 always-visible-scroll space-y-2">
        {#if logs.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center font-mono text-xs text-slate-400 py-10">
            <span>Логи аудита пусты</span>
          </div>
        {:else}
          {#each logs as l}
            <div class="p-2.5 rounded-xl border flex flex-col gap-1 font-mono text-xs transition-all
              {isDark ? 'bg-[#162238] border-slate-700/50' : 'bg-slate-50 border-slate-200'}"
            >
              <div class="flex justify-between items-center">
                <span class="font-extrabold text-[11px] text-indigo-400">IP: {l.ip}</span>
                <span class="text-[9px] text-slate-400">{formatTime(l.timestamp)}</span>
              </div>
              <div class="text-[10px] font-sans text-slate-200 leading-snug">
                {l.action}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>

  </div>
</div>