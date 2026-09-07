<!-- frontend/src/components/audit/NightAuditTab.svelte -->
<script>
  import { fade } from 'svelte/transition';
  import { BACKEND_URL } from '../../stores/networkStore.js';
  
  import NightAuditCalendar from './NightAuditCalendar.svelte';
  import NightAuditEventsList from './NightAuditEventsList.svelte';

  export let isDark = false;

  const today = new Date();
  let currentYear = today.getFullYear();
  let currentMonth = today.getMonth() + 1; // 1..12
  let selectedDay = today.getDate();
  let shiftFilter = 'night'; // 'night' | 'all'

  const monthNames = [
    '', 'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
    'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'
  ];

  let calendarDays = [];
  let switchIncidents = [];
  let gponHierarchy = [];
  let isLoading = false;
  let lastFetchKey = '';

  // Определение OLT станции (172.31.2.11 - 172.31.2.19)
  function isOltDevice(ip, contractStr = '') {
    if (!ip) return false;
    if ((contractStr || '').toLowerCase().includes('olt')) return true;
    const parts = ip.trim().split('.');
    if (parts.length === 4 && parts[0] === '172' && parts[1] === '31' && parts[2] === '2') {
      const last = parseInt(parts[3], 10);
      if (last >= 11 && last <= 19) return true;
    }
    return false;
  }

  async function fetchAuditData(year, month, day, shift) {
    const fetchKey = `${year}-${month}-${day}-${shift}`;
    if (fetchKey === lastFetchKey) return;
    lastFetchKey = fetchKey;
    
    isLoading = true;

    try {
      const token = localStorage.getItem('noc_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const res = await fetch(`${BACKEND_URL}/api/audit/month?year=${year}&month=${month}&day=${day}&shift=${shift}`, { headers });
      if (res.ok) {
        const json = await res.json();
        calendarDays = json.calendar_days || [];
        switchIncidents = json.switches || [];
        gponHierarchy = json.gpon || [];
      } else {
        console.error("Ошибка API аудита:", res.status);
      }
    } catch (e) {
      console.error("Ошибка загрузки ночного аудита:", e);
    } finally {
      isLoading = false;
    }
  }

  $: fetchAuditData(currentYear, currentMonth, selectedDay, shiftFilter);

  $: daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
  $: startDayOfWeek = (() => {
    let day = new Date(currentYear, currentMonth - 1, 1).getDay();
    return day === 0 ? 6 : day - 1;
  })();

  function handleMonthChange(delta) {
    let newMonth = currentMonth + delta;
    let newYear = currentYear;

    if (newMonth < 1) {
      newMonth = 12;
      newYear -= 1;
    } else if (newMonth > 12) {
      newMonth = 1;
      newYear += 1;
    }

    currentMonth = newMonth;
    currentYear = newYear;

    const maxDays = new Date(currentYear, currentMonth, 0).getDate();
    selectedDay = Math.min(selectedDay, maxDays);
  }

  function handleQuickToday() {
    currentYear = today.getFullYear();
    currentMonth = today.getMonth() + 1;
    selectedDay = today.getDate();
  }

  // РАЗДЕЛЕНИЕ: ОТСЕИВАЕМ OLT ИЗ СПИСКА СВИТЧЕЙ
  let cleanSwitchIncidents = [];
  let oltIncidents = [];

  $: {
    let olts = [];
    let cleanFolders = [];

    (switchIncidents || []).forEach(folder => {
      const folderName = folder.folder_name || folder.folderName || 'Общая';
      const items = folder.items || [];
      
      const folderSwitches = [];
      items.forEach(item => {
        if (isOltDevice(item.id, item.contract)) {
          olts.push({ ...item, folderName });
        } else {
          folderSwitches.push(item);
        }
      });

      if (folderSwitches.length > 0) {
        cleanFolders.push({ ...folder, items: folderSwitches });
      }
    });

    oltIncidents = olts;
    cleanSwitchIncidents = cleanFolders;
  }

  // ТОЧНЫЙ РАСЧЁТ МЕТРИК
  $: totalSwitchCount = cleanSwitchIncidents.reduce((s, f) => s + (f.items ? f.items.length : 0), 0);
  $: totalOltCount = oltIncidents.length;
  $: totalGponCount = gponHierarchy.reduce((acc, o) => acc + (o.ports || []).reduce((sum, p) => sum + (p.onus ? p.onus.length : 0), 0), 0);
  $: totalIncidents = totalSwitchCount + totalOltCount + totalGponCount;
  $: flappingCount = cleanSwitchIncidents.reduce((s, f) => s + (f.items ? f.items.filter(i => i.is_cluster || i.isCluster).length : 0), 0);
</script>

<div class="flex-1 flex flex-col gap-3.5 overflow-hidden min-h-0 font-sans" in:fade={{ duration: 150 }}>
  
  <!-- ВЕРХНИЙ ИНЖЕНЕРНЫЙ ТУЛБАР АУДИТА -->
  <div class="p-3 rounded-2xl border transition-all duration-300 flex flex-col lg:flex-row items-center justify-between gap-3 shrink-0 select-none shadow-sm
    {isDark ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200' : 'bg-white border-slate-200/90 text-slate-800'}"
  >
    <!-- ЛЕВАЯ ЧАСТЬ: ДАТА И БЫСТРЫЙ ПЕРЕХОД -->
    <div class="flex items-center gap-3 min-w-0 w-full lg:w-auto">
      <div class="flex items-center gap-2.5 font-mono">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center border font-bold text-sm
          {isDark ? 'bg-[#182335] border-slate-700/80 text-indigo-400' : 'bg-slate-100 border-slate-200 text-indigo-700'}">
          📋
        </div>
        <div class="flex flex-col">
          <div class="flex items-center gap-2">
            <span class="text-sm font-black {isDark ? 'text-white' : 'text-slate-900'} tracking-tight">
              {selectedDay} {monthNames[currentMonth]} {currentYear}
            </span>
            {#if selectedDay === today.getDate() && currentMonth === (today.getMonth() + 1) && currentYear === today.getFullYear()}
              <span class="px-2 py-0.2 rounded-md font-mono text-[9px] font-extrabold border uppercase
                {isDark ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40' : 'bg-indigo-50 text-indigo-700 border-indigo-200'}">
                СЕГОДНЯ
              </span>
            {/if}
          </div>
          <span class="text-[9.5px] font-mono text-slate-400">
            Журнал архивных деградаций и отчётов смен
          </span>
        </div>
      </div>

      <button 
        on:click={handleQuickToday}
        class="hidden sm:flex text-[10px] font-mono font-bold px-2.5 py-1 rounded-lg border transition-all cursor-pointer shadow-2xs active:scale-95 ml-1
        {isDark ? 'bg-[#24334a] hover:bg-[#2d3f59] border-slate-600/70 text-slate-300 hover:text-white' : 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700'}"
      >
        К сегодняшнему дню
      </button>
    </div>

    <!-- ЦЕНТР: СВОДНЫЕ СЧЁТЧИКИ -->
    <div class="flex items-center gap-2 font-mono text-[11px] font-bold">
      <!-- Всего -->
      <div class="px-3 py-1.5 rounded-xl border flex items-center gap-2
        {isDark ? 'bg-[#182335] border-slate-700/80' : 'bg-slate-50 border-slate-200'}">
        <span class="text-[9.5px] text-slate-400 uppercase">Всего:</span>
        <span class="font-black {totalIncidents > 0 ? (isDark ? 'text-rose-400' : 'text-rose-600') : (isDark ? 'text-emerald-400' : 'text-emerald-600')}">
          {totalIncidents}
        </span>
      </div>

      <!-- Коммутаторы L2 -->
      <div class="px-3 py-1.5 rounded-xl border flex items-center gap-2
        {isDark ? 'bg-[#182335] border-slate-700/80' : 'bg-slate-50 border-slate-200'}">
        <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-indigo-400' : 'bg-indigo-600'}"></span>
        <span class="text-[9.5px] text-slate-400 uppercase">SW L2:</span>
        <span class="font-black {isDark ? 'text-indigo-300' : 'text-indigo-700'}">{totalSwitchCount}</span>
      </div>

      <!-- OLT Станции -->
      <div class="px-3 py-1.5 rounded-xl border flex items-center gap-2
        {totalOltCount > 0 
          ? (isDark ? 'bg-rose-500/20 border-rose-500/40 text-rose-300 shadow-xs' : 'bg-rose-100 border-rose-300 text-rose-800') 
          : (isDark ? 'bg-[#182335] border-slate-700/80 text-slate-400' : 'bg-slate-50 border-slate-200 text-slate-600')}">
        <span class="w-1.5 h-1.5 rounded-full {totalOltCount > 0 ? 'bg-rose-500 animate-pulse' : (isDark ? 'bg-slate-500' : 'bg-slate-400')}"></span>
        <span class="text-[9.5px] uppercase">OLT:</span>
        <span class="font-black {totalOltCount > 0 ? (isDark ? 'text-rose-300' : 'text-rose-600') : ''}">{totalOltCount}</span>
      </div>

      <!-- GPON Оптика (СТРОГО КРАСНЫЙ ПРИ АВАРИЯХ LOS) -->
      <div class="px-3 py-1.5 rounded-xl border flex items-center gap-2
        {totalGponCount > 0 
          ? (isDark ? 'bg-rose-500/15 border-rose-500/30 text-rose-300' : 'bg-rose-50 border-rose-200 text-rose-700') 
          : (isDark ? 'bg-[#182335] border-slate-700/80 text-slate-400' : 'bg-slate-50 border-slate-200 text-slate-600')}">
        <span class="w-1.5 h-1.5 rounded-full {totalGponCount > 0 ? 'bg-rose-500 animate-pulse' : (isDark ? 'bg-emerald-400' : 'bg-emerald-600')}"></span>
        <span class="text-[9.5px] uppercase font-bold">GPON:</span>
        <span class="font-black {totalGponCount > 0 ? (isDark ? 'text-rose-400' : 'text-rose-600') : ''}">{totalGponCount}</span>
      </div>

      <!-- Дребезг -->
      {#if flappingCount > 0}
        <div class="px-3 py-1.5 rounded-xl border flex items-center gap-1.5
          {isDark ? 'bg-amber-500/15 border-amber-500/30 text-amber-300' : 'bg-amber-50 border-amber-200 text-amber-800'}">
          <span class="text-[10px]">⚠️</span>
          <span class="text-[9.5px] uppercase">Дребезг:</span>
          <span class="font-black">{flappingCount}</span>
        </div>
      {/if}
    </div>

    <!-- ПРАВАЯ ЧАСТЬ: СЕЛЕКТОР СМЕНЫ -->
    <div class="flex items-center p-1 rounded-xl border font-mono text-[10px] font-bold select-none
      {isDark ? 'bg-[#182335] border-slate-700/80' : 'bg-slate-100 border-slate-200'}">
      
      <button 
        on:click={() => shiftFilter = 'night'}
        class="px-3 py-1.5 rounded-lg transition-all duration-150 cursor-pointer flex items-center gap-1.5
        {shiftFilter === 'night' 
          ? (isDark ? 'bg-[#2d3f59] text-white shadow-xs font-black' : 'bg-white text-slate-900 shadow-xs font-black border border-slate-200') 
          : (isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900')}"
      >
        <span>🌙 Ночь (17:00–09:00)</span>
      </button>

      <button 
        on:click={() => shiftFilter = 'all'}
        class="px-3 py-1.5 rounded-lg transition-all duration-150 cursor-pointer flex items-center gap-1.5
        {shiftFilter === 'all' 
          ? (isDark ? 'bg-[#2d3f59] text-white shadow-xs font-black' : 'bg-white text-slate-900 shadow-xs font-black border border-slate-200') 
          : (isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900')}"
      >
        <span>☀️ Сутки (24ч)</span>
      </button>
    </div>
  </div>

  <!-- ОСНОВНАЯ РАБОЧАЯ ОБЛАСТЬ -->
  <div class="flex-1 flex gap-4 overflow-hidden min-h-0">
    <NightAuditCalendar
      {isDark}
      {currentYear}
      currentMonth={currentMonth - 1}
      {selectedDay}
      {calendarDays}
      {startDayOfWeek}
      on:selectDay={(e) => selectedDay = e.detail}
      on:changeMonth={(e) => handleMonthChange(e.detail)}
    />

    <NightAuditEventsList
      {isDark}
      {selectedDay}
      monthName={monthNames[currentMonth]}
      {shiftFilter}
      switchIncidents={cleanSwitchIncidents}
      {oltIncidents}
      {gponHierarchy}
      {isLoading}
      on:openHistory
    />
  </div>

</div>