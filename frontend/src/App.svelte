<svelte:head>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</svelte:head>

<script>
  import { onMount, tick } from 'svelte';
  import { slide, fade, scale } from 'svelte/transition';
  
  // let host = "localhost"; 
  let isDark = false;
  let wsConnected = false;

  // --- ПЕРЕМЕННЫЕ ДЛЯ СТАТИСТИКИ И ИСТОРИИ ---
  let dailyStats = { total_24h: 0, avg_repair_minutes: 0, active_now: 0 };
  let selectedEntity = null; 
  let entityHistory = [];
  let isHistoryLoading = false;
  let isModalOpen = false;

  // --- НОВОЕ: УВЕДОМЛЕНИЯ И ОБНОВЛЕНИЯ ---
  let notifications = [];
  let showNotifications = false;
  let unreadCount = 0;
  
  // Храним полное состояние
  let knownState = { massOlt: 0, massSw: 0, downSwitches: new Map(), downOnus: new Map() };
  let isFirstLoad = true; 

  function sendPushNotification(title, body) {
    if ("Notification" in window && Notification.permission === "granted") {
      
      // Считаем критичными все аварии, падения и массовые события
      const isCritical = title.includes("АВАРИЯ") || title.includes("ПАДЕНИЕ") || title.includes("УПАЛ");

      const options = {
        body: body,
        icon: '/favicon.ico', // Иконка поможет ОС считать пуш доверенным
        requireInteraction: isCritical, // ОС (Windows/Mac) не скроет пуш автоматически!
        silent: false // Обязательно со звуком
      };

      const notification = new Notification(title, options);

      // Если кликнуть по пушу в Windows/Mac - браузер сам откроет эту вкладку
      notification.onclick = function() {
        window.focus(); // Фокусируемся на вкладке NOC
        this.close();   // Закрываем пуш
      };
    }
  }

  // ОБНОВЛЕНО: Поддержка закрепления и автоудаления
  function addNotification(type, title, body) {
    const isMassOutage = title.includes('МАССОВАЯ');
    const id = Date.now() + Math.random(); // Уникальный ID
    let timeoutId = null;

    // Если это массовая авария, удаляем ее автоматически через 10 минут
    if (isMassOutage) {
      timeoutId = setTimeout(() => {
        removeNotification(id);
      }, 10 * 60 * 1000); // 10 минут
    }

    const newNotif = { id, type, title, body, time: new Date(), pinned: isMassOutage, timeoutId };
    
    notifications = [newNotif, ...notifications].slice(0, 100);
    unreadCount++;
    sendPushNotification(title, body);
  }

  // НОВОЕ: Удаление конкретного уведомления
  function removeNotification(id) {
    notifications = notifications.filter(n => {
      if (n.id === id && n.timeoutId) clearTimeout(n.timeoutId);
      return n.id !== id;
    });
  }

  // НОВОЕ: Очистка всех уведомлений (сброс таймеров)
  function clearAllNotifications() {
    notifications.forEach(n => { if (n.timeoutId) clearTimeout(n.timeoutId); });
    notifications = [];
  }

  function toggleNotifications() {
    showNotifications = !showNotifications;
    if (showNotifications) unreadCount = 0;
  }

  // Реактивная сортировка: Закрепленные всегда сверху, остальные по времени
  $: sortedNotifications = [...notifications].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return b.time - a.time;
  });

  // Расширенная функция анализа изменений
  function analyzeDataChanges(newData) {
    let currentMassOlt = 0; let currentMassSw = 0;
    let currentDownSwitches = new Map();
    let currentDownOnus = new Map();

    // 1. Собираем свежие данные
    newData.forEach(d => {
      if (d.isSwitch) {
        d.ports.forEach(folder => {
          if (folder.is_mass_outage) currentMassSw++;
          folder.onus.forEach(sw => {
            const state = (sw.state || '').toLowerCase();
            if (!['working', 'host is alive'].includes(state)) {
              currentDownSwitches.set(sw.id, sw.contract || '—');
            }
          });
        });
      } else {
        d.ports.forEach(port => {
          if (port.is_mass_outage) currentMassOlt++;
          port.onus.forEach(onu => {
            const state = (onu.state || '').toLowerCase();
            // Собираем ТОЛЬКО los, down и losi для уведомлений
            if (['los', 'down', 'losi'].includes(state)) {
              currentDownOnus.set(`${d.ip}:${onu.id}`, { contract: onu.contract || '—', state: state });
            }
          });
        });
      }
    });

    // 2. Сравниваем с предыдущим состоянием (ТОЛЬКО если это не первая загрузка)
    if (!isFirstLoad) {
      
      // -- Массовые очаги OLT/Папок (по флагам бекенда) --
      if (currentMassOlt > knownState.massOlt) {
        addNotification('critical', 'МАССОВАЯ АВАРИЯ OLT', `Зафиксировано ${currentMassOlt} очагов GPON.`);
      }
      if (currentMassSw > knownState.massSw) {
        addNotification('critical', 'МАССОВАЯ АВАРИЯ SW', `Зафиксировано ${currentMassSw} локаций коммутаторов.`);
      }

      // === АНТИ-СПАМ ЛОГИКА ===
      let newDownSw = []; let upSw = [];
      let newDownOnu = []; let upOnu = [];

      // Собираем списки изменений
      currentDownSwitches.forEach((contract, id) => { if (!knownState.downSwitches.has(id)) newDownSw.push(id); });
      knownState.downSwitches.forEach((contract, id) => { if (!currentDownSwitches.has(id)) upSw.push(id); });
      
      currentDownOnus.forEach((data, id) => { if (!knownState.downOnus.has(id)) newDownOnu.push({id, contract: data.contract, state: data.state}); });
      knownState.downOnus.forEach((data, id) => { if (!currentDownOnus.has(id)) upOnu.push({id, contract: data.contract}); });

      // ПОРОГИ СРАБАТЫВАНИЯ (Свыше какого количества схлопывать в одно уведомление)
      const SW_LIMIT = 5;  
      const ONU_LIMIT = 10; 

      // -- Обработка коммутаторов --
      if (newDownSw.length > SW_LIMIT) {
        addNotification('critical', `МАССОВОЕ ПАДЕНИЕ SW`, `Сразу ${newDownSw.length} коммутаторов недоступны.\nВозможно потеря SNMP пакетов или падение магистрали.`);
      } else {
        newDownSw.forEach(id => addNotification('critical', `УПАЛ КОММУТАТОР`, `🔌 IP-адрес: ${id}`));
      }

      if (upSw.length > SW_LIMIT) {
        addNotification('success', `МАССОВОЕ ВОССТАНОВЛЕНИЕ SW`, `Сразу ${upSw.length} коммутаторов вернулись в сеть.`);
      } else {
        upSw.forEach(id => addNotification('success', `КОММУТАТОР В СЕТИ`, `🔌 IP-адрес: ${id}`));
      }

      // -- Обработка GPON клиентов --
      if (newDownOnu.length > ONU_LIMIT) {
        addNotification('warning', `МАССОВЫЙ ОТВАЛ (GPON)`, `Сразу ${newDownOnu.length} клиентов отвалились (LOS/LOSi).`);
      } else {
        newDownOnu.forEach(onu => {
          const p = onu.id.split(':');
          const route = p.length === 3 ? `[${p[0]}] ➔ [${p[1]}] ➔ ONU ${p[2]}` : onu.id;
          const statusName = onu.state.toUpperCase();
          addNotification('warning', `АВАРИЯ GPON (${statusName})`, `👤 Договор: ${onu.contract}\n🔌 Маршрут: ${route}`);
        });
      }

      if (upOnu.length > ONU_LIMIT) {
        addNotification('success', `МАССОВОЕ ВОССТАНОВЛЕНИЕ GPON`, `Сразу ${upOnu.length} клиентов вернулись в сеть.`);
      } else {
        upOnu.forEach(onu => {
          const p = onu.id.split(':');
          const route = p.length === 3 ? `[${p[0]}] ➔ [${p[1]}] ➔ ONU ${p[2]}` : onu.id;
          addNotification('success', `GPON КЛИЕНТ В СЕТИ`, `👤 Договор: ${onu.contract}\n🔌 Маршрут: ${route}`);
        });
      }
    }

    // 3. Сохраняем текущее состояние как эталон
    knownState.massOlt = currentMassOlt;
    knownState.massSw = currentMassSw;
    knownState.downSwitches = currentDownSwitches;
    knownState.downOnus = currentDownOnus;
    isFirstLoad = false;
  }

  async function forceUpdate() {
    if (isUpdating) return;
    try {
      isUpdating = true;
      await fetch(`${BACKEND_URL}/api/update/force`, { method: 'POST' });
    } catch(e) { console.error("Ошибка принудительного обновления:", e); }
  }

  onMount(() => { 
    // host = window.location.hostname; 
    const storedTheme = localStorage.getItem('noc-theme');
    if (storedTheme) isDark = storedTheme === 'dark';
    else isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if ("Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {
      Notification.requestPermission();
    }
  });

  function toggleTheme() {
    isDark = !isDark;
    localStorage.setItem('noc-theme', isDark ? 'dark' : 'light');
  }

  $: BACKEND_URL = `http://${host}:8000`;
  $: WS_URL = `ws://${host}:8000/ws`;

  let activeTab = 'dash'; 
  let activeOltIndex = 0;
  let activeFolderIndex = 0;
  
  let searchQuery = ''; 
  let switchSearchQuery = ''; 
  
  let globalLosFilter = false;
  let globalLosiFilter = false;
  let globalSwLosFilter = false;
  let activePort = null;
  let subFilter = 'all'; 

  let currentPage = 1;
  const itemsPerPage = 16;

  let data = [];
  let nextUpdateTs = 0;
  let timeToNextUpdate = "00:00";
  let isUpdating = true;

  let currentUnixTime = Math.floor(Date.now() / 1000);
  setInterval(() => { currentUnixTime = Math.floor(Date.now() / 1000); }, 60000);

  // --- API ВЫЗОВЫ ---
  async function fetchDailyStats() {
    try {
      const res = await fetch(`${BACKEND_URL}/api/stats/daily`);
      dailyStats = await res.json();
    } catch(e) { console.error("Ошибка загрузки отчета:", e); }
  }

  let activeHistoryRequest = null;
  async function openHistory(contract, id, type = 'sw') {
    if (type !== 'sw') return; 
    if (!contract || contract === '—') return;
    
    if (isHistoryLoading) return;
    
    selectedEntity = { contract, id, type };
    isHistoryLoading = true;
    isModalOpen = true;
    
    try {
      const controller = new AbortController();
      activeHistoryRequest = controller; 
      
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 5000); 

      const res = await fetch(`${BACKEND_URL}/api/history/${encodeURIComponent(id)}?days=30`, {
        signal: controller.signal,
        cache: 'no-store' 
      });
      
      clearTimeout(timeoutId);

      if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
      
      const json = await res.json();
      entityHistory = json.incidents || []; 
      
    } catch(e) {
      console.error("❌ Ошибка загрузки истории:", e);
      entityHistory = []; 
    } finally {
      isHistoryLoading = false; 
      activeHistoryRequest = null;
    }
  }

  function closeHistory() {
    if (activeHistoryRequest) {
      activeHistoryRequest.abort();
      activeHistoryRequest = null;
    }
    
    isModalOpen = false;
    setTimeout(() => { 
      selectedEntity = null; 
      entityHistory = []; 
      isHistoryLoading = false; 
    }, 300);
  }

  function exportPortCsv(port) {
    if (!port || !port.onus) return;
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "ID,Договор/Адрес,Статус\n";
    port.onus.forEach(onu => {
      const id = onu.id || '';
      const contract = onu.contract || '';
      const state = onu.state || '';
      csvContent += `"${id}","${contract}","${state}"\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `export_port_${port.name}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // --- ДАННЫЕ СЕТИ ---
  $: olts = data.filter(d => !d.isSwitch);

  $: filteredOlts = olts.filter(olt => {
    if (globalLosFilter) return olt.ports.some(p => p.onus.some(o => ['los', 'down'].includes((o.state||'').toLowerCase())));
    if (globalLosiFilter) return olt.ports.some(p => p.onus.some(o => (o.state||'').toLowerCase() === 'losi'));
    return true;
  });
  
  $: if (activeOltIndex >= filteredOlts.length) activeOltIndex = 0;
  $: currentOlt = filteredOlts[activeOltIndex] || { ports: [] };

  $: filteredPorts = (currentOlt.ports || [])
    .filter(port => {
      const hasLos = port.onus.some(o => ['los', 'down'].includes((o.state||'').toLowerCase()));
      const hasLosi = port.onus.some(o => (o.state||'').toLowerCase() === 'losi');
      
      if (globalLosFilter && !hasLos) return false;
      if (globalLosiFilter && !hasLosi) return false;
      
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return port.name.toLowerCase().includes(q) || port.onus.some(o => (o.contract || '').toLowerCase().includes(q));
    })
    .sort((a, b) => {
      if (a.is_mass_outage && !b.is_mass_outage) return -1;
      if (!a.is_mass_outage && b.is_mass_outage) return 1;
      const badA = a.onus.filter(o => ['los', 'down', 'losi'].includes((o.state||'').toLowerCase())).length;
      const badB = b.onus.filter(o => ['los', 'down', 'losi'].includes((o.state||'').toLowerCase())).length;
      return badB - badA; 
    });

  $: paginatedPorts = filteredPorts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  $: totalPages = Math.ceil(filteredPorts.length / itemsPerPage);

  $: switchDataNode = data.find(d => d.isSwitch) || { ports: [] };
  $: switchFolders = switchDataNode.ports || [];

  $: filteredSwitchFolders = switchFolders.filter(folder => {
    if (!globalSwLosFilter) return true;
    return folder.onus.some(sw => !['working', 'host is alive'].includes((sw.state||'').toLowerCase()));
  });

  $: if (activeFolderIndex >= filteredSwitchFolders.length) activeFolderIndex = 0;
  $: currentSwitchFolder = filteredSwitchFolders[activeFolderIndex] || { onus: [] };
  $: allSwitchesFlat = switchFolders.flatMap(folder => folder.onus || []);

  $: displayedSwitches = switchSearchQuery 
    ? allSwitchesFlat.filter(sw => sw.id.toLowerCase().includes(switchSearchQuery.toLowerCase()) || (sw.contract || '').toLowerCase().includes(switchSearchQuery.toLowerCase()))
    : (currentSwitchFolder.onus || []).filter(sw => !globalSwLosFilter || !['working', 'host is alive'].includes((sw.state||'').toLowerCase()));

  $: totalStats = {
    onus: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).length, 0),
    online: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => o.state === 'working').length, 0),
    los: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => ['los', 'down'].includes((o.state||'').toLowerCase())).length, 0),
    losi: olts.reduce((acc, olt) => acc + olt.ports.flatMap(p => p.onus).filter(o => (o.state||'').toLowerCase() === 'losi').length, 0),
    olts: olts.length,
    switches: allSwitchesFlat.length,
    swUp: allSwitchesFlat.filter(sw => sw.state === 'working' || sw.state === 'Host is alive').length,
    massOlt: olts.reduce((acc, olt) => acc + olt.ports.filter(p => p.is_mass_outage).length, 0),
    massSw: switchFolders.filter(f => f.is_mass_outage).length
  };

  // --- НОВОЕ: БЕЗОПАСНЫЙ ГЛОБАЛЬНЫЙ ПОИСК (БЕЗ ЗАЦИКЛИВАНИЙ) ---
  function handleSearch() {
    // Небольшая задержка, чтобы svelte успел обновить searchQuery
    setTimeout(() => {
      if (!searchQuery || searchQuery.trim().length < 4) return;
      const q = searchQuery.trim().toLowerCase();
      let found = false;

      for (let i = 0; i < olts.length; i++) {
        const olt = olts[i];
        for (let j = 0; j < olt.ports.length; j++) {
          const port = olt.ports[j];
          for (let k = 0; k < port.onus.length; k++) {
            const onu = port.onus[k];
            const contract = (onu.contract || '').toLowerCase();
            
            if (contract.includes(q)) {
              const s = (onu.state || '').toLowerCase();
              const isLos = ['los', 'down'].includes(s);
              const isLosi = s === 'losi';

              // Отключаем мешающие глобальные фильтры
              if (globalLosFilter && !isLos) globalLosFilter = false;
              if (globalLosiFilter && !isLosi) globalLosiFilter = false;

              tick().then(() => {
                // Прыгаем на нужную OLT
                const visibleOltIndex = filteredOlts.findIndex(o => o.ip === olt.ip);
                if (visibleOltIndex !== -1) activeOltIndex = visibleOltIndex;
                
                // Выбираем правильную под-категорию
                if (isLos) subFilter = 'los';
                else if (isLosi) subFilter = 'losi';
                else if (s === 'dyinggasp') subFilter = 'dying';
                else if (s === 'offline') subFilter = 'offline';
                else if (s === 'working' || s === 'host is alive') subFilter = 'online';
                else subFilter = 'all';

                tick().then(() => {
                  // Раскрываем порт и перелистываем страницу к нему
                  activePort = port.name;
                  const pIndex = filteredPorts.findIndex(p => p.name === port.name);
                  if (pIndex !== -1) currentPage = Math.floor(pIndex / itemsPerPage) + 1;
                });
              });

              found = true; 
              break;
            }
          }
          if (found) break;
        }
        if (found) break;
      }
    }, 10);
  }

  // --- ГРАФИКИ ---
  let chartCanvas;
  let chartInstance = null;
  let historyLabels = [];
  let historyData = [];

  $: if (chartInstance) updateChartTheme(isDark);

  function chartSetup(node) {
    chartCanvas = node;
    const checkChart = setInterval(() => {
      if (window.Chart) {
        clearInterval(checkChart);
        initChart();
      }
    }, 50);

    return {
      destroy() {
        if (chartInstance) {
          chartInstance.destroy();
          chartInstance = null;
        }
        clearInterval(checkChart);
      }
    };
  }

  function updateChartTheme(dark) {
    if (!chartInstance) return;
    const gridColor = dark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = dark ? '#94a3b8' : '#64748b';
    const lineColor = dark ? '#6366f1' : '#4f46e5';
    const bgColor = dark ? 'rgba(99, 102, 241, 0.2)' : 'rgba(79, 70, 229, 0.1)';

    chartInstance.data.datasets[0].borderColor = lineColor;
    chartInstance.data.datasets[0].backgroundColor = bgColor;
    chartInstance.data.datasets[0].pointBackgroundColor = dark ? '#1e293b' : '#ffffff';
    chartInstance.data.datasets[0].pointBorderColor = lineColor;
    
    if(!chartInstance.options.scales.x) chartInstance.options.scales.x = { grid: {}, ticks: {} };
    if(!chartInstance.options.scales.y) chartInstance.options.scales.y = { beginAtZero: true, suggestedMin: 0, grid: {}, ticks: {} };
    
    chartInstance.options.scales.x.grid.color = gridColor;
    chartInstance.options.scales.x.ticks.color = textColor;
    chartInstance.options.scales.y.grid.color = gridColor;
    chartInstance.options.scales.y.ticks.color = textColor;
    chartInstance.update();
  }

  function initChart() {
    if (!chartCanvas) return;
    chartInstance = new Chart(chartCanvas, {
      type: 'line',
      data: { labels: historyLabels, datasets: [{ label: 'Потери', data: historyData, fill: true, tension: 0.4, borderWidth: 3, pointRadius: 4 }] },
      options: { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } }, interaction: { mode: 'nearest', axis: 'x', intersect: false } }
    });
    updateChartTheme(isDark);
  }

  function redrawChart() {
    if (chartInstance) {
      chartInstance.data.labels = historyLabels;
      chartInstance.data.datasets[0].data = historyData;
      chartInstance.update();
    }
  }

  async function updateChartData() {
    await tick(); 
    const now = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    const currentOutages = totalStats.los + totalStats.losi; // Учитываем LOS + LOSi
    
    if (historyLabels.length > 0 && historyLabels[historyLabels.length - 1] === now) {
      historyData[historyData.length - 1] = currentOutages;
    } else {
      if (historyLabels.length > 30) { historyLabels.shift(); historyData.shift(); }
      historyLabels.push(now);
      historyData.push(currentOutages);
    }
    
    localStorage.setItem('noc_chart_labels', JSON.stringify(historyLabels));
    localStorage.setItem('noc_chart_data', JSON.stringify(historyData));

    redrawChart();
  }

  const setTab = (tab) => { 
    activeTab = tab; activePort = null; currentPage = 1; 
  };
  
  const formatLosTime = (startTs) => {
    if (!startTs) return '';
    const diff = currentUnixTime - startTs;
    if (diff < 0) return 'Только что';
    const h = Math.floor(diff / 3600);
    const m = Math.floor((diff % 3600) / 60);
    return h > 0 ? `${h}ч ${m}м` : `${m}м`;
  };

  const getStatusColor = (state) => {
    if (!state) return 'text-slate-500';
    const s = state.toLowerCase();
    if (s === 'working' || s === 'host is alive') return 'text-emerald-500';
    if (s === 'dyinggasp') return 'text-orange-500';
    if (s === 'losi') return 'text-fuchsia-500'; // НОВОЕ
    return 'text-red-500';
  };

  const getDotColor = (state) => {
    if (!state) return 'bg-slate-500';
    const s = state.toLowerCase();
    if (s === 'working' || s === 'host is alive') return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
    if (s === 'dyinggasp') return 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]';
    if (s === 'losi') return 'bg-fuchsia-500 shadow-[0_0_8px_rgba(217,70,239,0.5)] animate-pulse'; // НОВОЕ
    return 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)] animate-pulse';
  };

  function updateTimer() {
    if (!nextUpdateTs) return;
    const diff = nextUpdateTs - Math.floor(Date.now() / 1000);
    timeToNextUpdate = diff <= 0 ? "00:00" : `${Math.floor(diff/60)}:${(diff%60).toString().padStart(2,'0')}`;
  }

let ws;
  function connectWebSocket() {
    if (ws) ws.close();
    ws = new WebSocket(WS_URL);
    ws.onopen = () => { wsConnected = true; };
    ws.onmessage = async (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "update") {
        analyzeDataChanges(msg.data); 
        data = msg.data; nextUpdateTs = msg.next_update; isUpdating = msg.is_updating;
        if (!msg.is_sw_only) await updateChartData();
      } else if (msg.type === "status") { 
        isUpdating = msg.is_updating;
      }
    };
    ws.onclose = () => {
      wsConnected = false; 
      setTimeout(connectWebSocket, 1000);
    };
    ws.onerror = () => { ws.close(); };
  }

  onMount(async () => {
    try {
      const savedLabels = localStorage.getItem('noc_chart_labels');
      const savedData = localStorage.getItem('noc_chart_data');
      if (savedLabels && savedData) {
        historyLabels = JSON.parse(savedLabels);
        historyData = JSON.parse(savedData);
      }
    } catch(e) { console.error("Ошибка чтения истории графика:", e); }

    try {
      const res = await fetch(`${BACKEND_URL}/api/data`);
      const json = await res.json();
      data = json.data; nextUpdateTs = json.next_update; isUpdating = json.is_updating;
      await tick();
      redrawChart();
    } catch(e) {}

    fetchDailyStats();
    setInterval(fetchDailyStats, 300000); 
    connectWebSocket();
    setInterval(updateTimer, 1000);
  });
</script>

<!-- Модальное окно истории -->
{#if isModalOpen}
  <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" in:fade={{duration: 200}} out:fade={{duration: 200}}>
    <div class="w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] {isDark ? 'bg-slate-900 border border-slate-700' : 'bg-white'}" in:scale={{start: 0.95, duration: 200}}>
      
      <!-- Хедер модалки -->
      <div class="px-6 py-5 border-b flex justify-between items-center bg-gradient-to-r {isDark ? 'from-slate-800 to-slate-900 border-slate-700' : 'from-slate-50 to-white border-slate-200'}">
        <div>
          <h2 class="text-lg font-black tracking-tight {isDark ? 'text-white' : 'text-slate-900'}">История подключений</h2>
          <div class="text-xs font-bold text-indigo-500 mt-1">{selectedEntity?.contract} <span class="text-slate-400">({selectedEntity?.id})</span></div>
        </div>
        <button on:click={closeHistory} class="w-8 h-8 flex items-center justify-center rounded-full bg-slate-200/50 hover:bg-slate-300 transition-colors {isDark ? 'bg-slate-800 text-slate-400 hover:text-white' : 'text-slate-600'}">✕</button>
      </div>

      <!-- Тело модалки -->
      <div class="p-6 overflow-y-auto flex-1 {isDark ? 'bg-slate-900' : 'bg-slate-50'} always-visible-scroll">
        {#if isHistoryLoading}
          <div class="flex flex-col items-center justify-center py-12 opacity-50">
            <div class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <span class="text-sm font-bold {isDark ? 'text-slate-400' : 'text-slate-500'}">Загрузка данных из БД...</span>
          </div>
        {:else if entityHistory.length === 0}
          <div class="text-center py-12">
            <div class="text-4xl mb-2">✨</div>
            <h3 class="text-sm font-bold {isDark ? 'text-slate-300' : 'text-slate-700'}">Идеальная связь</h3>
            <p class="text-xs mt-1 {isDark ? 'text-slate-500' : 'text-slate-400'}">За последние 30 дней падений не зафиксировано.</p>
          </div>
        {:else}
          <div class="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent {isDark ? 'before:via-slate-700' : ''}">
            {#each entityHistory as event}
              <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm {event.end_time ? (isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200') : 'bg-red-500 border-red-200 animate-pulse'}">
                  <span class="text-xs">{event.end_time ? '✅' : '🚨'}</span>
                </div>
                
                <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border shadow-sm transition-colors {isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'}">
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-[10px] font-black uppercase {event.end_time ? 'text-emerald-500' : 'text-red-500'}">
                      {event.end_time ? 'Восстановлено' : 'АКТИВНАЯ АВАРИЯ'}
                    </span>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 {isDark ? 'bg-slate-700 text-slate-300' : 'text-slate-600'}">
                      {Math.floor(event.duration / 60)} мин
                    </span>
                  </div>
                  <div class="text-xs font-bold {isDark ? 'text-slate-300' : 'text-slate-700'}">Начало: <span class="font-normal">{event.start_human}</span></div>
                  {#if event.end_time}
                    <div class="text-xs font-bold {isDark ? 'text-slate-300' : 'text-slate-700'}">Конец: <span class="font-normal">{event.end_human}</span></div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<div class="h-screen w-full overflow-hidden font-sans flex flex-col transition-colors duration-200 {isDark ? 'bg-[#0b1120] text-slate-200' : 'bg-slate-50 text-slate-900'} relative">
  <header class="h-14 shrink-0 flex items-center justify-between px-6 sticky top-0 z-40 shadow-sm backdrop-blur-md border-b {isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white/80 border-slate-200'}">
    <div class="flex items-center gap-8">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center font-black text-white bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md">N</div>
        <span class="font-black tracking-tight text-lg {isDark ? 'text-white' : 'text-slate-900'}">NOC <span class="text-indigo-500">MONITOR</span></span>
      </div>
      <nav class="flex gap-1 p-1 rounded-lg {isDark ? 'bg-slate-800/50' : 'bg-slate-100'}">
        <button on:click={() => setTab('dash')} class="px-5 py-1.5 rounded-md text-[11px] font-black tracking-wide transition-all {activeTab === 'dash' ? 'bg-indigo-500 text-white shadow-md' : 'text-slate-500 hover:text-indigo-500'}">ОБЗОР</button>
        <button on:click={() => setTab('olt')} class="px-5 py-1.5 rounded-md text-[11px] font-black tracking-wide transition-all {activeTab === 'olt' ? 'bg-indigo-500 text-white shadow-md' : 'text-slate-500 hover:text-indigo-500'}">GPON</button>
        <button on:click={() => setTab('sw')} class="px-5 py-1.5 rounded-md text-[11px] font-black tracking-wide transition-all {activeTab === 'sw' ? 'bg-indigo-500 text-white shadow-md' : 'text-slate-500 hover:text-indigo-500'}">КОММУТАТОРЫ</button>
      </nav>
    </div>
    
    <div class="flex items-center gap-4 relative">
      
      <button on:click={toggleNotifications} class="relative w-8 h-8 rounded-full flex items-center justify-center transition-colors {isDark ? 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/></svg>
        {#if unreadCount > 0}
          <span class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-black text-white shadow-md animate-bounce">{unreadCount}</span>
        {/if}
      </button>

      {#if showNotifications}
        <div class="absolute top-12 right-12 w-80 rounded-2xl shadow-2xl border overflow-hidden flex flex-col z-50 {isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}" transition:slide={{duration: 200}}>
          <div class="px-4 py-3 border-b flex justify-between items-center {isDark ? 'border-slate-800 bg-slate-800/50' : 'border-slate-100 bg-slate-50'}">
            <span class="text-xs font-black tracking-wider uppercase {isDark ? 'text-slate-300' : 'text-slate-600'}">Уведомления</span>
            <button on:click={clearAllNotifications} class="text-[10px] font-bold text-indigo-500 hover:underline">Очистить</button>
          </div>
          <div class="max-h-80 overflow-y-auto always-visible-scroll p-2">
            {#if sortedNotifications.length === 0}
              <div class="text-center py-8 text-xs font-bold opacity-50 {isDark ? 'text-slate-400' : 'text-slate-500'}">Нет новых событий</div>
            {:else}
              {#each sortedNotifications as notif (notif.id)}
                <div class="relative p-3 mb-2 last:mb-0 rounded-xl text-left border transition-all
                  {notif.pinned ? 'shadow-md border-l-4 border-l-red-500 ' : ''}
                  {notif.type === 'critical' ? (isDark ? 'bg-red-900/20 border-red-900/50' : 'bg-red-50 border-red-100') : 
                   notif.type === 'success' ? (isDark ? 'bg-emerald-900/20 border-emerald-900/50' : 'bg-emerald-50 border-emerald-100') :
                   notif.type === 'warning' ? (isDark ? 'bg-orange-900/20 border-orange-900/50' : 'bg-orange-50 border-orange-100') :
                   (isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-100')}">
                  
                  <div class="flex justify-between items-start mb-1 pr-5">
                    <span class="flex items-center gap-1 text-[10px] font-black uppercase 
                      {notif.type === 'critical' ? 'text-red-500' : 
                       notif.type === 'success' ? 'text-emerald-500' : 
                       notif.type === 'warning' ? 'text-orange-500' : 'text-slate-500'}">
                      {#if notif.pinned} <span title="Закреплено на 10 мин" class="animate-pulse">📌</span> {/if}
                      {notif.title}
                    </span>
                    <span class="text-[9px] font-bold opacity-50 {isDark ? 'text-slate-400' : 'text-slate-500'}">
                      {notif.time.toLocaleTimeString('ru-RU')}
                    </span>
                  </div>
                  
                  <!-- НОВОЕ: Перенос строк и улучшенный интерлиньяж для маршрута -->
                  <p class="text-xs font-medium leading-relaxed whitespace-pre-line {isDark ? 'text-slate-300' : 'text-slate-600'}">{notif.body}</p>
                  
                  <!-- Крестик закрытия -->
                  <button on:click|stopPropagation={() => removeNotification(notif.id)} class="absolute top-2.5 right-2 p-1 rounded-full opacity-40 hover:opacity-100 transition-opacity {isDark ? 'hover:bg-slate-700 text-slate-300' : 'hover:bg-slate-200 text-slate-600'}">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>
                  </button>
                </div>
              {/each}
            {/if}
          </div>
        </div>
      {/if}

      <button on:click={toggleTheme} class="w-8 h-8 rounded-full flex items-center justify-center transition-colors {isDark ? 'bg-slate-800 text-yellow-400 hover:bg-slate-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}">
        {#if isDark} ☀️ {:else} 🌙 {/if}
      </button>
      <div class="flex items-center gap-3 border-l pl-4 {isDark ? 'border-slate-700' : 'border-slate-200'}">
        <div class="flex items-center gap-2" title={wsConnected ? 'Connected' : 'Disconnected'}>
          <div class="relative flex h-2.5 w-2.5">
            {#if wsConnected}
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            {:else}
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
            {/if}
          </div>
          <span class="text-[10px] font-black tracking-wider {wsConnected ? 'text-emerald-500' : 'text-red-500'}">{wsConnected ? 'ONLINE' : 'OFFLINE'}</span>
        </div>
        
        <div class="flex items-center bg-slate-100 rounded-lg pr-1 {isDark ? 'bg-slate-800' : ''}">
          <div class="px-2 py-1.5 font-mono text-[10px] font-bold {isDark ? 'text-slate-400' : 'text-slate-500'}">ОПРОС: <span class="text-indigo-500">{timeToNextUpdate}</span></div>
          <button on:click={forceUpdate} title="Принудительный опрос" class="w-6 h-6 rounded-md flex items-center justify-center transition-all {isUpdating ? 'opacity-50 cursor-not-allowed' : 'hover:bg-indigo-500 hover:text-white'} {isDark ? 'text-slate-400' : 'text-slate-500'}">
            <svg class="w-3 h-3 {isUpdating ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          </button>
        </div>

      </div>
    </div>
  </header>

  <main class="p-6 flex-1 overflow-hidden flex flex-col min-h-0" on:click={() => showNotifications = false}>
    
    <!-- ВКЛАДКА: ОБЗОР -->
    {#if activeTab === 'dash'}
      <div class="flex flex-col gap-6 h-full min-h-0" in:fade>
        
        <!-- ТОП ПАНЕЛЬ С КАРТОЧКАМИ (4 КОЛОНКИ) -->
        <div class="grid grid-cols-4 gap-6 h-40 shrink-0">
          
          <!-- Клиенты -->
          <div class="relative p-6 rounded-3xl overflow-hidden shadow-sm flex flex-col justify-between group {isDark ? 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700' : 'bg-white border border-slate-200'}">
            <div class="absolute top-0 right-0 p-4 opacity-10 transform translate-x-4 -translate-y-4 group-hover:scale-110 transition-transform duration-500">
               <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            </div>
            <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest relative z-10">Клиенты (GPON)</span>
            <div class="relative z-10">
              <div class="text-5xl font-black {isDark ? 'text-white' : 'text-slate-900'}">{totalStats.onus}</div>
              <div class="mt-3 flex items-center gap-3">
                <div class="flex-1 h-1.5 rounded-full overflow-hidden bg-slate-200/20 {isDark ? 'bg-slate-700' : 'bg-slate-100'}">
                  <div class="bg-emerald-500 h-full shadow-[0_0_10px_rgba(16,185,129,0.8)]" style="width: {(totalStats.online/totalStats.onus)*100}%"></div>
                </div>
                <div class="flex flex-col leading-none text-right gap-1 shrink-0">
                  <span class="text-[11px] font-black text-red-500">{totalStats.los} LOS</span>
                  <span class="text-[11px] font-black text-fuchsia-500">{totalStats.losi} LOSi</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Коммутаторы -->
          <div class="relative p-6 rounded-3xl overflow-hidden shadow-sm flex flex-col justify-between group {isDark ? 'bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700' : 'bg-white border border-slate-200'}">
            <div class="absolute top-0 right-0 p-4 opacity-10 transform translate-x-4 -translate-y-4 group-hover:scale-110 transition-transform duration-500">
               <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 24 24"><path d="M4 10h3v7H4zM10.5 10h3v7h-3zM2 19h20v3H2zM17 10h3v7h-3zM12 1v8h-1V1zM8 1v8H7V1zM16 1v8h-1V1z"/></svg>
            </div>
            <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest relative z-10">Оборудование (SW)</span>
            <div class="relative z-10">
              <div class="flex items-baseline gap-2">
                <div class="text-5xl font-black {isDark ? 'text-white' : 'text-slate-900'}">{totalStats.swUp}</div>
                <div class="text-lg font-bold text-slate-500">/ {totalStats.switches}</div>
              </div>
              <div class="mt-3 text-xs font-bold {totalStats.switches - totalStats.swUp > 0 ? 'text-red-500' : 'text-emerald-500'}">
                {totalStats.switches - totalStats.swUp} Узлов недоступно
              </div>
            </div>
          </div>

          <!-- Аварии сети -->
          <div class="p-6 rounded-3xl border shadow-sm flex flex-col justify-center {isDark ? 'bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700' : 'bg-white border-slate-200'}">
            <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Статус локаций</span>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-xs font-bold {isDark ? 'text-slate-300' : 'text-slate-600'}">Массовые GPON:</span>
                <span class="text-xs font-black px-2 py-0.5 rounded-md {totalStats.massOlt > 0 ? 'bg-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.5)] animate-pulse' : (isDark ? 'bg-slate-800 text-emerald-500 border border-slate-700' : 'bg-emerald-50 text-emerald-600 border border-emerald-100')}">
                  {totalStats.massOlt} ОЧАГОВ
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-xs font-bold {isDark ? 'text-slate-300' : 'text-slate-600'}">Массовые SW:</span>
                <span class="text-xs font-black px-2 py-0.5 rounded-md {totalStats.massSw > 0 ? 'bg-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.5)] animate-pulse' : (isDark ? 'bg-slate-800 text-emerald-500 border border-slate-700' : 'bg-emerald-50 text-emerald-600 border border-emerald-100')}">
                  {totalStats.massSw} ЛОКАЦИЙ
                </span>
              </div>
            </div>
          </div>

          <!-- Отчет за сутки -->
          <div class="p-6 rounded-3xl border shadow-sm flex flex-col justify-center relative overflow-hidden {isDark ? 'bg-gradient-to-br from-indigo-900/40 to-slate-900 border-indigo-500/30' : 'bg-gradient-to-br from-indigo-50 to-white border-indigo-200'}">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-indigo-500/20 rounded-full blur-2xl"></div>
            <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-3">Суточный Отчет (24ч)</span>
            
            <div class="flex justify-between items-end mb-2 border-b pb-2 {isDark ? 'border-slate-700' : 'border-indigo-100'}">
              <span class="text-xs font-bold {isDark ? 'text-slate-300' : 'text-slate-600'}">Всего за 24 часа:</span>
              <span class="text-lg font-black text-indigo-500">{dailyStats.total_24h}</span>
            </div>
            <div class="flex justify-between items-end">
              <span class="text-xs font-bold {isDark ? 'text-slate-300' : 'text-slate-600'}">Активно сейчас:</span>
              <span class="text-sm font-black px-2 py-0.5 rounded-md {(totalStats.switches - totalStats.swUp) > 0 ? 'bg-red-500 text-white shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse' : (isDark ? 'bg-slate-800 text-emerald-500' : 'bg-emerald-50 text-emerald-600')}">
                {totalStats.switches - totalStats.swUp}
              </span>
            </div>
          </div>

        </div>

        <!-- ГРАФИК (Используем use:chartSetup) -->
        <div class="flex-1 p-6 min-h-0 rounded-3xl border shadow-sm flex flex-col relative {isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'}">
          <div class="absolute top-6 right-6 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
            <span class="text-[10px] font-black text-slate-400 uppercase">Динамика потерь (LOS+LOSi)</span>
          </div>
          <div class="flex-1 w-full h-full mt-4">
            <canvas use:chartSetup></canvas>
          </div>
        </div>
      </div>

    <!-- ВКЛАДКА: GPON (OLT) -->
    {:else if activeTab === 'olt'}
      <div class="flex gap-6 h-full overflow-hidden min-h-0" in:fade>
        
        <!-- Левое меню (ОЛТы) с надежным скроллом -->
        <div class="w-64 h-full flex flex-col gap-2 overflow-y-auto pr-2 pb-4 always-visible-scroll min-h-0">
          <h3 class="text-[10px] shrink-0 font-black text-slate-400 uppercase mb-2 px-2 tracking-widest">Список OLT</h3>
          
          {#if filteredOlts.length === 0}
            <div class="text-xs font-bold text-slate-400 text-center mt-10">Все OLT работают в норме</div>
          {/if}

          {#each filteredOlts as olt, i}
            {@const allOnus = olt.ports.flatMap(p => p.onus)}
            {@const onlineCount = allOnus.filter(o => (o.state||'').toLowerCase() === 'working').length}
            {@const losCount = allOnus.filter(o => ['los', 'down'].includes((o.state||'').toLowerCase())).length}
            {@const losiCount = allOnus.filter(o => (o.state||'').toLowerCase() === 'losi').length}
            {@const hasMass = olt.ports.some(p => p.is_mass_outage)}
            
            <button on:click={() => {activeOltIndex = i; currentPage = 1;}}
              class="p-4 shrink-0 rounded-2xl border text-left transition-all relative {activeOltIndex === i ? 'ring-2 ring-indigo-500 shadow-md ' + (isDark ? 'bg-slate-800 border-indigo-500' : 'bg-white border-indigo-300') : (isDark ? 'bg-slate-800/50 border-slate-800 hover:bg-slate-800' : 'bg-slate-50 border-slate-200 hover:bg-white')}">
              {#if hasMass}
                <div class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-ping"></div>
                <div class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full shadow-md"></div>
              {/if}
              <!-- Верхняя строка: IP и количество LOS (справа) -->
              <div class="flex justify-between items-start">
                <div class="font-bold text-sm {isDark ? 'text-slate-200' : 'text-slate-900'}">{olt.ip}</div>
                <div class="flex flex-col gap-1 items-end">
                  {#if losCount > 0}
                    <span class="text-[9px] font-black text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded whitespace-nowrap">{losCount} LOS</span>
                  {/if}
                  {#if losiCount > 0}
                    <span class="text-[9px] font-black text-fuchsia-500 bg-fuchsia-500/10 px-1.5 py-0.5 rounded whitespace-nowrap">{losiCount} LOSi</span>
                  {/if}
                </div>
              </div>
              
              <!-- Нижняя строка: Прогресс-бар и общий счетчик -->
              <div class="flex justify-between mt-2.5 items-center">
                <div class="flex-1 h-1 bg-slate-200 rounded-full overflow-hidden {isDark ? 'bg-slate-700' : ''}">
                  <div class="bg-indigo-500 h-full" style="width: {(onlineCount/allOnus.length)*100}%"></div>
                </div>
                <span class="text-[9px] font-black opacity-60 whitespace-nowrap ml-3">
                  {onlineCount}/{allOnus.length}
                </span>
              </div>
            </button>
          {/each}
        </div>

        <!-- Центральная часть -->
        <div class="flex-1 flex flex-col gap-4 h-full min-w-0 min-h-0">
          <div class="flex gap-3 shrink-0">
            <input type="text" bind:value={searchQuery} on:input={handleSearch} placeholder="Поиск по интерфейсу или договору..." 
              class="flex-1 rounded-2xl px-6 py-3 shadow-sm outline-none transition-all font-bold {isDark ? 'bg-slate-900 text-slate-200 placeholder-slate-600 border border-slate-700 focus:border-indigo-500' : 'bg-white border border-slate-200 focus:border-indigo-400 text-slate-900'}" />
            <button on:click={() => {globalLosFilter = !globalLosFilter; globalLosiFilter = false; currentPage = 1;}} 
              class="px-6 rounded-2xl font-black text-[11px] tracking-wider transition-all {globalLosFilter ? 'bg-red-500 text-white shadow-[0_4px_14px_rgba(239,68,68,0.4)]' : (isDark ? 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-500 border border-slate-200 hover:bg-slate-50')}">
              ТОЛЬКО LOS
            </button>
            <button on:click={() => {globalLosiFilter = !globalLosiFilter; globalLosFilter = false; currentPage = 1;}} 
              class="px-6 rounded-2xl font-black text-[11px] tracking-wider transition-all {globalLosiFilter ? 'bg-fuchsia-500 text-white shadow-[0_4px_14px_rgba(217,70,239,0.4)]' : (isDark ? 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-500 border border-slate-200 hover:bg-slate-50')}">
              ТОЛЬКО LOSi
            </button>
          </div>

          <!-- Список портов с надежным скроллом -->
          <div class="flex-1 overflow-y-auto space-y-3 pr-2 pb-4 always-visible-scroll min-h-0">
            {#each paginatedPorts as port}
              {@const pOnus = port.onus}
              {@const strictLosCount = pOnus.filter(o => ['los', 'down'].includes((o.state||'').toLowerCase())).length}
              {@const losiCount = pOnus.filter(o => (o.state||'').toLowerCase() === 'losi').length}
              
              <div class="rounded-2xl shrink-0 shadow-sm border overflow-hidden transition-colors {port.is_mass_outage ? (isDark ? 'border-red-900 bg-red-900/10' : 'border-red-300 bg-red-50') : (isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200')}">
                <div class="flex items-center justify-between pr-4 cursor-pointer hover:opacity-80 transition-opacity" on:click={() => { activePort = activePort === port.name ? null : port.name; subFilter = globalLosFilter ? 'los' : (globalLosiFilter ? 'losi' : 'all'); }}>
                  <div class="flex-1 flex items-center gap-6 p-4">
                    <span class="font-black w-16 text-lg {isDark ? 'text-slate-200' : 'text-slate-800'}">{port.name}</span>
                    {#if port.is_mass_outage}
                      <span class="px-3 py-1 text-[10px] font-black rounded-lg bg-red-500 text-white shadow-md animate-pulse uppercase tracking-widest">Авария порта</span>
                    {:else}
                      <div class="w-64 h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-900' : 'bg-slate-100'}">
                        <div class="bg-emerald-500 h-full" style="width: {((pOnus.length - (strictLosCount + losiCount))/pOnus.length)*100}%"></div>
                      </div>
                    {/if}
                    <div class="text-xs font-bold flex gap-2">
                      {#if strictLosCount > 0}<span class="text-red-500 drop-shadow-sm">{strictLosCount} LOS</span>{/if}
                      {#if losiCount > 0}<span class="text-fuchsia-500 drop-shadow-sm">{losiCount} LOSi</span>{/if}
                      {#if strictLosCount === 0 && losiCount === 0}<span class={isDark ? 'text-slate-500' : 'text-slate-400'}>0 проблем</span>{/if}
                      <span class="text-slate-400"> / {pOnus.length}</span>
                    </div>
                  </div>
                  <button on:click|stopPropagation={() => exportPortCsv(port)} class="text-[10px] px-3 py-1.5 rounded-md font-bold transition-colors {isDark ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}">CSV</button>
                </div>

                {#if activePort === port.name}
                  <div class="p-5 border-t {isDark ? 'bg-slate-900/50 border-slate-700' : 'bg-slate-50 border-slate-100'}" transition:slide>
                    
                    <div class="flex flex-wrap gap-2 mb-4 border-b pb-4 {isDark ? 'border-slate-700' : 'border-slate-200'}">
                      {#each [
                        {id: 'all', label: 'Все', count: pOnus.length},
                        {id: 'online', label: 'В сети', count: pOnus.filter(o => (o.state||'').toLowerCase() === 'working').length},
                        {id: 'los', label: 'LOS', count: strictLosCount},
                        {id: 'losi', label: 'LOSi', count: losiCount},
                        {id: 'dying', label: 'DyingGasp', count: pOnus.filter(o => (o.state||'').toLowerCase() === 'dyinggasp').length},
                        {id: 'offline', label: 'Offline', count: pOnus.filter(o => (o.state||'').toLowerCase() === 'offline').length}
                      ] as filter}
                        <button on:click={() => subFilter = filter.id}
                          class="text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg transition-all 
                          {subFilter === filter.id 
                            ? 'bg-indigo-500 text-white shadow-md' 
                            : (isDark ? 'text-slate-400 bg-slate-800 hover:bg-slate-700' : 'text-slate-500 bg-slate-200 hover:bg-slate-300')}">
                          {filter.label} <span class="opacity-75 ml-1">({filter.count})</span>
                        </button>
                      {/each}
                    </div>
                    
                    <div class="grid grid-cols-5 gap-3">
                      {#each pOnus.filter(o => {
                        const s = (o.state || '').toLowerCase();
                        if (subFilter === 'online') return s === 'working';
                        if (subFilter === 'los') return ['los', 'down'].includes(s);
                        if (subFilter === 'losi') return s === 'losi';
                        if (subFilter === 'dying') return s === 'dyinggasp';
                        if (subFilter === 'offline') return s === 'offline';
                        return true;
                      }) as onu}
                      
                        <div class="p-3 rounded-xl border shadow-sm flex flex-col relative {isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'}">
                          
                          <div class="flex justify-between items-start">
                            <span class="text-[10px] font-black {isDark ? 'text-slate-500' : 'text-slate-400'}">{onu.id.split(':').pop()}</span>
                            <div class="w-2.5 h-2.5 rounded-full {getDotColor(onu.state)}"></div>
                          </div>
                          
                          <div class="text-[11px] font-bold mt-2 truncate {isDark ? 'text-slate-200' : 'text-slate-800'}">{onu.contract || '—'}</div>
                          
                          <div class="flex justify-between items-end mt-2 pt-2 border-t {isDark ? 'border-slate-700' : 'border-slate-100'}">
                            <div class="text-[9px] font-black uppercase tracking-wider {getStatusColor(onu.state)}">{onu.state}</div>
                            {#if !['working', 'host is alive'].includes((onu.state || '').toLowerCase()) && onu.los_time}
                              <div class="text-[9px] font-bold text-red-500">⏱ {formatLosTime(onu.los_time)}</div>
                            {/if}
                          </div>
                          
                        </div>
                        
                      {/each}
                    </div>
                    
                  </div>
                {/if}
              </div>
            {/each}
          </div>
          <!-- ПАГИНАЦИЯ -->
          {#if totalPages > 1}
            <div class="shrink-0 flex items-center justify-center gap-2 pt-2">
              <button
                on:click={() => currentPage = Math.max(1, currentPage - 1)}
                disabled={currentPage === 1}
                class="px-4 py-2 rounded-xl font-black text-[11px] tracking-wider transition-all disabled:opacity-30
                  {isDark ? 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}">
                ← НАЗАД
              </button>

              <div class="flex gap-1">
                {#each Array(totalPages) as _, i}
                  {#if totalPages <= 7 || i === 0 || i === totalPages - 1 || Math.abs(i + 1 - currentPage) <= 1}
                    <button
                      on:click={() => currentPage = i + 1}
                      class="w-9 h-9 rounded-xl font-black text-[11px] transition-all
                        {currentPage === i + 1
                          ? 'bg-indigo-500 text-white shadow-md'
                          : (isDark ? 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-500 border border-slate-200 hover:bg-slate-50')}">
                      {i + 1}
                    </button>
                  {:else if Math.abs(i + 1 - currentPage) === 2}
                    <span class="w-9 h-9 flex items-center justify-center text-slate-400 font-bold">…</span>
                  {/if}
                {/each}
              </div>

              <button
                on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
                disabled={currentPage === totalPages}
                class="px-4 py-2 rounded-xl font-black text-[11px] tracking-wider transition-all disabled:opacity-30
                  {isDark ? 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}">
                ВПЕРЁД →
              </button>

              <span class="text-[10px] font-bold ml-2 {isDark ? 'text-slate-500' : 'text-slate-400'}">
                {currentPage} / {totalPages} · {filteredPorts.length} портов
              </span>
            </div>
          {/if}
        </div>
      </div>
      
    <!-- ВКЛАДКА: КОММУТАТОРЫ -->
    {:else if activeTab === 'sw'}
      <div class="flex gap-6 h-full overflow-hidden min-h-0" in:fade>
        {#if !switchSearchQuery}
          <!-- Левое меню коммутаторов с надежным скроллом -->
          <div class="w-64 h-full flex flex-col gap-2 overflow-y-auto pr-2 pb-4 always-visible-scroll min-h-0" transition:slide={{ axis: 'x' }}>
            <h3 class="text-[10px] shrink-0 font-black text-slate-400 uppercase mb-2 px-2 tracking-widest">Локации</h3>
            
            {#if filteredSwitchFolders.length === 0}
              <div class="text-xs font-bold text-slate-400 text-center mt-10">Все коммутаторы в сети</div>
            {/if}

            {#each filteredSwitchFolders as folder, i}
              {@const downs = folder.onus.filter(s => !['working', 'host is alive'].includes((s.state||'').toLowerCase())).length}
              <button on:click={() => activeFolderIndex = i} class="p-4 shrink-0 rounded-2xl border text-left transition-all relative {activeFolderIndex === i ? (isDark ? 'bg-slate-800 border-indigo-500 ring-1 ring-indigo-500 shadow-md' : 'bg-white border-indigo-400 ring-1 ring-indigo-400 shadow-md') : (isDark ? 'bg-slate-800/50 border-slate-800' : 'bg-slate-50 border-slate-200')}">
                {#if folder.is_mass_outage} <div class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-ping"></div><div class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full shadow-md"></div> {/if}
                <div class="font-bold text-sm truncate {isDark ? 'text-slate-200' : 'text-slate-800'}">{folder.name}</div>
                <div class="flex justify-between mt-2 items-center">
                  <span class="text-[10px] font-bold text-slate-500">{folder.onus.length} УЗЛОВ</span>
                  {#if folder.is_mass_outage} <span class="text-[9px] font-black px-2 py-0.5 rounded bg-red-500 text-white">АВАРИЯ</span>
                  {:else if downs > 0} <span class="text-[9px] font-black px-2 py-0.5 rounded {isDark ? 'bg-slate-900 text-red-500' : 'bg-red-50 text-red-600'}">{downs} DOWN</span>
                  {:else} <span class="text-[9px] font-black px-2 py-0.5 rounded {isDark ? 'bg-slate-900 text-emerald-500' : 'bg-emerald-50 text-emerald-600'}">ОК</span> {/if}
                </div>
              </button>
            {/each}
          </div>
        {/if}

        <div class="flex-1 flex flex-col gap-4 h-full min-w-0 min-h-0">
          
          <div class="flex gap-3 shrink-0">
            <input type="text" bind:value={switchSearchQuery} placeholder="Поиск по IP или адресу..." 
              class="flex-1 rounded-2xl px-6 py-3 shadow-sm outline-none transition-all font-bold {isDark ? 'bg-slate-900 text-slate-200 placeholder-slate-600 border border-slate-700 focus:border-indigo-500' : 'bg-white border border-slate-200 focus:border-indigo-400 text-slate-900'}" />
            <button on:click={() => globalSwLosFilter = !globalSwLosFilter} 
              class="px-6 rounded-2xl font-black text-[11px] tracking-wider transition-all {globalSwLosFilter ? 'bg-red-500 text-white shadow-[0_4px_14px_rgba(239,68,68,0.4)]' : (isDark ? 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-500 border border-slate-200 hover:bg-slate-50')}">
              ТОЛЬКО LOS
            </button>
          </div>
          
          <!-- Сетка с коммутаторами с надежным скроллом -->
          <div class="flex-1 grid grid-cols-4 gap-4 overflow-y-auto pr-2 pb-4 content-start always-visible-scroll min-h-0">
            {#each displayedSwitches as sw}
              <div class="p-5 rounded-3xl border shadow-sm flex flex-col justify-between cursor-pointer transition-all group {['working', 'host is alive'].includes((sw.state||'').toLowerCase()) ? (isDark ? 'bg-slate-800 border-slate-700 hover:border-indigo-500' : 'bg-white border-slate-200 hover:border-indigo-300') : (isDark ? 'border-red-900 bg-red-900/10 hover:border-red-500' : 'border-red-300 bg-red-50 hover:border-red-400')}"
                   on:click={() => openHistory(sw.contract, sw.id, 'sw')}>
                <div>
                  <div class="flex justify-between items-start mb-2">
                    <div class="font-mono font-black text-sm {isDark ? 'text-slate-200' : 'text-slate-800'}">{sw.id}</div>
                    <div class="w-3 h-3 mt-1 rounded-full {getDotColor(sw.state)}"></div>
                  </div>
                  <div class="text-xs font-bold leading-tight {isDark ? 'text-slate-400' : 'text-slate-500'}">{sw.contract || '—'}</div>
                </div>
                <div class="mt-4 pt-3 border-t flex justify-between items-end {isDark ? 'border-slate-700' : 'border-slate-100'}">
                  <div class="text-[10px] font-black uppercase tracking-wider {getStatusColor(sw.state)}">{sw.state}</div>
                  {#if !['working', 'host is alive'].includes((sw.state||'').toLowerCase()) && sw.los_time}
                    <div class="text-[10px] font-black text-red-500">⏱ {formatLosTime(sw.los_time)}</div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(body) { 
    margin: 0; 
    height: 100vh; 
    overflow: hidden; 
  }

  :global(.always-visible-scroll) {
    overflow-y: auto !important;
    overflow-x: hidden !important; 
    scrollbar-width: thin !important; 
    scrollbar-color: rgba(148, 163, 184, 0.6) transparent !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar) {
    width: 10px !important;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-track) {
    background-color: transparent !important; 
    border-radius: 8px;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-thumb) {
    background-color: rgba(148, 163, 184, 0.5) !important;
    border-radius: 8px;
    border: 2px solid transparent; 
    background-clip: padding-box;
  }
  
  :global(.always-visible-scroll::-webkit-scrollbar-thumb:hover),
  :global(.always-visible-scroll::-webkit-scrollbar-thumb:active) {
    background-color: rgba(99, 102, 241, 0.9) !important; 
    border: 1px solid transparent; 
  }
</style>