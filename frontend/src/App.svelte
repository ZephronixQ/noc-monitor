<!-- frontend/src/App.svelte -->
<script>
  import { onMount, tick } from 'svelte';
  
  import Header from './components/common/Header.svelte';
  import HistoryModal from './components/common/HistoryModal.svelte';
  import PollingHud from './components/common/PollingHud.svelte';
  import LoginModal from './components/common/LoginModal.svelte';
  import AdminLoginModal from './components/admin/AdminLoginModal.svelte';
  import AdminHeader from './components/admin/AdminHeader.svelte';

  import DashboardTab from './components/dashboard/DashboardTab.svelte';
  import GponTab from './components/gpon/GponTab.svelte';
  import SwitchesTab from './components/switches/SwitchesTab.svelte';
  import NightAuditTab from './components/audit/NightAuditTab.svelte';
  import SessionManagerTab from './components/admin/SessionManagerTab.svelte';

  import { isDark, toggleTheme } from './stores/themeStore.js';
  import { 
    data, dailyStats, wsConnected, isUpdating, timeToNextUpdate, totalStats,
    fetchInitialData, fetchDailyStats, connectWebSocket, updateTimer, forceUpdate, BACKEND_URL 
  } from './stores/networkStore.js';
  
  import { initSecurityGuards } from './utils/security.js';

  let isAuthenticated = false;
  let isAdminAuthenticated = false;
  let isSecretAdminRoute = false;

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

  function checkRoute() {
    if (typeof window !== 'undefined') {
      isSecretAdminRoute = window.location.pathname.includes('/sessions');
    }
  }

  function setTab(tabId) {
    activeTab = tabId;
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('noc_active_tab', tabId);
      } catch (e) {}
    }
  }

  let currentUnixTime = Math.floor(Date.now() / 1000);
  let historyLabels = [];
  let historyData = [];

  $: switchFolders = $data.find(d => d && d.isSwitch)?.ports || [];

  setInterval(() => { currentUnixTime = Math.floor(Date.now() / 1000); }, 60000);

  async function checkAuth() {
    if (typeof window === 'undefined') return;
    checkRoute();

    const token = localStorage.getItem('noc_token');
    if (!token) {
      isAuthenticated = false;
    } else {
      try {
        const res = await fetch(`${BACKEND_URL}/api/auth/check`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) {
          localStorage.removeItem('noc_token');
          isAuthenticated = false;
        } else {
          isAuthenticated = true;
        }
      } catch (e) {
        // Офлайн
      }
    }

    const adminToken = localStorage.getItem('noc_admin_token');
    if (!adminToken) {
      isAdminAuthenticated = false;
    } else {
      try {
        const payload = JSON.parse(atob(adminToken.split('.')[1]));
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp < now) {
          localStorage.removeItem('noc_admin_token');
          isAdminAuthenticated = false;
        } else {
          isAdminAuthenticated = true;
        }
      } catch (e) {
        localStorage.removeItem('noc_admin_token');
        isAdminAuthenticated = false;
      }
    }
  }

  async function openHistory(contract, id, type = 'sw') {
    if (!id || isHistoryLoading) return;
    
    selectedEntity = { contract: contract || '—', id, type };
    isHistoryLoading = true;
    isModalOpen = true;
    
    try {
      const token = localStorage.getItem('noc_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const res = await fetch(`${BACKEND_URL}/api/history/${encodeURIComponent(id)}?days=30`, { headers });
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
    }, 300);
  }

  async function updateChartData() {
    await tick(); 
    const now = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    const currentOutages = $totalStats.los + $totalStats.losi;
    
    if (historyLabels.length > 0 && historyLabels[historyLabels.length - 1] === now) {
      historyData[historyData.length - 1] = currentOutages;
    } else {
      if (historyLabels.length > 30) { historyLabels.shift(); historyData.shift(); }
      historyLabels.push(now);
      historyData.push(currentOutages);
    }
    
    localStorage.setItem('noc_chart_labels', JSON.stringify(historyLabels));
    localStorage.setItem('noc_chart_data', JSON.stringify(historyData));
    
    historyLabels = [...historyLabels];
    historyData = [...historyData];
  }

  onMount(() => {
    initSecurityGuards();
    checkAuth();
    const authInterval = setInterval(checkAuth, 3000);

    try {
      const savedLabels = localStorage.getItem('noc_chart_labels');
      const savedData = localStorage.getItem('noc_chart_data');
      if (savedLabels && savedData) {
        historyLabels = JSON.parse(savedLabels);
        historyData = JSON.parse(savedData);
      }
    } catch(e) { console.error(e); }

    fetchInitialData();
    fetchDailyStats();
    const dailyStatsInterval = setInterval(fetchDailyStats, 300000); 

    connectWebSocket(updateChartData);
    const timerInterval = setInterval(updateTimer, 1000);

    return () => {
      clearInterval(authInterval);
      clearInterval(dailyStatsInterval);
      clearInterval(timerInterval);
    };
  });
</script>

{#if !isAuthenticated && !isSecretAdminRoute}
  <LoginModal isDark={$isDark} on:authenticated={() => isAuthenticated = true} />
{/if}

{#if isSecretAdminRoute && !isAdminAuthenticated}
  <AdminLoginModal isDark={$isDark} on:authenticated={() => isAdminAuthenticated = true} />
{/if}

{#if isModalOpen}
  <HistoryModal 
    isDark={$isDark} 
    {selectedEntity} 
    {entityHistory} 
    {isHistoryLoading} 
    on:close={closeHistory}
  />
{/if}

<div class="h-screen w-full overflow-hidden font-sans flex flex-col transition-colors duration-300 relative {$isDark ? 'bg-[#1c283e]' : 'bg-[#f4f6fc]'}">
  
  <div class="absolute inset-0 -z-20 {$isDark ? 'bg-grid-dark' : 'bg-grid-light'}"></div>

  <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none select-none">
    {#if $isDark}
      <div class="absolute top-[-10%] left-[-5%] w-[60%] h-[60%] rounded-full bg-indigo-500/[0.14] blur-[150px]"></div>
      <div class="absolute bottom-[-10%] right-[-5%] w-[55%] h-[55%] rounded-full bg-purple-500/[0.12] blur-[150px]"></div>
    {:else}
      <div class="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-400/[0.06] blur-[100px]"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[55%] rounded-full bg-purple-400/[0.03] blur-[100px]"></div>
    {/if}
  </div>

  {#if isSecretAdminRoute}
    <AdminHeader isDark={$isDark} on:toggleTheme={toggleTheme} />
  {:else}
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
  {/if}

  <main class="p-8 flex-1 overflow-hidden flex flex-col min-h-0">
    {#if isSecretAdminRoute}
      <SessionManagerTab isDark={$isDark} />
    {:else}
      {#if activeTab === 'dash'}
        <DashboardTab 
          isDark={$isDark} 
          dailyStats={$dailyStats} 
          totalStats={$totalStats} 
          {historyLabels} 
          {historyData}
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
    {/if}
  </main>
</div>

{#if !isSecretAdminRoute}
  <PollingHud isDark={$isDark} />
{/if}

<style>
  :global(body) { 
    margin: 0; 
    height: 100vh; 
    overflow: hidden; 
    background-color: #1c283e; 
  }

  :global(.bg-grid-dark) {
    background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1.5px, transparent 1.5px);
    background-size: 24px 24px;
  }
  
  :global(.bg-grid-light) {
    background-image: radial-gradient(rgba(99, 102, 241, 0.03) 1.5px, transparent 1.5px);
    background-size: 24px 24px;
  }

  :global(.always-visible-scroll) {
    overflow-y: auto !important;
    overflow-x: hidden !important; 
    scrollbar-width: thin !important; 
    scrollbar-color: #a855f7 transparent !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar) {
    width: 5px !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-track) {
    background-color: transparent !important; 
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-thumb) {
    background: linear-gradient(180deg, #6366f1 0%, #a855f7 50%, #ec4899 100%) !important;
    border-radius: 99px !important;
    box-shadow: 0 0 8px rgba(168, 85, 247, 0.5) !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(180deg, #818cf8 0%, #f43f5e 100%) !important;
    box-shadow: 0 0 12px rgba(244, 63, 94, 0.8) !important;
  }
</style>