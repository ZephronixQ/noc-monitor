<script>
  import { onMount, tick } from 'svelte';
  
  // Импорты общих компонентов (папка common)
  import Header from './components/common/Header.svelte';
  import HistoryModal from './components/common/HistoryModal.svelte';

  // Импорты вкладок по соответствующим подпапкам
  import DashboardTab from './components/dashboard/DashboardTab.svelte';
  import GponTab from './components/gpon/GponTab.svelte';
  import SwitchesTab from './components/switches/SwitchesTab.svelte';
  import NightAuditTab from './components/audit/NightAuditTab.svelte';

  // Импорт хранилищ
  import { isDark, toggleTheme } from './stores/themeStore.js';
  import { 
    data, dailyStats, wsConnected, isUpdating, timeToNextUpdate, totalStats,
    fetchInitialData, fetchDailyStats, connectWebSocket, updateTimer, forceUpdate, BACKEND_URL 
  } from './stores/networkStore.js';

  let selectedEntity = null; 
  let entityHistory = [];
  let isHistoryLoading = false;
  let isModalOpen = false;

  let activeTab = 'dash'; 
  let currentUnixTime = Math.floor(Date.now() / 1000);
  let historyLabels = [];
  let historyData = [];

  $: switchFolders = $data.find(d => d.isSwitch)?.ports || [];

  setInterval(() => { currentUnixTime = Math.floor(Date.now() / 1000); }, 60000);

  // Стабильный запрос логов для коммутаторов и ONU
  async function openHistory(contract, id, type = 'sw') {
    if (!contract || contract === '—' || isHistoryLoading) return;
    
    selectedEntity = { contract, id, type };
    isHistoryLoading = true;
    isModalOpen = true;
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/history/${encodeURIComponent(id)}?days=30`);
      if (!res.ok) throw new Error();
      const json = await res.json();
      entityHistory = json.incidents || json.data || [];
    } catch {
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
    setInterval(fetchDailyStats, 300000); 

    connectWebSocket(updateChartData);
    setInterval(updateTimer, 1000);
  });
</script>

{#if isModalOpen}
  <HistoryModal 
    isDark={$isDark} 
    {selectedEntity} 
    {entityHistory} 
    {isHistoryLoading} 
    on:close={closeHistory}
  />
{/if}

<div class="h-screen w-full overflow-hidden font-sans flex flex-col transition-colors duration-300 relative {$isDark ? 'bg-[#121724]' : 'bg-[#f4f6fc]'}">
  
  <div class="absolute inset-0 -z-20 {$isDark ? 'bg-grid-dark' : 'bg-grid-light'}"></div>

  <div class="absolute inset-0 -z-10 overflow-hidden pointer-events-none select-none">
    {#if $isDark}
      <div class="absolute top-[-10%] left-[-5%] w-[60%] h-[60%] rounded-full bg-indigo-500/[0.12] blur-[120px]"></div>
      <div class="absolute bottom-[-10%] right-[-5%] w-[55%] h-[55%] rounded-full bg-purple-500/[0.08] blur-[120px]"></div>
    {:else}
      <div class="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-400/[0.06] blur-[100px]"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[55%] rounded-full bg-purple-400/[0.03] blur-[100px]"></div>
    {/if}
  </div>

  <!-- Шапка (ИСПРАВЛЕНО: Удалены неиспользуемые переменные и слушатели уведомлений) -->
  <Header 
    isDark={$isDark} 
    wsConnected={$wsConnected} 
    timeToNextUpdate={$timeToNextUpdate} 
    isUpdating={$isUpdating} 
    {activeTab} 
    on:tabChange={(e) => activeTab = e.detail}
    on:toggleTheme={toggleTheme}
    on:forceUpdate={forceUpdate}
  />

  <main class="p-8 flex-1 overflow-hidden flex flex-col min-h-0">
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
  </main>
</div>

<style>
  :global(body) { 
    margin: 0; 
    height: 100vh; 
    overflow: hidden; 
  }

  :global(.bg-grid-dark) {
    background-image: radial-gradient(rgba(255, 255, 255, 0.04) 1.5px, transparent 1.5px);
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
    scrollbar-color: rgba(148, 163, 184, 0.3) transparent !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar) {
    width: 6px !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-track) {
    background-color: transparent !important; 
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-thumb) {
    background-color: rgba(148, 163, 184, 0.2) !important;
    border-radius: 99px;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-thumb:hover) {
    background-color: rgba(99, 102, 241, 0.5) !important; 
  }
</style>