<!-- frontend\src\components\HistoryModal.svelte -->
<script>
  import { fade, scale, slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let selectedEntity = null;
  export let entityHistory = [];
  export let isHistoryLoading = false;

  const dispatch = createEventDispatcher();

  let expandedEventKey = null;
  let timeFilter = 'all'; // 'all', 'morning', 'day', 'evening', 'night'

  function close() {
    dispatch('close');
  }

  // Очищенный парсинг без дубликатов вендора коммутатора в теге порта
  $: parsedHeader = (() => {
    if (!selectedEntity?.contract) return { street: '—', device: '', port: '' };
    const contract = selectedEntity.contract;
    
    const commaIndex = contract.indexOf(',');
    if (commaIndex === -1) return { street: contract, device: '', port: '' };
    
    const street = contract.substring(0, commaIndex).trim();
    const rest = contract.substring(commaIndex + 1).trim();
    
    const minusIndex = rest.indexOf('-');
    if (minusIndex === -1) return { street, device: rest, port: '' };
    
    const device = rest.substring(0, minusIndex).trim();
    let port = rest.substring(minusIndex + 1).trim();
    
    // Безопасно очищаем тег порта от дублирования вендора/таймаута после знака |
    if (port.includes('|')) {
      port = port.split('|')[0].trim();
    }
    
    return { street, device, port };
  })();

  $: deviceModel = selectedEntity?.contract ? selectedEntity.contract.split('|')[1]?.trim() : '';

  // Человекочитаемый конвертер длительности инцидента
  function formatDuration(totalSeconds) {
    if (!totalSeconds || totalSeconds <= 0) return '0 сек';
    const d = Math.floor(totalSeconds / 86400);
    const h = Math.floor((totalSeconds % 86400) / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;

    let parts = [];
    if (d > 0) parts.push(`${d} дн`);
    if (h > 0) parts.push(`${h} ч`);
    if (m > 0 || (d === 0 && h === 0)) parts.push(`${m} мин`);
    if (s > 0 && d === 0 && h === 0) parts.push(`${s} сек`);
    return parts.join(' ');
  }

  // Определение времени суток по строке "09.07.2026 12:22:36"
  function getTimeCategory(timeStr) {
    if (!timeStr) return 'day';
    const match = timeStr.match(/\s(\d{2}):/);
    if (!match) return 'day';
    const hour = parseInt(match[1], 10);
    
    if (hour >= 0 && hour < 6) return 'night';
    if (hour >= 6 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 18) return 'day';
    return 'evening';
  }

  // Калькулятор счетчиков категорий времени суток
  $: counts = (() => {
    let morning = 0; let day = 0; let evening = 0; let night = 0;
    entityHistory.forEach(event => {
      const cat = getTimeCategory(event.start_human);
      if (cat === 'morning') morning++;
      else if (cat === 'day') day++;
      else if (cat === 'evening') evening++;
      else if (cat === 'night') night++;
    });
    return { all: entityHistory.length, morning, day, evening, night };
  })();

  // Сортировка и группировка флуда/дребезга в единые родительские инциденты
  function clusterOutages(rawHistory) {
    if (!rawHistory || rawHistory.length === 0) return [];
    
    // Сортируем по возрастанию для сборки последовательных цепочек
    const sorted = [...rawHistory].sort((a, b) => a.start_time - b.start_time);
    const clusters = [];
    let currentCluster = [];

    for (let i = 0; i < sorted.length; i++) {
      const event = sorted[i];
      if (currentCluster.length === 0) {
        currentCluster.push(event);
      } else {
        const lastInCluster = currentCluster[currentCluster.length - 1];
        // Группируем, если промежуток между стартами последовательных падений меньше 1 часа (3600 сек)
        if (event.start_time - lastInCluster.start_time <= 3600) {
          currentCluster.push(event);
        } else {
          clusters.push(currentCluster);
          currentCluster = [event];
        }
      }
    }
    if (currentCluster.length > 0) {
      clusters.push(currentCluster);
    }

    // Собираем финальный массив для вывода в обратном порядке (сначала новые)
    return clusters.map(cluster => {
      if (cluster.length === 1) {
        return {
          isGroup: false,
          ...cluster[0],
          key: cluster[0].start_time,
          isFlapping: false
        };
      } else {
        const latestEvent = cluster[cluster.length - 1];
        const earliestEvent = cluster[0];
        const hasActive = !latestEvent.end_time;
        const totalDuration = cluster.reduce((sum, e) => sum + (e.duration || 0), 0);

        return {
          isGroup: true,
          key: earliestEvent.start_time,
          start_time: earliestEvent.start_time,
          start_human: earliestEvent.start_human,
          end_time: latestEvent.end_time,
          end_human: latestEvent.end_human,
          duration: totalDuration,
          hasActive: hasActive,
          isFlapping: true,
          events: [...cluster].reverse() // Внутри кластера новые падения сверху
        };
      }
    }).reverse();
  }

  // Фильтруем сырую историю и собираем в кластеры
  $: filteredRawHistory = entityHistory.filter(event => {
    if (timeFilter === 'all') return true;
    return getTimeCategory(event.start_human) === timeFilter;
  });

  $: enrichedHistory = clusterOutages(filteredRawHistory);

  function toggleExpand(eventKey) {
    expandedEventKey = expandedEventKey === eventKey ? null : eventKey;
  }
</script>

<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md" in:fade={{duration: 180}} out:fade={{duration: 180}}>
  
  <div class="w-full max-w-2xl rounded-3xl shadow-[0_24px_60px_rgba(0,0,0,0.6)] overflow-hidden flex flex-col max-h-[85vh] 
    {isDark ? 'bg-[#161f33] border border-slate-800' : 'bg-white border border-slate-200'}" 
    in:scale={{start: 0.96, duration: 180}}
  >
    
    <!-- Шапка -->
    <div class="px-6 py-5 border-b flex justify-between items-start gap-4 
      {isDark ? 'bg-[#121724]/70 border-slate-800/80' : 'bg-slate-50 border-slate-100'}"
    >
      <div class="min-w-0 flex-1">
        <h2 class="text-[10px] font-black tracking-widest uppercase text-indigo-400 mb-1">Архив инцидентов</h2>
        <div class="text-lg font-extrabold leading-snug {isDark ? 'text-slate-100' : 'text-slate-900'}">
          {parsedHeader.street}
        </div>
        
        <div class="flex flex-wrap items-center gap-2 mt-2.5 select-none font-mono text-[10px] font-bold">
          {#if parsedHeader.device}
            <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-slate-800 text-slate-300 border border-slate-700/60' : 'bg-slate-100 text-slate-600 border border-slate-200'}">
              ID: {parsedHeader.device}
            </span>
          {/if}
          {#if parsedHeader.port}
            <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-slate-800 text-slate-300 border border-slate-700/60' : 'bg-slate-100 text-slate-600 border border-slate-200'}">
              порт: {parsedHeader.port}
            </span>
          {/if}
          {#if deviceModel}
            <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-slate-800/60 text-slate-400 border border-slate-700/40' : 'bg-slate-50 text-slate-500 border border-slate-100'}">
              ⑂ {deviceModel}
            </span>
          {/if}
          <span class="px-2 py-0.5 rounded-md {isDark ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20' : 'bg-indigo-50 text-indigo-600 border border-indigo-100'}">
            IP: {selectedEntity?.id}
          </span>
        </div>
      </div>
      
      <button on:click={close} 
        class="w-8 h-8 shrink-0 flex items-center justify-center rounded-xl transition-all duration-200 border
        {isDark 
          ? 'bg-white/[0.03] border-slate-800 text-slate-400 hover:text-white hover:bg-white/[0.08]' 
          : 'bg-slate-100 border-slate-200 text-slate-600 hover:text-slate-800 hover:bg-slate-200'}"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Новые переключатели Категорий Времени Суток -->
    <div class="px-6 py-3 border-b flex flex-wrap gap-2 select-none items-center justify-between
      {isDark ? 'bg-[#121724]/40 border-slate-800/60' : 'bg-slate-50/50 border-slate-100'}"
    >
      <span class="text-[9px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-wider">Аналитика по времени:</span>
      <div class="flex flex-wrap gap-1.5 font-mono text-[9px] font-bold">
        {#each [
          { id: 'all', label: 'Все', count: counts.all, icon: '📊' },
          { id: 'morning', label: 'Утро', count: counts.morning, icon: '🌅' },
          { id: 'day', label: 'День', count: counts.day, icon: '☀️' },
          { id: 'evening', label: 'Вечер', count: counts.evening, icon: '🌆' },
          { id: 'night', label: 'Ночь', count: counts.night, icon: '🌙' }
        ] as cat}
          <button on:click={() => { timeFilter = cat.id; expandedEventKey = null; }}
            class="px-2 py-1 rounded-md border flex items-center gap-1 transition-all duration-150
            {timeFilter === cat.id
              ? 'bg-indigo-500 text-white border-indigo-500 shadow-[0_2px_8px_rgba(99,102,241,0.3)]'
              : (isDark 
                  ? 'bg-slate-800/40 text-slate-400 border-slate-700/60 hover:bg-slate-800/80 hover:text-slate-200' 
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50')}"
          >
            <span>{cat.icon}</span> {cat.label} <span class="opacity-60">({cat.count})</span>
          </button>
        {/each}
      </div>
    </div>

    <!-- Основное тело со списком -->
    <div class="p-8 overflow-y-auto flex-1 always-visible-scroll {isDark ? 'bg-[#121724]/20' : 'bg-slate-50/20'}">
      {#if isHistoryLoading}
        <div class="flex flex-col items-center justify-center py-16 opacity-75">
          <div class="w-9 h-9 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <span class="text-xs font-bold tracking-wider uppercase {isDark ? 'text-slate-400' : 'text-slate-500'}">Запрос истории...</span>
        </div>
      {:else if enrichedHistory.length === 0}
        <div class="text-center py-16">
          <div class="text-4xl mb-4 select-none">✨</div>
          <h3 class="text-sm font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Нет инцидентов</h3>
          <p class="text-xs mt-1.5 {isDark ? 'text-slate-400' : 'text-slate-500'}">Для выбранного фильтра времени суток падений не найдено.</p>
        </div>
      {:else}
        
        <div class="relative pl-8 border-l border-dashed {isDark ? 'border-slate-800' : 'border-slate-200'} ml-3 space-y-6">
          
          {#each enrichedHistory as event (event.key)}
            {@const hasEnded = !event.isGroup ? !!event.end_time : !event.hasActive}
            {@const isExpanded = expandedEventKey === event.key}
            
            <div class="relative">
              
              <!-- Круглый узел на таймлайне -->
              <div class="absolute -left-[41px] top-3.5 w-6 h-6 rounded-full flex items-center justify-center border shadow-sm transition-all duration-300
                {hasEnded 
                  ? (isDark ? 'bg-[#121724] border-emerald-500/40 text-emerald-400' : 'bg-white border-emerald-400 text-emerald-600') 
                  : 'bg-rose-500 border-rose-300 text-white animate-pulse shadow-[0_0_12px_rgba(239,68,68,0.5)]'}"
              >
                {#if hasEnded}
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                {:else}
                  <svg class="w-3 h-3 animate-bounce" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.03L3.07 19.5a1.5 1.5 0 001.3 2.25h15.26a1.5 1.5 0 001.3-2.25L13.3 3.22a1.5 1.5 0 00-2.6 0zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                {/if}
              </div>
              
              <!-- Кликабельное тело записи лога (клик разворачивает только групповые аварии) -->
              <div class="p-4.5 rounded-2xl border transition-all duration-200 flex flex-col justify-between gap-3
                {isDark ? 'bg-[#121724]/75 hover:bg-[#121724]/90' : 'bg-white hover:shadow-sm'}
                {event.isGroup ? 'cursor-pointer select-none' : ''}
                {hasEnded 
                  ? (isDark ? 'border-slate-800/80 border-l-4 border-l-emerald-500' : 'border-slate-200 border-l-4 border-l-emerald-500') 
                  : (isDark ? 'border-slate-800 border-l-4 border-l-rose-500 shadow-[inset_1px_0_10px_rgba(239,68,68,0.03)]' : 'border-slate-200 border-l-4 border-l-rose-500')}"
                on:click={() => { if (event.isGroup) toggleExpand(event.key); }}
              >
                
                <div class="flex items-center justify-between gap-4">
                  <span class="text-[9px] font-black tracking-widest uppercase select-none
                    {hasEnded ? 'text-emerald-500' : 'text-rose-500 animate-pulse'}"
                  >
                    {#if event.isGroup}
                      {event.hasActive ? 'АКТИВНЫЙ ФЛАППИНГ' : 'ФЛАППИНГ (ВОССТАНОВЛЕНО)'}
                    {:else}
                      {hasEnded ? 'Восстановлено' : 'АКТИВНАЯ АВАРИЯ'}
                    {/if}
                  </span>
                  
                  <div class="flex items-center gap-2 font-mono">
                    {#if event.isGroup}
                      <span class="text-[8px] font-extrabold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
                        ⚠️ ФЛАППИНГ: {event.events.length} АВАРИЙ ЗА ЧАС
                      </span>
                    {/if}
                    
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-md
                      {isDark ? 'bg-slate-800 text-slate-300 border border-slate-700/60' : 'bg-slate-100 text-slate-600 border border-slate-200'}"
                    >
                      {formatDuration(event.duration)}
                    </span>
                  </div>
                </div>

                <!-- Строка интервала -->
                <div class="flex flex-wrap items-center gap-1.5 text-xs font-semibold">
                  <span class="text-slate-400 dark:text-slate-500 select-none">Интервал:</span>
                  <span class="font-mono text-slate-700 dark:text-slate-200">{event.start_human}</span>
                  <span class="text-slate-400 select-none">➔</span>
                  {#if hasEnded}
                    <span class="font-mono text-slate-700 dark:text-slate-200">{event.end_human}</span>
                  {:else}
                    <span class="text-[10px] font-black uppercase tracking-wider text-rose-500 px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/25 animate-pulse">
                      активно сейчас
                    </span>
                  {/if}
                </div>

                <!-- Раскрывающийся список с историей дребезга только для групповых записей -->
                {#if event.isGroup && isExpanded}
                  <div transition:slide={{duration: 200}} class="mt-2.5 p-4 rounded-xl flex flex-col gap-2.5
                    {isDark ? 'bg-black/30 border border-slate-800/80' : 'bg-slate-100/50 border border-slate-200/50'}"
                    on:click|stopPropagation
                  >
                    <span class="text-[10px] font-extrabold tracking-widest text-amber-500 dark:text-amber-400 uppercase flex items-center gap-1.5 select-none">
                      <span>⚡</span> Лог падений внутри этого кластера (±1 час)
                    </span>
                    
                    <div class="space-y-1.5 mt-1">
                      {#each event.events as subEvent}
                        <div class="flex justify-between items-center text-[11px] p-2 rounded border border-white/[0.02] bg-white/[0.01] dark:bg-black/10">
                          <div class="flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full {subEvent.end_time ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'}"></span>
                            <span class="font-mono text-slate-400">
                              {subEvent.start_human.split(' ')[1]}
                            </span>
                            <span class="text-slate-400">➔</span>
                            <span class="font-mono text-slate-400">
                              {subEvent.end_time ? subEvent.end_human.split(' ')[1] : 'сейчас'}
                            </span>
                          </div>
                          
                          <span class="font-mono font-bold text-slate-500 dark:text-slate-300">
                            {formatDuration(subEvent.duration)}
                          </span>
                        </div>
                      {/each}
                    </div>
                  </div>
                {/if}

              </div>
            </div>
          {/each}
          
        </div>
      {/if}
    </div>
  </div>
</div>