<script>
  import { onMount } from 'svelte';
  import { slide, fade } from 'svelte/transition';

  let host = "localhost"; 
  onMount(() => { host = window.location.hostname; });

  $: BACKEND_URL = `http://${host}:8000`;
  $: WS_URL = `ws://${host}:8000/ws`;

  let activeTab = 'dash'; 
  let activeOltIndex = 0;
  let activeFolderIndex = 0; // Индекс для папок коммутаторов
  
  // Независимые поисковые запросы
  let searchQuery = ''; // Для OLT
  let switchSearchQuery = ''; // Для Коммутаторов
  
  let globalLosFilter = false;
  let activePort = null;
  let subFilter = 'all'; // all, online, los, dying, offline

  // Пагинация для OLT
  let currentPage = 1;
  const itemsPerPage = 16;

  let data = [];
  let nextUpdateTs = 0;
  let timeToNextUpdate = "00:00";
  let isUpdating = true;

  // --- ДАННЫЕ OLT ---
  $: olts = data.filter(d => !d.isSwitch);
  $: currentOlt = olts[activeOltIndex] || { ports: [] };

  // Фильтрация портов OLT
  $: filteredPorts = currentOlt.ports?.filter(port => {
    const hasLos = port.onus.some(o => ['LOS', 'Down'].includes(o.state));
    if (globalLosFilter && !hasLos) return false;
    
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return port.name.toLowerCase().includes(q) || 
           port.onus.some(o => (o.contract || '').toLowerCase().includes(q));
  }) || [];

  $: paginatedPorts = filteredPorts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  $: totalPages = Math.ceil(filteredPorts.length / itemsPerPage);


  // --- ДАННЫЕ КОММУТАТОРОВ (С ПАПКАМИ) ---
  $: switchDataNode = data.find(d => d.isSwitch) || { ports: [] };
  $: switchFolders = switchDataNode.ports || [];
  
  // Плоский список всех коммутаторов
  $: allSwitchesFlat = switchFolders.flatMap(folder => folder.onus || []);
  
  // Текущая активная папка
  $: currentSwitchFolder = switchFolders[activeFolderIndex] || { onus: [] };

  // Если есть текст в поиске - ищем по ВСЕМ папкам плоским списком. Если нет - показываем выбранную папку.
  $: displayedSwitches = switchSearchQuery 
    ? allSwitchesFlat.filter(sw => sw.id.toLowerCase().includes(switchSearchQuery.toLowerCase()) || (sw.contract || '').toLowerCase().includes(switchSearchQuery.toLowerCase()))
    : currentSwitchFolder.onus || [];


  // --- СТАТИСТИКА (ОБЗОР) ---
  $: totalStats = {
    onus: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).length, 0),
    online: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => o.state === 'working').length, 0),
    los: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => ['LOS', 'Down'].includes(o.state)).length, 0),
    olts: olts.length,
    switches: allSwitchesFlat.length,
    swUp: allSwitchesFlat.filter(sw => sw.state === 'working' || sw.state === 'Host is alive').length
  };


  // --- ФУНКЦИИ ---

  const setTab = (tab) => { 
    activeTab = tab; 
    activePort = null; 
    currentPage = 1; 
  };
  
  const exportPortCsv = (port) => {
    const headers = "ID,Contract,State\n";
    const rows = port.onus.map(o => `${o.id},${o.contract || '—'},${o.state}`).join("\n");
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `port_${port.name.replace(/\//g, '_')}.csv`;
    a.click();
  };

  const exportJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "noc_export.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const getStatusColor = (state) => {
    if (state === 'working' || state === 'Host is alive') return 'text-emerald-500';
    if (state === 'DyingGasp') return 'text-orange-500';
    return 'text-red-500';
  };

  const getDotColor = (state) => {
    if (state === 'working' || state === 'Host is alive') return 'bg-emerald-500';
    if (state === 'DyingGasp') return 'bg-orange-500';
    return 'bg-red-500';
  };

  function updateTimer() {
    if (!nextUpdateTs) return;
    const diff = nextUpdateTs - Math.floor(Date.now() / 1000);
    timeToNextUpdate = diff <= 0 ? "00:00" : `${Math.floor(diff/60)}:${(diff%60).toString().padStart(2,'0')}`;
  }

  onMount(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/data`);
      const json = await res.json();
      data = json.data; nextUpdateTs = json.next_update; isUpdating = json.is_updating;
    } catch(e) {}

    const ws = new WebSocket(WS_URL);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "update") {
        data = msg.data; nextUpdateTs = msg.next_update; isUpdating = msg.is_updating;
      }
    };
    setInterval(updateTimer, 1000);
  });
</script>

<div class="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
  <header class="bg-[#1e293b] text-white h-14 flex items-center justify-between px-6 sticky top-0 z-50 shadow-md">
    <div class="flex items-center gap-8">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-indigo-500 rounded flex items-center justify-center font-bold">N</div>
        <span class="font-bold tracking-tight text-lg italic">NOC VISION</span>
      </div>
      
      <nav class="flex gap-1 bg-slate-800 p-1 rounded-lg">
        <button on:click={() => setTab('dash')} class="px-4 py-1 rounded text-[11px] font-bold transition-all {activeTab === 'dash' ? 'bg-indigo-500 shadow' : 'text-slate-400 hover:text-white'}">ОБЗОР</button>
        <button on:click={() => setTab('olt')} class="px-4 py-1 rounded text-[11px] font-bold transition-all {activeTab === 'olt' ? 'bg-indigo-500 shadow' : 'text-slate-400 hover:text-white'}">GPON</button>
        <button on:click={() => setTab('sw')} class="px-4 py-1 rounded text-[11px] font-bold transition-all {activeTab === 'sw' ? 'bg-indigo-500 shadow' : 'text-slate-400 hover:text-white'}">КОММУТАТОРЫ</button>
      </nav>
    </div>

    <div class="flex items-center gap-4">
      <button on:click={exportJson} class="text-[10px] bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded font-bold transition-colors">JSON EXPORT</button>
      <div class="font-mono text-[11px] text-slate-400">СЛЕД. ОПРОС: <span class="text-indigo-400">{timeToNextUpdate}</span></div>
    </div>
  </header>

  <main class="p-6 flex-1 overflow-hidden flex flex-col">
    <!-- ВКЛАДКА: ОБЗОР -->
    {#if activeTab === 'dash'}
      <div class="grid grid-cols-3 gap-6" in:fade>
        <div class="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Клиенты (ONU)</span>
          <div class="text-5xl font-black mt-2 text-slate-800">{totalStats.onus}</div>
          <div class="mt-4 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div class="bg-indigo-500 h-full" style="width: {(totalStats.online/totalStats.onus)*100}%"></div>
          </div>
          <div class="mt-2 text-xs font-bold text-emerald-500">{((totalStats.online/totalStats.onus)*100).toFixed(1)}% Up</div>
        </div>
        <div class="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Коммутаторы</span>
          <div class="text-5xl font-black mt-2 text-slate-800">{totalStats.swUp}/{totalStats.switches}</div>
          <div class="mt-4 flex gap-1">
             {#each Array(totalStats.switches) as _, i}
               <div class="h-2 flex-1 rounded-full {i < totalStats.swUp ? 'bg-emerald-400' : 'bg-red-400'}"></div>
             {/each}
          </div>
          <div class="mt-2 text-xs font-bold text-red-500">{totalStats.switches - totalStats.swUp} Down</div>
        </div>
        <div class="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Активные OLT</span>
          <div class="text-5xl font-black mt-2 text-slate-800">{totalStats.olts}</div>
          <p class="text-xs text-slate-400 mt-4 font-bold">Все системы мониторинга стабильны</p>
        </div>
      </div>

    <!-- ВКЛАДКА: GPON (OLT) -->
    {:else if activeTab === 'olt'}
      <div class="flex gap-6 h-full overflow-hidden" in:fade>
        <div class="w-64 flex flex-col gap-2 overflow-y-auto pr-2">
          <h3 class="text-[10px] font-black text-slate-400 uppercase mb-2 px-2">Агрегация (OLT)</h3>
          {#each olts as olt, i}
            <!-- Считаем Онлайн / Всего для текущего OLT -->
            {@const allOnus = olt.ports.flatMap(p => p.onus)}
            {@const totalCount = allOnus.length}
            {@const onlineCount = allOnus.filter(o => o.state === 'working').length}
            
            <button on:click={() => {activeOltIndex = i; currentPage = 1;}}
              class="p-4 rounded-2xl border text-left transition-all {activeOltIndex === i ? 'bg-white border-indigo-500 shadow-md ring-1 ring-indigo-500' : 'bg-white/50 border-slate-200 hover:bg-white'}">
              <div class="font-bold text-sm text-slate-700">{olt.ip}</div>
              <div class="flex justify-between mt-1 items-center">
                <!-- Выводим соотношение как на втором скрине -->
                <span class="text-[10px] font-bold text-slate-400">{onlineCount} / {totalCount} В СЕТИ</span>
                
                <span class="text-[9px] font-black px-1.5 py-0.5 rounded {allOnus.some(o => ['LOS', 'Down'].includes(o.state)) ? 'bg-red-100 text-red-600' : 'bg-emerald-100 text-emerald-600'}">
                   {allOnus.some(o => ['LOS', 'Down'].includes(o.state)) ? 'АВАРИЯ' : 'НОРМА'}
                </span>
              </div>
            </button>
          {/each}
        </div>

        <div class="flex-1 flex flex-col gap-4">
          <div class="flex gap-2">
            <input type="text" bind:value={searchQuery} placeholder="Поиск по интерфейсу или договору на {currentOlt.ip}..." 
              class="flex-1 bg-white border border-slate-200 rounded-2xl px-6 py-3 shadow-sm outline-none focus:ring-2 ring-indigo-500/20 transition-all" />
            <button on:click={() => {globalLosFilter = !globalLosFilter; currentPage = 1;}} 
              class="px-6 rounded-2xl font-bold text-sm transition-all {globalLosFilter ? 'bg-red-500 text-white shadow-lg' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}">
              LOS
            </button>
          </div>

          <div class="flex-1 overflow-y-auto space-y-2 pr-2">
            {#each paginatedPorts as port}
              {@const pOnus = port.onus}
              {@const losCount = pOnus.filter(o => ['LOS', 'Down'].includes(o.state)).length}
              
              <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <div class="flex items-center justify-between pr-4 hover:bg-slate-50 transition-colors">
                  <button class="flex-1 flex items-center gap-6 p-4 text-left"
                    on:click={() => { 
                      if(activePort === port.name) { 
                        activePort = null; 
                      } else { 
                        activePort = port.name; 
                        subFilter = globalLosFilter ? 'los' : 'all'; 
                      } 
                    }}>
                    <span class="font-black text-slate-700 w-16">{port.name}</span>
                    <div class="w-48 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div class="bg-indigo-500 h-full" style="width: {((pOnus.length - losCount)/pOnus.length)*100}%"></div>
                    </div>
                    <div class="text-[11px] font-bold text-slate-400">
                      <span class={losCount > 0 ? 'text-red-500' : ''}>{losCount} ПРОБЛЕМ</span> / {pOnus.length}
                    </div>
                  </button>
                  <button on:click|stopPropagation={() => exportPortCsv(port)} class="text-[10px] bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded font-bold text-slate-500 transition-colors">CSV EXPORT</button>
                </div>

                {#if activePort === port.name}
                  <div class="p-6 bg-slate-50 border-t border-slate-100" transition:slide>
                    <div class="flex gap-4 mb-4">
                      {#each [
                        {id: 'all', label: 'Все', count: pOnus.length},
                        {id: 'online', label: 'Online', count: pOnus.filter(o => o.state === 'working').length},
                        {id: 'los', label: 'LOS/Down', count: losCount},
                        {id: 'dying', label: 'DyingGasp', count: pOnus.filter(o => o.state === 'DyingGasp').length},
                        {id: 'offline', label: 'Offline', count: pOnus.filter(o => o.state === 'Offline').length}
                      ] as filter}
                        <button on:click={() => subFilter = filter.id}
                          class="text-[10px] font-black uppercase tracking-widest pb-1 border-b-2 transition-all 
                          {subFilter === filter.id ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'}">
                          {filter.label} ({filter.count})
                        </button>
                      {/each}
                    </div>
                    <div class="grid grid-cols-5 gap-3">
                      {#each pOnus.filter(o => {
                        if (subFilter === 'online') return o.state === 'working';
                        if (subFilter === 'los') return ['LOS', 'Down'].includes(o.state);
                        if (subFilter === 'dying') return o.state === 'DyingGasp';
                        if (subFilter === 'offline') return o.state === 'Offline';
                        return true;
                      }) as onu}
                        <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                          <div class="flex justify-between items-start">
                            <span class="text-[10px] font-bold text-slate-400">{onu.id.split(':').pop()}</span>
                            <div class="w-2 h-2 rounded-full {getDotColor(onu.state)}"></div>
                          </div>
                          <div class="text-[11px] font-black mt-1 text-slate-800 truncate" title={onu.contract}>{onu.contract || '—'}</div>
                          <div class="text-[9px] font-bold uppercase mt-1 {getStatusColor(onu.state)}">{onu.state}</div>
                        </div>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
          <div class="flex justify-center items-center gap-4 py-2">
            <button disabled={currentPage === 1} on:click={() => currentPage--} class="w-10 h-10 rounded-xl border border-slate-200 bg-white flex items-center justify-center disabled:opacity-30">←</button>
            <span class="text-xs font-bold text-slate-500">СТРАНИЦА {currentPage} ИЗ {totalPages || 1}</span>
            <button disabled={currentPage >= totalPages} on:click={() => currentPage++} class="w-10 h-10 rounded-xl border border-slate-200 bg-white flex items-center justify-center disabled:opacity-30">→</button>
          </div>
        </div>
      </div>
      
    <!-- ВКЛАДКА: КОММУТАТОРЫ -->
    {:else if activeTab === 'sw'}
      <div class="flex gap-6 h-full overflow-hidden" in:fade>
        
        <!-- ЛЕВАЯ ПАНЕЛЬ ПАПОК -->
        {#if !switchSearchQuery}
          <div class="w-64 flex flex-col gap-2 overflow-y-auto pr-2" transition:slide={{ axis: 'x' }}>
            <h3 class="text-[10px] font-black text-slate-400 uppercase mb-2 px-2">Папки / Локации</h3>
            {#each switchFolders as folder, i}
              {@const downs = folder.onus.filter(s => s.state !== 'working' && s.state !== 'Host is alive').length}
              <button on:click={() => {activeFolderIndex = i;}}
                class="p-4 rounded-2xl border text-left transition-all {activeFolderIndex === i ? 'bg-white border-indigo-500 shadow-md ring-1 ring-indigo-500' : 'bg-white/50 border-slate-200 hover:bg-white'}">
                <div class="font-bold text-sm text-slate-700 truncate" title={folder.name}>{folder.name}</div>
                <div class="flex justify-between mt-1 items-center">
                  <span class="text-[10px] font-bold text-slate-400">{folder.onus.length} УЗЛОВ</span>
                  {#if downs > 0}
                    <span class="text-[9px] font-black px-1.5 py-0.5 rounded bg-red-100 text-red-600">{downs} DOWN</span>
                  {:else}
                    <span class="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-600">НОРМА</span>
                  {/if}
                </div>
              </button>
            {/each}
            {#if switchFolders.length === 0}
               <div class="text-xs text-slate-400 p-2 text-center">Папки не найдены</div>
            {/if}
          </div>
        {/if}

        <div class="flex-1 flex flex-col gap-4 overflow-hidden">
          <!-- ПОИСК ПО КОММУТАТОРАМ -->
          <div class="flex gap-2">
            <input type="text" bind:value={switchSearchQuery} placeholder="Поиск по IP или адресу (ищет по ВСЕМ папкам)..." 
              class="flex-1 bg-white border border-slate-200 rounded-2xl px-6 py-3 shadow-sm outline-none focus:ring-2 ring-indigo-500/20 transition-all" />
          </div>

          <!-- СЕТКА КОММУТАТОРОВ -->
          <div class="grid grid-cols-4 gap-4 overflow-y-auto pr-2 pb-4 content-start">
            {#each displayedSwitches as sw}
              <div class="bg-white p-5 rounded-3xl border shadow-sm transition-all flex flex-col justify-between {sw.state === 'working' || sw.state === 'Host is alive' ? 'border-slate-200 hover:border-indigo-300' : 'border-red-200 bg-red-50 hover:border-red-400'}">
                <div>
                  <div class="flex justify-between items-start mb-2">
                    <div class="font-mono font-bold text-slate-800 text-sm truncate" title={sw.id}>{sw.id}</div>
                    <div class="w-2 h-2 mt-1.5 rounded-full {getDotColor(sw.state)}"></div>
                  </div>
                  <div class="text-[11px] font-bold text-slate-400 uppercase truncate" title={sw.contract}>{sw.contract || '—'}</div>
                </div>
                
                <div class="mt-3 flex justify-between items-end gap-2">
                  <div class="text-[10px] font-black {getStatusColor(sw.state)} uppercase">{sw.state}</div>
                  <div class="text-[9px] font-bold text-slate-300 uppercase truncate text-right max-w-[50%]" title="Папка">
                    {switchFolders.find(f => f.onus.includes(sw))?.name || ''}
                  </div>
                </div>
              </div>
            {/each}
            
            {#if displayedSwitches.length === 0}
              <div class="col-span-4 text-center py-10 text-slate-400 font-bold text-sm">
                Ничего не найдено
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(body) { margin: 0; background-color: #f8fafc; height: 100vh; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>