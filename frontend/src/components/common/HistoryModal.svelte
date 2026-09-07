<!-- frontend/src/components/common/HistoryModal.svelte -->
<script>
  import { fade, scale, slide } from 'svelte/transition';
  import { createEventDispatcher, onMount } from 'svelte';

  export let isDark = false;
  export let selectedEntity = null;
  export let entityHistory = [];
  export let isHistoryLoading = false;

  const dispatch = createEventDispatcher();
  let expandedEventKey = null;
  let timeFilter = 'all';

  function close() { 
    dispatch('close'); 
  }

  function toggleExpand(key) {
    expandedEventKey = expandedEventKey === key ? null : key;
  }

  // ЖЕСТКИЙ ПЕРЕХВАТ ESC: закрывает ТОЛЬКО историю и глушит событие для фона
  function handleKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      close();
    }
  }

  onMount(() => {
    // capture: true перехватывает нажатие ДО того, как оно долетит до тулбаров
    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  });

  // Надежный парсер метаданных
  $: parsedHeader = (() => {
    if (!selectedEntity) return { title: 'Узел сети', subtitle: '', typeTag: 'УЗЕЛ' };
    
    const contract = (selectedEntity.contract || selectedEntity.name || selectedEntity.title || '').trim();
    const type = (selectedEntity.type || '').toLowerCase();
    const id = selectedEntity.id || selectedEntity.ip || '';

    if (type === 'olt' || contract.startsWith('OLT') || (id.startsWith('172.31.') && (contract.includes('OLT') || !contract))) {
      return {
        title: contract || `OLT Станция ${id}`,
        subtitle: `Головная станция GPON · ${id}`,
        typeTag: 'OLT СТАНЦИЯ',
        ip: id
      };
    }

    if (type === 'sw' || selectedEntity.isSwitch || id.includes('172.31.')) {
      const parts = contract.split('|');
      const address = parts[0] ? parts[0].trim() : (contract || id);
      const model = parts[1] ? parts[1].trim() : '';
      return {
        title: address,
        subtitle: model ? `Модель: ${model}` : (selectedEntity.folderName ? `Кластер: ${selectedEntity.folderName}` : ''),
        typeTag: 'КОММУТАТОР L2/L3',
        ip: id
      };
    }

    // ONU
    const parts = contract.split('|');
    const address = parts[0] ? parts[0].trim() : (contract || `ONU #${id}`);
    const onuDetails = parts[1] ? parts[1].trim() : '';
    return {
      title: address,
      subtitle: onuDetails || (id ? `Интерфейс: ${id}` : ''),
      typeTag: 'GPON ONU',
      ip: id
    };
  })();

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

  $: counts = (() => {
    let morning = 0; let day = 0; let evening = 0; let night = 0;
    (entityHistory || []).forEach(event => {
      const cat = getTimeCategory(event.start_human);
      if (cat === 'morning') morning++;
      else if (cat === 'day') day++;
      else if (cat === 'evening') evening++;
      else if (cat === 'night') night++;
    });
    return { all: (entityHistory || []).length, morning, day, evening, night };
  })();

  function clusterOutages(rawHistory) {
    if (!rawHistory || rawHistory.length === 0) return [];
    const sorted = [...rawHistory].sort((a, b) => a.start_time - b.start_time);
    const clusters = [];
    let currentCluster = [];

    for (let i = 0; i < sorted.length; i++) {
      const event = sorted[i];
      if (currentCluster.length === 0) {
        currentCluster.push(event);
      } else {
        const lastInCluster = currentCluster[currentCluster.length - 1];
        if (event.start_time - lastInCluster.start_time <= 3600) {
          currentCluster.push(event);
        } else {
          clusters.push(currentCluster);
          currentCluster = [event];
        }
      }
    }
    if (currentCluster.length > 0) clusters.push(currentCluster);

    return clusters.map(cluster => {
      if (cluster.length === 1) {
        return { isGroup: false, ...cluster[0], key: cluster[0].start_time };
      } else {
        const latestEvent = cluster[cluster.length - 1];
        const earliestEvent = cluster[0];
        const totalDuration = cluster.reduce((sum, e) => sum + (e.duration || 0), 0);
        return {
          isGroup: true,
          key: earliestEvent.start_time,
          start_time: earliestEvent.start_time,
          start_human: earliestEvent.start_human,
          end_time: latestEvent.end_time,
          end_human: latestEvent.end_human,
          duration: totalDuration,
          hasActive: !latestEvent.end_time,
          events: [...cluster].reverse()
        };
      }
    }).reverse();
  }

  $: enrichedHistory = clusterOutages((entityHistory || []).filter(e => timeFilter === 'all' || getTimeCategory(e.start_human) === timeFilter));
</script>

<!-- BACKDROP ОВЕРЛЕЙ -->
<div 
  on:click|self={close}
  class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-md font-sans select-none" 
  in:fade={{duration: 120}} 
  out:fade={{duration: 100}}
>
  <!-- ОСНОВНОЙ КОНТЕЙНЕР ОКНА -->
  <div 
    on:click|stopPropagation
    class="w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col h-[82vh] max-h-[720px] border transition-all
    {isDark ? 'bg-[#1b2537] border-slate-700/70 text-slate-100 shadow-black/80' : 'bg-white border-slate-200 text-slate-900 shadow-2xl'}" 
    in:scale={{start: 0.96, duration: 150}}
  >
    <!-- 1. ФИКСИРОВАННАЯ ШАПКА -->
    <div class="px-6 py-4 border-b flex justify-between items-start gap-4 shrink-0 relative
      {isDark ? 'bg-[#223046] border-slate-700/70' : 'bg-slate-50/90 border-slate-200'}"
    >
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 mb-1 font-mono">
          <span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
          <h2 class="text-[10px] font-bold tracking-widest uppercase {isDark ? 'text-indigo-400' : 'text-indigo-600'}">
            Журнал инцидентов узла
          </h2>
        </div>
        
        <div class="text-base font-extrabold leading-snug truncate {isDark ? 'text-white' : 'text-slate-900'}" title={parsedHeader.title}>
          {parsedHeader.title}
        </div>
        
        <div class="flex flex-wrap items-center gap-2 mt-2 font-mono text-[10px] font-bold">
          <span class="px-2.5 py-0.5 rounded-lg border {isDark ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30' : 'bg-indigo-50 text-indigo-700 border-indigo-200'}">
            {parsedHeader.typeTag}
          </span>
          {#if parsedHeader.ip}
            <span class="px-2.5 py-0.5 rounded-lg border {isDark ? 'bg-[#182335] text-slate-300 border-slate-700' : 'bg-white text-slate-700 border-slate-300'}">
              IP: {parsedHeader.ip}
            </span>
          {/if}
          {#if parsedHeader.subtitle}
            <span class="px-2.5 py-0.5 rounded-lg border {isDark ? 'bg-[#182335] text-slate-400 border-slate-700/60' : 'bg-white text-slate-500 border-slate-200'}">
              {parsedHeader.subtitle}
            </span>
          {/if}
        </div>
      </div>
      
      <!-- КНОПКА ЗАКРЫТИЯ -->
      <button 
        on:click={close} 
        class="px-3 py-1.5 rounded-xl border font-mono text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shrink-0 active:scale-95
        {isDark ? 'bg-[#182335] hover:bg-slate-700 border-slate-700 text-slate-300 hover:text-white' : 'bg-white hover:bg-slate-100 border-slate-300 text-slate-700'}"
        title="Закрыть окно (ESC)"
      >
        <span>✕</span>
        <kbd class="opacity-60 text-[9px] font-normal">ESC</kbd>
      </button>
    </div>

    <!-- 2. ФИКСИРОВАННАЯ ПОЛОСА ФИЛЬТРОВ СМЕН -->
    <div class="px-6 py-2.5 border-b flex items-center justify-between font-mono text-[10px] font-bold shrink-0
      {isDark ? 'bg-[#182335] border-slate-700/60' : 'bg-slate-100/80 border-slate-200'}"
    >
      <span class="{isDark ? 'text-slate-400' : 'text-slate-600'} uppercase tracking-wider text-[9px]">Фильтр смены:</span>
      
      <div class="flex gap-1.5">
        {#each [
          { id: 'all', label: 'Все', count: counts.all },
          { id: 'morning', label: 'Утро', count: counts.morning },
          { id: 'day', label: 'День', count: counts.day },
          { id: 'evening', label: 'Вечер', count: counts.evening },
          { id: 'night', label: 'Ночь', count: counts.night }
        ] as cat}
          <button 
            on:click={() => { timeFilter = cat.id; expandedEventKey = null; }}
            class="px-2.5 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1
            {timeFilter === cat.id
              ? (isDark ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm' : 'bg-indigo-600 text-white border-indigo-600 shadow-xs')
              : (isDark ? 'bg-[#1e2a3e] text-slate-300 border-slate-700 hover:bg-slate-700 hover:text-white' : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50')}"
          >
            <span>{cat.label}</span>
            <span class="opacity-70 text-[9px]">({cat.count})</span>
          </button>
        {/each}
      </div>
    </div>

    <!-- 3. ТЕЛО ТАЙМЛАЙНА СО СКРОЛЛОМ -->
    <div class="p-6 overflow-y-auto flex-1 min-h-0 always-visible-scroll {isDark ? 'bg-[#151f30]/60' : 'bg-slate-50/50'}">
      
      {#if isHistoryLoading}
        <div class="flex flex-col items-center justify-center py-16 font-mono">
          <div class="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3"></div>
          <span class="text-xs font-bold tracking-wider text-indigo-400 uppercase animate-pulse">Загрузка архива SQLite...</span>
        </div>
      {:else if enrichedHistory.length === 0}
        <div class="flex flex-col items-center justify-center text-center py-16">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center mb-3 text-xl {isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-100 text-emerald-700'}">✓</div>
          <h3 class="text-sm font-bold {isDark ? 'text-white' : 'text-slate-900'}">Сбоев не зафиксировано</h3>
          <p class="text-xs mt-1 text-slate-400 font-mono">За выбранный период узел работал стабильно без аварий.</p>
        </div>
      {:else}
        
        <!-- ЛИНИЯ ТАЙМЛАЙНА -->
        <div class="relative pl-6 border-l-2 border-dashed {isDark ? 'border-slate-700/80' : 'border-slate-300'} ml-3 space-y-3.5">
          {#each enrichedHistory as event (event.key)}
            {@const hasEnded = !event.isGroup ? !!event.end_time : !event.hasActive}
            {@const isExpanded = expandedEventKey === event.key}
            
            <div class="relative">
              <!-- ТОЧКА -->
              <div class="absolute -left-[32px] top-3.5 w-4 h-4 rounded-full flex items-center justify-center border transition-all
                {hasEnded 
                  ? (isDark ? 'bg-[#1b2537] border-emerald-500 text-emerald-400' : 'bg-white border-emerald-500 text-emerald-600') 
                  : 'bg-rose-500 border-rose-300 text-white animate-pulse'}"
              >
                <div class="w-1.5 h-1.5 rounded-full {hasEnded ? 'bg-emerald-500' : 'bg-white'}"></div>
              </div>
              
              <!-- КАРТОЧКА СОБЫТИЯ -->
              <div 
                on:click={() => event.isGroup && toggleExpand(event.key)}
                class="p-3.5 rounded-2xl border transition-all flex flex-col gap-2
                {isDark ? 'bg-[#1e2a3e] border-slate-700/80' : 'bg-white border-slate-200 shadow-2xs'}
                {hasEnded ? 'border-l-4 border-l-emerald-500' : 'border-l-4 border-l-rose-500'}
                {event.isGroup ? (isDark ? 'hover:bg-[#24334a] cursor-pointer' : 'hover:bg-slate-50 cursor-pointer') : ''}"
              >
                <!-- ШАПКА СОБЫТИЯ -->
                <div class="flex items-center justify-between gap-3 font-mono text-[10px]">
                  <div class="flex items-center gap-2">
                    <span class="font-bold uppercase tracking-wider
                      {hasEnded ? 'text-emerald-500' : 'text-rose-500 animate-pulse'}"
                    >
                      {#if event.isGroup}
                        ⚠️ ФЛАППИНГ ({event.events.length} СКАЧКОВ ЗА ЧАС)
                      {:else}
                        {hasEnded ? 'ВОССТАНОВЛЕНО' : 'АКТИВНАЯ АВАРИЯ'}
                      {/if}
                    </span>

                    {#if event.isGroup}
                      <span class="text-[9.5px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        {isExpanded ? 'Скрыть ▲' : 'Хронология ▼'}
                      </span>
                    {/if}
                  </div>
                  
                  <span class="font-bold px-2 py-0.5 rounded-md border tabular-nums
                    {isDark ? 'bg-[#182335] text-slate-300 border-slate-700' : 'bg-slate-100 text-slate-800 border-slate-200'}">
                    ⏱ {formatDuration(event.duration)}
                  </span>
                </div>

                <!-- ВРЕМЕННЫЕ МЕТКИ -->
                <div class="flex items-center gap-2 text-xs font-mono font-bold {isDark ? 'text-slate-100' : 'text-slate-900'}">
                  <span>{event.start_human}</span>
                  <span class="text-indigo-400">➔</span>
                  {#if hasEnded}
                    <span>{event.end_human}</span>
                  {:else}
                    <span class="text-rose-500 uppercase text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 animate-pulse">
                      АКТИВНО СЕЙЧАС
                    </span>
                  {/if}
                </div>

                <!-- ВЛОЖЕННАЯ ХРОНОЛОГИЯ ФЛАППИНГА -->
                {#if event.isGroup && isExpanded}
                  <div transition:slide={{duration: 140}} class="pt-2.5 mt-1 border-t border-dashed space-y-1.5 {isDark ? 'border-slate-700/80' : 'border-slate-200'}">
                    <span class="text-[9.5px] font-mono font-bold uppercase tracking-wider block text-slate-400">
                      Хронология скачков:
                    </span>
                    {#each event.events as subEvent}
                      {@const subEnded = !!subEvent.end_time}
                      <div class="p-2 rounded-xl border font-mono text-xs flex items-center justify-between
                        {isDark ? 'bg-[#182335] border-slate-700 text-slate-200' : 'bg-slate-50 border-slate-200 text-slate-900'}">
                        
                        <div class="flex items-center gap-2">
                          <span class="w-1.5 h-1.5 rounded-full {subEnded ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'}"></span>
                          <span>{subEvent.start_human}</span>
                          <span class="text-indigo-400">➔</span>
                          {#if subEnded}
                            <span>{subEvent.end_human}</span>
                          {:else}
                            <span class="text-rose-500 text-[10px] font-bold uppercase">АКТИВНО</span>
                          {/if}
                        </div>
                        <span class="text-[10px] font-bold {isDark ? 'text-slate-400' : 'text-slate-600'}">
                          ⏱ {formatDuration(subEvent.duration)}
                        </span>
                      </div>
                    {/each}
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