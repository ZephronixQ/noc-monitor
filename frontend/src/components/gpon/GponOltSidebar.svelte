<!-- frontend/src/components/gpon/GponOltSidebar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let olts = [];
  export let activeOltIp = "";
  export let globalLosFilter = false;
  export let globalLosiFilter = false;

  const dispatch = createEventDispatcher();

  // Натуральная сортировка IP по возрастанию (2.11, 2.12, 2.13...)
  function sortIpAsc(a, b) {
    const numA = (a.ip || '').split('.').map(Number);
    const numB = (b.ip || '').split('.').map(Number);
    for (let i = 0; i < Math.max(numA.length, numB.length); i++) {
      const nA = numA[i] || 0;
      const nB = numB[i] || 0;
      if (nA !== nB) return nA - nB;
    }
    return 0;
  }

  $: filteredOlts = olts.filter(olt => {
    const ports = olt.ports || [];
    if (globalLosFilter) return ports.some(p => (p.onus || []).some(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())));
    if (globalLosiFilter) return ports.some(p => (p.onus || []).some(o => (o.state||'').trim().toLowerCase() === 'losi'));
    return true;
  }).sort(sortIpAsc);

  $: if (filteredOlts.length > 0 && !filteredOlts.some(o => o.ip === activeOltIp)) {
    activeOltIp = filteredOlts[0].ip;
  }
</script>

<div class="w-68 h-full flex flex-col rounded-2xl border transition-all duration-300 overflow-hidden shrink-0 select-none shadow-md font-sans
  {isDark ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200' : 'bg-white border-slate-200/90 text-slate-800'}"
>
  <!-- ШАПКА САЙДБАРА -->
  <div class="px-4 py-3 border-b flex items-center justify-between shrink-0
    {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'}">
    <div class="flex items-center gap-1.5">
      <span class="w-2 h-2 rounded-full {isDark ? 'bg-indigo-400' : 'bg-indigo-600'}"></span>
      <span class="text-xs font-bold uppercase tracking-wider font-mono {isDark ? 'text-slate-200' : 'text-slate-900'}">
        Станции OLT
      </span>
    </div>

    <span class="font-mono font-bold text-[9px] px-2 py-0.5 rounded-md border tracking-wider
      {isDark ? 'bg-[#293a52] text-indigo-300 border-slate-600/60' : 'bg-slate-100 text-indigo-800 border-slate-300'}">
      {filteredOlts.length} СТАНЦИЙ
    </span>
  </div>

  <!-- СПИСОК OLT СТАНЦИЙ СО СПЕКТРАЛЬНОЙ ШКАЛОЙ -->
  <div class="flex-1 p-2 overflow-y-auto space-y-2 min-h-0 always-visible-scroll">
    {#each filteredOlts as olt}
      {@const allOnus = (olt.ports || []).flatMap(p => p.onus || [])}
      {@const totalCount = allOnus.length}
      {@const onlineCount = allOnus.filter(o => ['working', 'host is alive'].includes((o.state||'').trim().toLowerCase())).length}
      {@const losCount = allOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length}
      {@const losiCount = allOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length}
      {@const dyingCount = allOnus.filter(o => (o.state||'').trim().toLowerCase() === 'dyinggasp').length}
      {@const offlineCount = Math.max(0, totalCount - onlineCount - losCount - losiCount - dyingCount)}
      
      {@const isOltActive = totalCount > 0}
      {@const healthPercent = isOltActive ? ((onlineCount / totalCount) * 100).toFixed(0) : 0}
      {@const isActive = activeOltIp === olt.ip}
      
      <div 
        on:click={() => dispatch('select', olt.ip)}
        class="w-full p-3 rounded-xl border text-left transition-all duration-150 flex flex-col gap-2 cursor-pointer relative overflow-hidden
        {isActive 
          ? (isDark 
              ? 'bg-[#2a3a52] border-indigo-500/70 shadow-sm' 
              : 'bg-indigo-50/90 border-indigo-300 text-indigo-950 shadow-2xs') 
          : (isDark 
              ? 'bg-[#223046]/70 border-slate-700/60 hover:bg-[#283852]' 
              : 'bg-white border-slate-200 hover:border-indigo-200 hover:bg-slate-50/80')}"
      >
        {#if isActive}
          <div class="absolute left-0 top-1.5 bottom-1.5 w-1 bg-indigo-500 rounded-r-full"></div>
        {/if}

        <!-- ВЕРХ: IP + ЧИПЫ АВАРИЙ (LOS И LOSI) -->
        <div class="flex justify-between items-center w-full gap-2 pl-1 font-mono">
          <div class="flex items-center gap-1.5 min-w-0">
            <span class="w-1.5 h-1.5 rounded-full shrink-0 
              {isOltActive ? (losCount > 0 ? 'bg-rose-500 animate-ping' : (losiCount > 0 ? 'bg-purple-400' : 'bg-emerald-500')) : 'bg-rose-500 animate-pulse'}">
            </span>
            <span class="font-bold text-xs tracking-tight {isDark ? 'text-indigo-300' : 'text-indigo-800'}">{olt.ip}</span>
          </div>

          <div class="flex items-center gap-1 text-[9px] font-bold shrink-0">
            {#if losCount > 0}
              <span class="px-1.5 py-0.2 rounded {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                {losCount} LOS
              </span>
            {/if}
            {#if losiCount > 0}
              <span class="px-1.5 py-0.2 rounded {isDark ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'bg-purple-100 text-purple-800 border border-purple-300'}">
                {losiCount} LOSi
              </span>
            {/if}
          </div>
        </div>

        <!-- МУЛЬТИСЕГМЕНТНЫЙ СПЕКТР OLT (ТОЧНО КАК НА ПЛАТАХ И ДАШБОРДЕ) -->
        {#if isOltActive}
          <div class="space-y-1.5 w-full font-mono text-[9.5px] pl-1">
            <div class="w-full h-[3px] rounded-full overflow-hidden flex {isDark ? 'bg-slate-700/60' : 'bg-slate-200'}">
              <!-- 1. ОНЛАЙН (ЗЕЛЕНЫЙ) -->
              {#if onlineCount > 0}
                <div 
                  class="h-full {isDark ? 'bg-emerald-400' : 'bg-emerald-500'} transition-all duration-300" 
                  style="width: {(onlineCount / totalCount) * 100}%"
                  title="Онлайн: {onlineCount}">
                </div>
              {/if}

              <!-- 2. DYING GASP (ЖЕЛТЫЙ) -->
              {#if dyingCount > 0}
                <div 
                  class="h-full bg-amber-400 transition-all duration-300" 
                  style="width: {(dyingCount / totalCount) * 100}%"
                  title="DyingGasp: {dyingCount}">
                </div>
              {/if}

              <!-- 3. LOSi (ФИОЛЕТОВЫЙ) -->
              {#if losiCount > 0}
                <div 
                  class="h-full bg-purple-500 transition-all duration-300" 
                  style="width: {(losiCount / totalCount) * 100}%"
                  title="LOSi: {losiCount}">
                </div>
              {/if}

              <!-- 4. LOS (КРАСНЫЙ С ПУЛЬСАЦИЕЙ) -->
              {#if losCount > 0}
                <div 
                  class="h-full bg-rose-500 animate-pulse transition-all duration-300" 
                  style="width: {(losCount / totalCount) * 100}%"
                  title="LOS: {losCount}">
                </div>
              {/if}

              <!-- 5. OFFLINE (СЕРЫЙ) -->
              {#if offlineCount > 0}
                <div 
                  class="h-full bg-slate-400/80 transition-all duration-300" 
                  style="width: {(offlineCount / totalCount) * 100}%"
                  title="Offline: {offlineCount}">
                </div>
              {/if}
            </div>

            <div class="flex justify-between items-center {isDark ? 'text-slate-400' : 'text-slate-600'}">
              <span>{onlineCount} / {totalCount} ONU</span>
              <span class="font-bold {healthPercent >= 90 ? 'text-emerald-500' : (losCount > 0 ? 'text-rose-500' : 'text-purple-400')}">
                {healthPercent}% OK
              </span>
            </div>
          </div>
        {/if}

        <!-- НИЗ: КНОПКА ЛОГОВ OLT -->
        <div class="flex justify-between items-center w-full pt-1.5 border-t font-mono text-[9px] {isDark ? 'border-slate-700/50' : 'border-slate-100'} pl-1">
          <button 
            on:click|stopPropagation={() => dispatch('openOltHistory', { contract: `OLT Станция ${olt.ip}`, id: olt.ip })}
            class="px-2 py-0.5 rounded-md border text-[9px] font-bold font-mono transition-all cursor-pointer flex items-center gap-1 active:scale-95
            {isDark 
              ? 'bg-[#182335] border-slate-600/70 text-indigo-300 hover:bg-slate-700 hover:text-white' 
              : 'bg-slate-50 border-slate-300 text-indigo-800 hover:bg-indigo-50'}"
            title="История логов OLT"
          >
            <span>Логи OLT</span>
            <span class="text-[8px]">➔</span>
          </button>

          {#if !isOltActive}
            <span class="px-2 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
              ОФФЛАЙН
            </span>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>