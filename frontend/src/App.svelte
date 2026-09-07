<!-- frontend/src/App.svelte -->
<script>
  import { onMount } from 'svelte';
  
  import Header from './components/common/Header.svelte';
  import HistoryModal from './components/common/HistoryModal.svelte';
  import PollingHud from './components/common/PollingHud.svelte';
  import LoginModal from './components/common/LoginModal.svelte';

  import DashboardTab from './components/dashboard/DashboardTab.svelte';
  import GponTab from './components/gpon/GponTab.svelte';
  import SwitchesTab from './components/switches/SwitchesTab.svelte';
  import NightAuditTab from './components/audit/NightAuditTab.svelte';

  import { isDark, toggleTheme } from './stores/themeStore.js';
  import { 
    data, dailyStats, wsConnected, isUpdating, timeToNextUpdate, totalStats,
    fetchInitialData, fetchDailyStats, connectWebSocket, updateTimer, forceUpdate, BACKEND_URL 
  } from './stores/networkStore.js';
  
  import { initSecurityGuards } from './utils/security.js';

  // Срок действия сессии оператора: 365 дней (1 год)
  const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;

  let isAuthenticated = false;

  let selectedEntity = null; 
  let entityHistory = [];
  let isHistoryLoading = false;
  let isModalOpen = false;

  let initialTab = 'dash';
  if (typeof window !== 'undefined') {
    try {
      initialTab = localStorage.getItem('noc_active_tab') || 'dash';
    } catch (e) {}
  }
  let activeTab = initialTab; 

  function setTab(tabId) {
    activeTab = tabId;
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('noc_active_tab', tabId);
      } catch (e) {}
    }
  }

  let currentUnixTime = Math.floor(Date.now() / 1000);
  $: switchFolders = $data.find(d => d && d.isSwitch)?.ports || [];

  setInterval(() => { currentUnixTime = Math.floor(Date.now() / 1000); }, 60000);

  // Проверка валидности сессии (хранится 1 год)
  function checkAuth() {
    if (typeof window === 'undefined') return;

    const token = localStorage.getItem('noc_token');
    const expiresAt = localStorage.getItem('noc_token_expires_at');

    if (!token) {
      isAuthenticated = false;
    } else {
      const now = Date.now();
      if (!expiresAt) {
        localStorage.setItem('noc_token_expires_at', String(now + ONE_YEAR_MS));
        isAuthenticated = true;
      } else if (now > Number(expiresAt)) {
        localStorage.removeItem('noc_token');
        localStorage.removeItem('noc_token_expires_at');
        localStorage.removeItem('noc_user');
        isAuthenticated = false;
      } else {
        isAuthenticated = true;
      }
    }
  }

  function handleSuccessfulAuth() {
    const expiresAt = Date.now() + ONE_YEAR_MS;
    localStorage.setItem('noc_token_expires_at', String(expiresAt));
    isAuthenticated = true;
  }

  async function openHistory(contract, id, type = 'sw') {
    if (!id || isHistoryLoading) return;
    
    selectedEntity = { contract: contract || '—', id, type };
    isHistoryLoading = true;
    isModalOpen = true;
    
    try {
      const token = localStorage.getItem('noc_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const res = await fetch(`${BACKEND_URL}/api/history/${encodeURIComponent(id)}?days=365`, { headers });
      
      // Если токен недействителен (401) - сразу открываем окно логина
      if (res.status === 401) {
        localStorage.removeItem('noc_token');
        localStorage.removeItem('noc_token_expires_at');
        isAuthenticated = false;
        isModalOpen = false;
        return;
      }

      if (!res.ok) throw new Error('Ошибка сервера');
      const json = await res.json();
      entityHistory = json.incidents || json.data || [];
    } catch (err) {
      console.error("Ошибка загрузки истории:", err);
      entityHistory = []; 
    } finally {
      isHistoryLoading = false; 
    }
  }

  function closeHistory() {
    isModalOpen = false;
    setTimeout(() => { 
      selectedEntity = null; 
      entityHistory = []; 
    }, 200);
  }

  onMount(() => {
    initSecurityGuards();
    checkAuth();
    
    const authInterval = setInterval(checkAuth, 1800000);

    fetchInitialData();
    fetchDailyStats();
    const dailyStatsInterval = setInterval(fetchDailyStats, 300000); 

    connectWebSocket();
    const timerInterval = setInterval(updateTimer, 1000);

    return () => {
      clearInterval(authInterval);
      clearInterval(dailyStatsInterval);
      clearInterval(timerInterval);
    };
  });
</script>

<!-- МОДАЛЬНОЕ ОКНО АВТОРИЗАЦИИ ОПЕРАТОРА -->
{#if !isAuthenticated}
  <LoginModal isDark={$isDark} on:authenticated={handleSuccessfulAuth} />
{/if}

<!-- МОДАЛЬНОЕ ОКНО ИСТОРИИ ИНЦИДЕНТОВ -->
{#if isModalOpen}
  <HistoryModal 
    isDark={$isDark} 
    {selectedEntity} 
    {entityHistory} 
    {isHistoryLoading} 
    on:close={closeHistory}
  />
{/if}

<!-- ГЛАВНЫЙ ЭКРАН МОНИТОРИНГА -->
<div class="h-screen w-full overflow-hidden font-sans flex flex-col transition-colors duration-300 relative {$isDark ? 'bg-[#182335]' : 'bg-[#f8fafc]'}">
  
  <div class="absolute inset-0 -z-20 {$isDark ? 'bg-grid-dark' : 'bg-grid-light'}"></div>

  <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none select-none">
    {#if $isDark}
      <div class="absolute top-[-10%] left-[-5%] w-[60%] h-[60%] rounded-full bg-indigo-500/[0.12] blur-[150px]"></div>
      <div class="absolute bottom-[-10%] right-[-5%] w-[55%] h-[55%] rounded-full bg-purple-500/[0.10] blur-[150px]"></div>
    {:else}
      <div class="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-400/[0.05] blur-[100px]"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[55%] rounded-full bg-purple-400/[0.03] blur-[100px]"></div>
    {/if}
  </div>

  <!-- ШАПКА МОНИТОРИНГА -->
  <Header 
    isDark={$isDark} 
    wsConnected={$wsConnected} 
    timeToNextUpdate={$timeToNextUpdate} 
    isUpdating={$isUpdating} 
    {activeTab} 
    on:tabChange={(e) => setTab(e.detail)}
    on:toggleTheme={toggleTheme}
    on:forceUpdate={forceUpdate}
  />

  <!-- ОСНОВНОЙ КОНТЕНТ ВКЛАДОК -->
  <main class="p-6 flex-1 overflow-hidden flex flex-col min-h-0">
    {#if activeTab === 'dash'}
      <DashboardTab 
        isDark={$isDark} 
        dailyStats={$dailyStats} 
        totalStats={$totalStats} 
      />
    {:else if activeTab === 'olt'}
      <GponTab 
        isDark={$isDark} 
        olts={$data.filter(d => !d.isSwitch)} 
        {currentUnixTime}
        on:openHistory={(e) => openHistory(e.detail.contract, e.detail.id, 'onu')} 
      />
    {:else if activeTab === 'sw'}
      <SwitchesTab 
        isDark={$isDark} 
        {switchFolders} 
        {currentUnixTime}
        on:openHistory={(e) => openHistory(e.detail.contract, e.detail.id, 'sw')}
      />
    {:else if activeTab === 'night'}
      <NightAuditTab 
        isDark={$isDark}
        {currentUnixTime}
        on:openHistory={(e) => openHistory(e.detail.contract, e.detail.id, e.detail.type)}
      />
    {/if}
  </main>
</div>

<!-- ИНДИКАТОР ПРОЦЕССА ОПРОСА В РЕАЛЬНОМ ВРЕМЕНИ -->
<PollingHud isDark={$isDark} />

<style>
  :global(::-webkit-scrollbar) {
    width: 5px;
    height: 5px;
  }

  :global(::-webkit-scrollbar-track) {
    background: transparent;
  }

  :global(::-webkit-scrollbar-thumb) {
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.45) 0%, rgba(168, 85, 247, 0.45) 100%);
    border-radius: 9999px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 0.25s ease;
  }

  :global(::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%);
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
  }

  :global(::-webkit-scrollbar-corner) {
    background: transparent;
  }
</style>