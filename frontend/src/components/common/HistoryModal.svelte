<!-- frontend/src/components/common/HistoryModal.svelte -->
<script>
  import { fade, scale, slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let selectedEntity = null;
  export let entityHistory = [];
  export let isHistoryLoading = false;

  const dispatch = createEventDispatcher();
  let expandedEventKey = null;
  let timeFilter = 'all';

  function close() { dispatch('close'); }

  function toggleExpand(key) {
    expandedEventKey = expandedEventKey === key ? null : key;
  }

  // Универсальный и надежный парсер заголовка модального окна
  $: parsedHeader = (() => {
    if (!selectedEntity?.contract) return { title: '—', subtitle: '', details: [] };
    const contract = selectedEntity.contract.trim();
    const type = selectedEntity.type || 'sw';
    const id = selectedEntity.id || '';

    if (type === 'olt' || contract.startsWith('OLT Станция')) {
      return {
        title: contract,
        subtitle: `IP-адрес станции: ${id}`,
        typeTag: 'OLT СТАНЦИЯ'
      };
    }

    if (type === 'sw') {
      const parts = contract.split('|');
      const address = parts[0] ? parts[0].trim() : contract;
      const model = parts[1] ? parts[1].trim() : '';
      return {
        title: address,
        subtitle: model ? `Модель: ${model}` : '',
        typeTag: 'КОММУТАТОР',
        ip: id
      };
    }

    // ONU
    const parts = contract.split('|');
    const address = parts[0] ? parts[0].trim() : contract;
    const onuDetails = parts[1] ? parts[1].trim() : '';
    return {
      title: address,
      subtitle: onuDetails,
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
    entityHistory.forEach(event => {
      const cat = getTimeCategory(event.start_human);
      if (cat === 'morning') morning++;
      else if (cat === 'day') day++;
      else if (cat === 'evening') evening++;
      else if (cat === 'night') night++;
    });
    return { all: entityHistory.length, morning, day, evening, night };
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

  $: enrichedHistory = clusterOutages(entityHistory.filter(e => timeFilter === 'all' || getTimeCategory(e.start_human) === timeFilter));
</script>

<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-md font-sans" in:fade={{duration: 180}} out:fade={{duration: 150}}>
  
  <div class="w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] border backdrop-blur-2xl transition-colors
    {isDark ? 'bg-[#1e2a40] border-slate-700/70 text-slate-100' : 'bg-white border-slate-200 text-slate-900'}" 
    in:scale={{start: 0.95, duration: 180}}
  >
    <!-- Шапка модального окна -->
    <div class="px-7 py-5 border-b flex justify-between items-start gap-4 relative overflow-hidden
      {isDark ? 'bg-[#1e2a40] border-slate-700/60' : 'bg-slate-50 border-slate-100'}"
    >
      <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-rose-500"></div>

      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 mb-1">
          <span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
          <h2 class="text-[10px] font-mono font-bold tracking-widest uppercase text-indigo-400">Архив инцидентов узла</h2>
        </div>
        
        <div class="text-xl font-bold leading-snug truncate {isDark ? 'text-slate-100' : 'text-slate-800'}" title={parsedHeader.title}>
          {parsedHeader.title}
        </div>
        
        <div class="flex flex-wrap items-center gap-2 mt-2 font-mono text-[10px] font-bold select-none">
          <span class="px-2.5 py-0.5 rounded-md border shadow-2xs {isDark ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30' : 'bg-indigo-50 text-indigo-700 border-indigo-100'}">
            {parsedHeader.typeTag}
          </span>
          {#if parsedHeader.ip}
            <span class="px-2.5 py-0.5 rounded-md border {isDark ? 'bg-[#152033] text-slate-300 border-slate-700/60' : 'bg-slate-100 text-slate-700 border-slate-200'}">
              ID / IP: {parsedHeader.ip}
            </span>
          {/if}
          {#if parsedHeader.subtitle}
            <span class="px-2.5 py-0.5 rounded-md border {isDark ? 'bg-[#152033] text-slate-400 border-slate-700/40' : 'bg-slate-50 text-slate-500 border-slate-100'}">
              {parsedHeader.subtitle}
            </span>
          {/if}
        </div>
      </div>
      
      <button on:click={close} 
        class="w-8 h-8 shrink-0 flex items-center justify-center rounded-xl transition-all duration-200 border cursor-pointer
        {isDark ? 'bg-[#152033] border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-700' : 'bg-slate-100 border-slate-200 text-slate-600 hover:text-slate-900'}"
      >
        ✕
      </button>
    </div>

    <!-- Фильтры смен -->
    <div class="px-7 py-3 border-b flex items-center justify-between font-mono text-[10px] font-bold select-none
      {isDark ? 'bg-[#1a263c] border-slate-700/60' : 'bg-slate-50 border-slate-100'}"
    >
      <span class="text-slate-400 uppercase tracking-wider text-[9px]">Фильтр смены:</span>
      <div class="flex gap-1.5">
        {#each [
          { id: 'all', label: 'Все', count: counts.all },
          { id: 'morning', label: 'Утро', count: counts.morning },
          { id: 'day', label: 'День', count: counts.day },
          { id: 'evening', label: 'Вечер', count: counts.evening },
          { id: 'night', label: 'Ночь', count: counts.night }
        ] as cat}
          <button on:click={() => { timeFilter = cat.id; expandedEventKey = null; }}
            class="px-2.5 py-1 rounded-lg border transition-all duration-200 cursor-pointer
            {timeFilter === cat.id
              ? 'bg-indigo-500 text-white border-indigo-500 shadow-2xs'
              : (isDark ? 'bg-[#121b2d] text-slate-300 border-slate-700/60 hover:bg-slate-700/60 hover:text-slate-100' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50')}"
          >
            {cat.label} <span class="opacity-60">({cat.count})</span>
          </button>
        {/each}
      </div>
    </div>

    <!-- Список истории -->
    <div class="p-7 overflow-y-auto flex-1 always-visible-scroll {isDark ? 'bg-[#131b2e]/70' : 'bg-slate-50/50'}">
      {#if isHistoryLoading}
        <div class="flex flex-col items-center justify-center py-16">
          <div class="w-9 h-9 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3 shadow-2xs"></div>
          <span class="text-xs font-mono font-bold tracking-widest text-indigo-400 uppercase animate-pulse">Считывание SQLite истории...</span>
        </div>
      {:else if enrichedHistory.length === 0}
        <div class="text-center py-16 select-none">
          <div class="text-4xl mb-3">✨</div>
          <h3 class="text-sm font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Сбоев не зафиксировано</h3>
          <p class="text-xs mt-1 text-slate-400 font-mono">В базе данных нет записей о падениях за выбранный период.</p>
        </div>
      {:else}
        
        <div class="relative pl-7 border-l-2 border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-200'} ml-3 space-y-4">
          {#each enrichedHistory as event (event.key)}
            {@const hasEnded = !event.isGroup ? !!event.end_time : !event.hasActive}
            {@const isExpanded = expandedEventKey === event.key}
            
            <div class="relative">
              <div class="absolute -left-[37px] top-3.5 w-5 h-5 rounded-full flex items-center justify-center border transition-all duration-300
                {hasEnded 
                  ? (isDark ? 'bg-[#1e2a40] border-emerald-500 text-emerald-400' : 'bg-white border-emerald-500 text-emerald-600') 
                  : 'bg-rose-500 border-rose-300 text-white animate-pulse'}"
              >
                <div class="w-1.5 h-1.5 rounded-full {hasEnded ? 'bg-emerald-400' : 'bg-white'}"></div>
              </div>
              
              <div 
                on:click={() => event.isGroup && toggleExpand(event.key)}
                class="p-4 rounded-2xl border transition-all duration-200 flex flex-col gap-2.5 backdrop-blur-md
                {isDark ? 'bg-[#18253f] border-slate-700/60' : 'bg-white border-slate-200 shadow-2xs'}
                {hasEnded ? 'border-l-4 border-l-emerald-500' : 'border-l-4 border-l-rose-500'}
                {event.isGroup ? (isDark ? 'hover:border-indigo-500/50 hover:bg-slate-700/60 cursor-pointer' : 'hover:border-indigo-300 hover:bg-slate-50/60 cursor-pointer') : ''}"
              >
                <div class="flex items-center justify-between gap-4 select-none">
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-mono font-bold tracking-wider uppercase
                      {hasEnded ? 'text-emerald-400' : 'text-rose-500 animate-pulse'}"
                    >
                      {#if event.isGroup}
                        ⚠️ ФЛАППИНГ ({event.events.length} СБОЕВ ЗА ЧАС)
                      {:else}
                        {hasEnded ? 'ВОССТАНОВЛЕНО' : 'АКТИВНЫЙ СБОЙ'}
                      {/if}
                    </span>

                    {#if event.isGroup}
                      <span class="text-[10px] font-mono font-bold text-indigo-400 flex items-center gap-1 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        <span>{isExpanded ? 'Скрыть ▲' : 'Детали ▼'}</span>
                      </span>
                    {/if}
                  </div>
                  
                  <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-md border
                    {isDark ? 'bg-[#121b2d] text-indigo-300 border-slate-700' : 'bg-indigo-50 text-indigo-700 border-indigo-100'}"
                  >
                    ⏱ {formatDuration(event.duration)}
                  </span>
                </div>

                <div class="flex items-center gap-2 text-xs font-mono font-bold {isDark ? 'text-slate-100' : 'text-slate-800'}">
                  <span>{event.start_human}</span>
                  <span class="text-indigo-400">➔</span>
                  {#if hasEnded}
                    <span>{event.end_human}</span>
                  {:else}
                    <span class="text-rose-500 uppercase text-[10px] font-mono font-bold tracking-wider px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 animate-pulse">
                      АКТИВНО СЕЙЧАС
                    </span>
                  {/if}
                </div>

                {#if event.isGroup && isExpanded}
                  <div transition:slide={{duration: 150}} class="pt-3 mt-1 border-t border-dashed space-y-1.5 {isDark ? 'border-slate-700/60' : 'border-slate-200'}">
                    <span class="text-[10px] font-mono font-bold uppercase tracking-wider block mb-1 text-slate-300">
                      Хронология сбоев в этой группе:
                    </span>
                    {#each event.events as subEvent}
                      {@const subEnded = !!subEvent.end_time}
                      <div class="p-2.5 rounded-xl border font-mono text-xs flex items-center justify-between transition-colors
                        {isDark ? 'bg-[#121b2d] border-slate-700/50 text-slate-100' : 'bg-slate-50 border-slate-200/80 text-slate-800 hover:border-indigo-200'}"
                      >
                        <div class="flex items-center gap-2">
                          <span class="w-1.5 h-1.5 rounded-full shrink-0 {subEnded ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'}"></span>
                          <span>{subEvent.start_human}</span>
                          <span class="text-indigo-400">➔</span>
                          {#if subEnded}
                            <span>{subEvent.end_human}</span>
                          {:else}
                            <span class="text-rose-500 text-[10px] font-bold uppercase">АКТИВНО</span>
                          {/if}
                        </div>
                        <span class="text-[10px] font-bold text-slate-300 shrink-0">
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