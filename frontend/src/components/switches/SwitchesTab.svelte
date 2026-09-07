<!-- frontend/src/components/switches/SwitchesTab.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { fade } from 'svelte/transition';
  import SwitchToolbar from './SwitchToolbar.svelte';
  import SwitchSidebar from './SwitchSidebar.svelte';
  import SwitchCard from './SwitchCard.svelte';

  export let isDark = false;
  export let switchFolders = [];
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();

  let searchQuery = '';
  let onlyDownFilter = false;
  let selectedGroupName = null;

  // Разворачиваем все коммутаторы
  $: flatSwitches = (switchFolders || []).flatMap(folder => 
    (folder.onus || []).map(sw => ({
      ...sw,
      folderName: folder.name || 'Общая'
    }))
  );

  // Обогащаем группы со статусами
  $: enrichedFolders = (switchFolders || []).map(f => {
    const list = f.onus || [];
    const downSwitchesList = list.filter(s => !['working', 'host is alive'].includes((s.state || '').trim().toLowerCase()));
    const down = downSwitchesList.length;
    const total = list.length;
    const health = total > 0 ? ((total - down) / total) * 100 : 100;
    return {
      name: f.name || 'Общая',
      switches: list.map(sw => ({ ...sw, folderName: f.name })),
      downSwitchesList: downSwitchesList.map(sw => ({ ...sw, folderName: f.name })),
      down,
      total,
      health
    };
  }).sort((a, b) => {
    if (b.down !== a.down) return b.down - a.down; // Аварийные ВСЕГДА первыми
    return a.name.localeCompare(b.name);
  });

  // Фильтр групп
  $: visibleFolders = enrichedFolders.filter(f => {
    if (onlyDownFilter && f.down === 0) return false;
    return true;
  });

  // Авто-переключение на проблемную группу при включении фильтра аварий
  $: {
    if (onlyDownFilter && selectedGroupName) {
      const current = enrichedFolders.find(f => f.name === selectedGroupName);
      if (!current || current.down === 0) {
        const firstTroubled = enrichedFolders.find(f => f.down > 0);
        selectedGroupName = firstTroubled ? firstTroubled.name : null;
      }
    }
  }

  // Результаты поиска
  $: searchResults = searchQuery.trim() 
    ? flatSwitches.filter(sw => {
        const q = searchQuery.trim().toLowerCase();
        const isDownMatch = !onlyDownFilter || !['working', 'host is alive'].includes((sw.state || '').trim().toLowerCase());
        const desc = (sw.contract || '').toLowerCase();
        const ip = (sw.id || '').toLowerCase();
        return isDownMatch && (ip.includes(q) || desc.includes(q));
      })
    : [];

  // Коммутаторы внутри открытой группы
  $: groupSwitches = selectedGroupName 
    ? (enrichedFolders.find(f => f.name === selectedGroupName)?.switches || []).filter(sw => {
        if (onlyDownFilter && ['working', 'host is alive'].includes((sw.state || '').trim().toLowerCase())) return false;
        return true;
      })
    : [];

  $: totalCount = flatSwitches.length;
  $: downCount = flatSwitches.filter(s => !['working', 'host is alive'].includes((s.state || '').trim().toLowerCase())).length;
</script>

<div class="flex-1 flex flex-col gap-3.5 h-full overflow-hidden min-h-0 font-sans" in:fade={{ duration: 150 }}>
  
  <!-- 1. ТУЛБАР УПРАВЛЕНИЯ -->
  <SwitchToolbar 
    {isDark} 
    {totalCount}
    {downCount}
    {selectedGroupName}
    bind:searchQuery 
    bind:onlyDownFilter 
    on:backToGrid={() => selectedGroupName = null}
  />

  <!-- 2. ОСНОВНОЙ КОНТЕНТ -->
  {#if searchQuery.trim()}
    
    <!-- РЕЖИМ 1: РЕЗУЛЬТАТЫ ГЛОБАЛЬНОГО ПОИСКА -->
    <div class="flex-1 rounded-2xl border flex flex-col min-h-0 overflow-hidden transition-colors shadow-md
      {isDark ? 'bg-[#1e2a3e] border-slate-700/70' : 'bg-white border-slate-200/90'}">
      
      <div class="px-5 py-3 border-b flex items-center justify-between shrink-0 select-none
        {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'}">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold {isDark ? 'text-white' : 'text-slate-900'} font-mono">
            🔍 Результаты поиска: "{searchQuery.trim()}"
          </span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold">
            Найдено: {searchResults.length}
          </span>
        </div>
      </div>

      <div class="flex-1 p-3.5 overflow-y-auto min-h-0 always-visible-scroll">
        {#if searchResults.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center p-6 font-mono text-xs text-slate-400">
            <span class="text-xl mb-1">🔍</span>
            <span class="font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Коммутаторов по запросу "{searchQuery.trim()}" не найдено</span>
            <span class="text-[10px] text-slate-400 mt-0.5">Попробуйте ввести IP (например 172.31.6.35), адрес или модель</span>
          </div>
        {:else}
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3.5 content-start">
            {#each searchResults as sw (sw.id)}
              <SwitchCard 
                {sw} 
                {isDark} 
                {currentUnixTime} 
                isSearchMode={true}
                on:openHistory={(e) => dispatch('openHistory', e.detail)}
              />
            {/each}
          </div>
        {/if}
      </div>
    </div>

  {:else if selectedGroupName}
    
    <!-- РЕЖИМ 2: ВНУТРИ ГРУППЫ -->
    <div class="flex-1 flex gap-4 min-h-0 overflow-hidden">
      
      <!-- САЙДБАР СЛЕВА -->
      <SwitchSidebar 
        {isDark}
        mode="group"
        folders={visibleFolders}
        {selectedGroupName}
        {currentUnixTime}
        on:selectFolder={(e) => selectedGroupName = e.detail}
      />

      <!-- СЕТКА СВИТЧЕЙ ВЫБРАННОЙ ГРУППЫ -->
      <div class="flex-1 rounded-2xl border flex flex-col min-h-0 overflow-hidden transition-colors shadow-md
        {isDark ? 'bg-[#1e2a3e] border-slate-700/70' : 'bg-white border-slate-200/90'}">
        
        <div class="px-5 py-3 border-b flex items-center justify-between shrink-0 select-none
          {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'}">
          <div class="flex items-center gap-2.5">
            <h3 class="text-sm font-black tracking-tight {isDark ? 'text-white' : 'text-slate-900'} font-mono">
              {selectedGroupName}
            </h3>
            <span class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-md border
              {groupSwitches.some(s => !['working', 'host is alive'].includes((s.state || '').trim().toLowerCase()))
                ? (isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300')
                : (isDark ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-emerald-100 text-emerald-800 border border-emerald-300')}">
              {groupSwitches.length} узлов
            </span>
          </div>

          <button 
            on:click={() => selectedGroupName = null}
            class="text-xs font-mono font-bold text-indigo-400 hover:text-indigo-300 cursor-pointer flex items-center gap-1 transition-colors"
          >
            <span>✕ Закрыть группу (ESC)</span>
          </button>
        </div>

        <div class="flex-1 p-3.5 overflow-y-auto min-h-0 always-visible-scroll">
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-3.5 content-start">
            {#each groupSwitches as sw (sw.id)}
              <SwitchCard 
                {sw} 
                {isDark} 
                {currentUnixTime} 
                isSearchMode={false}
                on:openHistory={(e) => dispatch('openHistory', e.detail)}
              />
            {/each}
          </div>
        </div>
      </div>

    </div>

  {:else}

    <!-- РЕЖИМ 3: ГЛАВНЫЙ ЭКРАН КЛАСТЕРОВ -->
    <div class="flex-1 flex gap-4 min-h-0 overflow-hidden">
      
      <!-- САЙДБАР АВАРИЙ СЛЕВА -->
      <SwitchSidebar 
        {isDark}
        mode="main"
        folders={visibleFolders}
        {currentUnixTime}
        on:selectFolder={(e) => selectedGroupName = e.detail}
      />

      <!-- СЕТКА КЛАСТЕРОВ СПРАВА -->
      <div class="flex-1 rounded-2xl border p-3.5 overflow-y-auto transition-colors min-h-0 always-visible-scroll shadow-md
        {isDark ? 'bg-[#1e2a3e] border-slate-700/70' : 'bg-white border-slate-200/90'}">
        
        {#if visibleFolders.length === 0}
          <div class="h-full flex flex-col items-center justify-center text-center p-6 font-mono text-xs text-slate-400">
            <div class="w-10 h-10 rounded-2xl flex items-center justify-center mb-2 {isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-100 text-emerald-700'}">✓</div>
            <span class="font-bold {isDark ? 'text-slate-200' : 'text-slate-800'}">Все группы работают штатно</span>
            <span class="text-[10px] text-slate-400 mt-0.5">Аварийных сегментов не обнаружено</span>
          </div>
        {:else}
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5 content-start">
            {#each visibleFolders as f}
              {@const isTroubled = f.down > 0}
              {@const onlineWidth = f.total > 0 ? ((f.total - f.down) / f.total) * 100 : 100}
              {@const downWidth = f.total > 0 ? (f.down / f.total) * 100 : 0}

              <button 
                on:click={() => selectedGroupName = f.name}
                class="p-4 rounded-2xl border text-left transition-all duration-150 flex flex-col justify-between gap-3 cursor-pointer group relative overflow-hidden select-none transform hover:-translate-y-1 hover:shadow-lg
                {isDark 
                  ? 'bg-[#223046]/80 hover:bg-[#283952] border-slate-700/60 hover:border-indigo-500/50' 
                  : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-indigo-300 shadow-2xs'}"
              >
                <!-- ВЕРХ КАРТОЧКИ КЛАСТЕРА -->
                <div class="flex items-center justify-between gap-2">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="w-2 h-2 rounded-full shrink-0 {isTroubled ? 'bg-rose-500 animate-ping' : 'bg-emerald-500'}"></span>
                    <h3 class="text-sm font-bold tracking-tight truncate {isDark ? 'text-white' : 'text-slate-900'} group-hover:text-indigo-600 transition-colors">
                      {f.name}
                    </h3>
                  </div>

                  {#if isTroubled}
                    <span class="px-2 py-0.5 rounded-lg text-[10px] font-mono font-extrabold border shrink-0
                      {isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                      {f.down} DOWN
                    </span>
                  {:else}
                    <span class="text-[10px] font-mono font-bold text-emerald-600 shrink-0">
                      ✓ 100%
                    </span>
                  {/if}
                </div>

                <!-- ДВУХСЕГМЕНТНАЯ ШКАЛА: ОНЛАЙН (ГРАДИЕНТ) + АВАРИИ (КРАСНЫЙ ПУЛЬС) БЕЗ ПУСТОТЫ -->
                <div class="w-full h-[3px] rounded-full overflow-hidden flex {isDark ? 'bg-slate-700/60' : 'bg-slate-200'}">
                  {#if f.total > 0}
                    <!-- 1. Онлайн сегмент -->
                    {#if onlineWidth > 0}
                      <div 
                        class="h-full bg-gradient-to-r from-indigo-500 via-teal-400 to-emerald-400 transition-all duration-500" 
                        style="width: {onlineWidth}%"
                        title="Онлайн: {f.total - f.down}">
                      </div>
                    {/if}

                    <!-- 2. Красный сегмент аварии -->
                    {#if isTroubled}
                      <div 
                        class="h-full bg-rose-500 animate-pulse transition-all duration-500" 
                        style="width: {downWidth}%"
                        title="Аварии: {f.down}">
                      </div>
                    {/if}
                  {:else}
                    <div class="h-full w-full bg-slate-300 dark:bg-slate-700"></div>
                  {/if}
                </div>

                <!-- НИЗ: СТАТУС ОНЛАЙНА -->
                <div class="flex justify-between items-center text-xs font-mono {isDark ? 'text-slate-400 border-slate-700/50' : 'text-slate-600 border-slate-100'} pt-1 border-t">
                  <span class="{isTroubled ? 'text-rose-600 font-bold' : ''}">
                    {f.total - f.down}/{f.total} онлайн
                  </span>
                  <span class="text-[11px] font-bold text-indigo-400 group-hover:translate-x-1 transition-transform">
                    Открыть →
                  </span>
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>

    </div>

  {/if}

</div>