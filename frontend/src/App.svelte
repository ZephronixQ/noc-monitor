<script>
  import { onMount, onDestroy } from 'svelte';
  import { slide, fade } from 'svelte/transition';

  // ─── Настройки подключения к локальному бэкенду ───
  const BACKEND_URL = "http://localhost:8000";
  const WS_URL = "ws://localhost:8000/ws";

  let isDark = false;
  let activeOltIndex = 0;
  let searchQuery = '';
  let globalLosFilter = false;
  
  let activePort = null; 
  let portPage = 0;
  const ONU_PER_PAGE = 50;
  
  let toasts = []; 
  let soundEnabled = true;

  // Данные с сервера
  let data = [];
  let nextUpdateTs = 0;
  let timeToNextUpdate = "00:00";
  let isUpdating = true;
  let ws;
  let timerInterval;

  function playAlert() {
    if (!soundEnabled) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const gainNode = ctx.createGain();
      gainNode.connect(ctx.destination);
      gainNode.gain.setValueAtTime(1, ctx.currentTime);
      const osc1 = ctx.createOscillator();
      osc1.type = 'sine'; osc1.frequency.setValueAtTime(587.33, ctx.currentTime); 
      osc1.connect(gainNode); osc1.start(ctx.currentTime); osc1.stop(ctx.currentTime + 0.15);
      const osc2 = ctx.createOscillator();
      osc2.type = 'sine'; osc2.frequency.setValueAtTime(783.99, ctx.currentTime + 0.1); 
      osc2.connect(gainNode); osc2.start(ctx.currentTime + 0.1); osc2.stop(ctx.currentTime + 0.3);
      gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.3);
    } catch(e) {}
  }

  $: currentDevice = data[activeOltIndex] || { ports: [] };
  $: filteredPorts = currentDevice.ports?.filter(port => {
    const hasLos = port.onus.some(o => o.state === 'LOS');
    if (globalLosFilter && !hasLos) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return port.name.toLowerCase().includes(q) || port.onus.some(o => String(o.contract).includes(q) || o.id.toLowerCase().includes(q));
    }
    return true;
  }) || [];
  
  $: paginatedPorts = filteredPorts.slice(portPage * 16, (portPage + 1) * 16);
  $: allOnus = currentDevice.ports?.flatMap(p => p.onus) || [];
  $: mTotal = allOnus.length;
  $: mOnline = allOnus.filter(o => o.state === 'working').length;
  $: mLos = allOnus.filter(o => o.state === 'LOS').length;
  $: mDying = allOnus.filter(o => o.state === 'DyingGasp').length;

  function toggleTheme() {
    isDark = !isDark;
    if (isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }

  function addToast(msg, type = 'error') {
    const id = Date.now();
    toasts = [...toasts, { id, msg, type }];
    if (type === 'error') playAlert();
    setTimeout(() => { toasts = toasts.filter(t => t.id !== id); }, 5000);
  }

  function exportCSV(port) {
    const headers = "ID,Contract/VLAN,State\n";
    const rows = port.onus.map(o => `${o.id},${o.contract},${o.state}`).join("\n");
    const blob = new Blob([headers + rows], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `export_port_${port.name.replace(/\//g, '-')}.csv`;
    link.click();
    addToast(`CSV выгружен: ${port.name}`, 'success');
  }

  function togglePort(portName) {
    if (activePort && activePort.name === portName) {
      activePort = null;
    } else {
      activePort = { name: portName, filter: globalLosFilter ? 'LOS' : 'all', page: 0 };
    }
  }

  function updateTimer() {
    if (!nextUpdateTs) return;
    const now = Math.floor(Date.now() / 1000);
    const diff = nextUpdateTs - now;
    if (diff <= 0) {
      timeToNextUpdate = "Опрос...";
      isUpdating = true;
    } else {
      const m = Math.floor(diff / 60).toString().padStart(2, '0');
      const s = (diff % 60).toString().padStart(2, '0');
      timeToNextUpdate = `${m}:${s}`;
    }
  }

  onMount(async () => {
    // 1. Грузим данные по REST при заходе
    try {
      const res = await fetch(`${BACKEND_URL}/api/data`);
      const json = await res.json();
      data = json.data;
      nextUpdateTs = json.next_update;
      isUpdating = json.is_updating;
    } catch (e) {
      addToast("Не удалось подключиться к FastAPI", "error");
    }

    // 2. Подключаем WebSocket для лайв-апдейтов
    ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "update") {
        data = msg.data;
        nextUpdateTs = msg.next_update;
        isUpdating = msg.is_updating;
        addToast("Данные успешно обновлены", "success");
      } else if (msg.type === "status") {
        isUpdating = msg.is_updating;
      }
    };
    ws.onerror = () => addToast("Ошибка WebSocket соединения", "error");

    // 3. Запускаем таймер
    timerInterval = setInterval(updateTimer, 1000);
  });

  onDestroy(() => {
    if (ws) ws.close();
    clearInterval(timerInterval);
  });
</script>

<div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
  {#each toasts as toast (toast.id)}
    <div transition:fade class="px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 text-sm font-medium text-white {toast.type === 'error' ? 'bg-red-500' : 'bg-emerald-500'}">
      {toast.msg}
    </div>
  {/each}
</div>

<header class="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-3 flex justify-between items-center shadow-sm">
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">Z</div>
    <h1 class="text-lg font-bold tracking-tight text-slate-900 dark:text-white">NOC Dashboard</h1>
  </div>
  <div class="flex items-center gap-6">
    <div class="flex items-center gap-2 text-sm font-mono font-medium px-3 py-1.5 rounded-lg border {isUpdating ? 'bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-400 animate-pulse' : 'bg-slate-50 border-slate-200 text-slate-600 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400'}">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      {isUpdating ? "Идёт опрос оборудования..." : `Обновление: ${timeToNextUpdate}`}
    </div>
    <button on:click={() => soundEnabled = !soundEnabled} class="text-xl opacity-70 hover:opacity-100 transition-opacity">
      {#if soundEnabled} 🔊 {:else} 🔇 {/if}
    </button>
    <button on:click={toggleTheme} class="text-xl p-2 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
      {#if isDark} 🌙 {:else} ☀️ {/if}
    </button>
  </div>
</header>

<main class="max-w-7xl mx-auto p-6 flex flex-col gap-6 text-slate-900 dark:text-slate-100">
  {#if data.length === 0}
    <div class="flex flex-col gap-3 justify-center items-center h-64 text-slate-500 font-mono">
      <div class="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      Подключение к серверу и первый опрос оборудования...
    </div>
  {:else}
    <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
      {#each data as olt, i}
        {@const devOnus = olt.ports?.flatMap(p => p.onus) || []}
        {@const devTotal = devOnus.length}
        {@const devOnline = devOnus.filter(o => o.state === 'working').length}
        {@const devLos = devOnus.filter(o => o.state === 'LOS').length}
        {@const isCrit = devLos > (devTotal * 0.15)}
        {@const statusText = isCrit ? 'Критично' : (devLos > 0 ? 'Авария' : (devTotal === 0 ? 'Нет данных' : 'В норме'))}
        {@const statusColor = isCrit ? 'text-red-500' : (devLos > 0 ? 'text-amber-500' : (devTotal===0 ? 'text-slate-400' : 'text-emerald-500'))}
        {@const dotColor = isCrit ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' : (devLos > 0 ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]' : (devTotal===0 ? 'bg-slate-400' : 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]'))}

        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <div on:click={() => { activeOltIndex = i; portPage = 0; activePort = null; }}
             class="flex flex-col min-w-[210px] p-3 rounded-xl border cursor-pointer transition-all
             {activeOltIndex === i ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 shadow-sm' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-500'}">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div class="w-2.5 h-2.5 rounded-full {dotColor}"></div>
              <span class="font-mono text-sm font-bold">{olt.ip}</span>
            </div>
            <div class="text-xs text-slate-500 font-medium px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded-md">
              {olt.isSwitch ? 'SW' : 'OLT'}
            </div>
          </div>
          <div class="mt-1 pt-2 border-t border-slate-100 dark:border-slate-700/50 flex justify-between items-center text-[13px] font-mono">
            <div class="text-slate-600 dark:text-slate-300">{devOnline}/{devTotal}</div>
            <div class="{statusColor} font-bold text-xs">{olt.error ? "Ошибка связи" : statusText}</div>
          </div>
        </div>
      {/each}
    </div>

    <!-- Поиск и фильтры -->
    <div class="flex flex-wrap gap-3 items-center">
      <input type="text" bind:value={searchQuery} on:input={() => portPage = 0} placeholder="Поиск интерфейса или договора..." class="flex-1 min-w-[250px] px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50" />
      <button on:click={() => {globalLosFilter = !globalLosFilter; activePort = null; portPage = 0;}} 
              class="px-4 py-2 rounded-lg font-medium border {globalLosFilter ? 'bg-red-100 border-red-300 text-red-700 dark:bg-red-900/30 dark:border-red-500/50 dark:text-red-400' : 'bg-white border-slate-200 dark:bg-slate-800 dark:border-slate-700'}">
        Только аварийные (LOS/Down)
      </button>
    </div>

    <!-- Порты -->
    <div class="flex flex-col gap-3">
      {#if currentDevice.error}
        <div class="p-6 text-center text-red-500 bg-red-50 border border-red-200 rounded-xl dark:bg-red-900/20 dark:border-red-800/50">
          Ошибка при опросе оборудования: {currentDevice.error}
        </div>
      {/if}

      {#each paginatedPorts as port (port.name)}
        {@const losCount = port.onus.filter(o => o.state === 'LOS').length}
        {@const isAlert = currentDevice.isSwitch ? losCount > port.onus.length / 2 : losCount >= 8}
        {@const isOpen = activePort && activePort.name === port.name}

        <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-sm">
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <div class="flex items-center gap-4 p-3.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50" on:click={() => togglePort(port.name)}>
            <span class="font-mono font-bold w-24 text-sm">{port.name}</span>
            <div class="flex-1 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500 {isAlert ? 'bg-red-500' : losCount > 0 ? 'bg-amber-500' : 'bg-emerald-500'}" style="width: {Math.max((losCount / port.onus.length) * 100, 2)}%;"></div>
            </div>
            <div class="text-sm text-slate-500 min-w-[140px] text-right">
              {losCount} {currentDevice.isSwitch ? 'Down' : 'LOS'} / {port.onus.length}
            </div>
          </div>
          
          {#if isOpen}
             {@const filteredOnus = port.onus.filter(o => activePort.filter === 'all' || o.state === activePort.filter)}
             {@const displayedOnus = filteredOnus.slice(activePort.page * ONU_PER_PAGE, (activePort.page + 1) * ONU_PER_PAGE)}
             <div class="border-t border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 p-4">
                 
                 <div class="flex flex-wrap gap-2 mb-3">
                   {#each [{id:'all',l:`Все (${port.onus.length})`}, {id:'working',l:`Online (${port.onus.filter(o=>o.state==='working').length})`}, {id:'LOS',l:`LOS (${port.onus.filter(o=>o.state==='LOS').length})`}, {id:'DyingGasp',l:`Dying Gasp (${port.onus.filter(o=>o.state==='DyingGasp').length})`}, {id:'OffLine',l:`Offline (${port.onus.filter(o=>o.state==='OffLine').length})`}] as f}
                     <button on:click={() => { activePort.filter = f.id; activePort.page = 0; }} class="px-3 py-1.5 text-xs font-semibold rounded-lg border {activePort.filter === f.id ? 'bg-white shadow-sm dark:bg-slate-700' : 'border-transparent text-slate-500'}">
                       {f.l}
                     </button>
                   {/each}
                   <button on:click={() => exportCSV(port)} class="ml-auto text-xs font-bold text-blue-600 bg-blue-100 px-3 py-1.5 rounded-lg">📥 CSV</button>
                 </div>

                 <div class="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                   <table class="w-full text-left text-sm">
                     <thead class="bg-slate-50 dark:bg-slate-800/80 text-xs uppercase text-slate-500">
                       <tr><th class="px-4 py-3">ID</th><th class="px-4 py-3">Договор</th><th class="px-4 py-3 text-right">Статус</th></tr>
                     </thead>
                     <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">
                       {#each displayedOnus as onu}
                         <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                           <td class="px-4 py-2.5 font-mono text-slate-500">{onu.id}</td>
                           <td class="px-4 py-2.5 font-medium">{onu.contract}</td>
                           <td class="px-4 py-2.5 text-right font-semibold {onu.state === 'working' ? 'text-emerald-500' : onu.state === 'LOS' ? 'text-red-500' : 'text-slate-400'}">
                             {onu.state}
                           </td>
                         </tr>
                       {/each}
                     </tbody>
                   </table>
                 </div>
             </div>
          {/if}
        </div>
      {/each}

      <!-- Пагинация портов/интерфейсов -->
      {#if filteredPorts.length > 16}
        {@const totalPortPages = Math.ceil(filteredPorts.length / 16)}
        <div class="flex justify-between items-center mt-2 px-1 text-sm text-slate-500 dark:text-slate-400">
          <span>Интерфейсы {portPage * 16 + 1}–{Math.min((portPage + 1) * 16, filteredPorts.length)} из {filteredPorts.length}</span>
          <div class="flex gap-1">
            <button 
              disabled={portPage === 0} 
              on:click={() => portPage--} 
              class="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors bg-white dark:bg-slate-800">
              ← Назад
            </button>
            <div class="px-3 py-1.5 font-bold bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              {portPage + 1} / {totalPortPages}
            </div>
            <button 
              disabled={portPage >= totalPortPages - 1} 
              on:click={() => portPage++} 
              class="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors bg-white dark:bg-slate-800">
              Вперед →
            </button>
          </div>
        </div>
      {/if}

    </div>

    <!-- Метрики подвала -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
      <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700"><div class="text-sm font-medium text-slate-500">Всего линков</div><div class="text-3xl font-bold">{mTotal}</div></div>
      <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700"><div class="text-sm font-medium text-slate-500">В работе</div><div class="text-3xl font-bold text-emerald-500">{mOnline}</div></div>
      <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700"><div class="text-sm font-medium text-slate-500">Аварии (LOS)</div><div class="text-3xl font-bold text-red-500">{mLos}</div></div>
      <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700"><div class="text-sm font-medium text-slate-500">Dying Gasp</div><div class="text-3xl font-bold text-amber-500">{mDying}</div></div>
    </div>
  {/if}
</main>