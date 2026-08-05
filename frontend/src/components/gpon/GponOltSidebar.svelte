<!-- frontend/src/components/gpon/GponOltSidebar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';

  export let isDark = false;
  export let olts = [];
  export let activeOltIp = "";
  export let globalLosFilter = false;
  export let globalLosiFilter = false;

  const dispatch = createEventDispatcher();

  $: filteredOlts = olts.filter(olt => {
    const ports = olt.ports || [];
    if (globalLosFilter) return ports.some(p => (p.onus || []).some(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())));
    if (globalLosiFilter) return ports.some(p => (p.onus || []).some(o => (o.state||'').trim().toLowerCase() === 'losi'));
    return true;
  });

  $: if (filteredOlts.length > 0 && !filteredOlts.some(o => o.ip === activeOltIp)) {
    activeOltIp = filteredOlts[0].ip;
  }
</script>

<div class="w-64 h-full flex flex-col gap-2 overflow-y-auto pr-2 pb-4 cyber-scroll min-h-0 select-none font-sans">
  
  <div class="flex items-center justify-between px-3 py-1 shrink-0">
    <div class="flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
      <span class="text-[10px] font-black uppercase tracking-widest font-mono {isDark ? 'text-slate-300' : 'text-slate-700'}">
        Станции OLT
      </span>
    </div>

    <span class="font-mono font-black text-[9px] px-2.5 py-0.5 rounded-full border tracking-wider shadow-2xs
      {isDark ? 'bg-[#1e2a40] text-indigo-300 border-slate-700/70' : 'bg-indigo-50 text-indigo-700 border-indigo-200'}"
    >
      {filteredOlts.length} OLT
    </span>
  </div>

  <div class="flex flex-col gap-2.5">
    {#each filteredOlts as olt}
      {@const allOnus = (olt.ports || []).flatMap(p => p.onus || [])}
      {@const totalCount = allOnus.length}
      {@const onlineCount = allOnus.filter(o => (o.state||'').trim().toLowerCase() === 'working').length}
      {@const losCount = allOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length}
      {@const losiCount = allOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length}
      {@const isOltActive = totalCount > 0}
      {@const healthPercent = isOltActive ? ((onlineCount / totalCount) * 100).toFixed(0) : 0}
      {@const isActive = activeOltIp === olt.ip}
      
      <div 
        on:click={() => dispatch('select', olt.ip)}
        class="w-full p-3.5 rounded-2xl border text-left transition-all duration-200 flex flex-col gap-2.5 group cursor-pointer relative overflow-hidden shadow-2xs
        {isActive 
          ? (isDark 
              ? 'bg-gradient-to-r from-indigo-500/30 via-purple-500/20 to-transparent border-indigo-500/70 text-white font-black shadow-[0_4px_20px_rgba(99,102,241,0.25)]' 
              : 'bg-gradient-to-r from-indigo-50/90 via-purple-50/50 to-white border-indigo-400 text-indigo-950 font-black shadow-sm') 
          : (isDark 
              ? 'bg-[#1e2a40] border-slate-700/70 text-slate-200 hover:text-white hover:bg-slate-700/60' 
              : 'bg-white border-slate-200 text-slate-800 hover:border-indigo-300 hover:bg-slate-50/80')}"
      >
        {#if isActive}
          <div class="absolute left-0 top-1.5 bottom-1.5 w-1 bg-gradient-to-b from-indigo-500 via-purple-500 to-pink-500 rounded-r-full shadow-[0_0_10px_rgba(168,85,247,0.8)]"></div>
        {/if}

        <div class="flex justify-between items-center w-full gap-2">
          <div class="flex items-center gap-1.5 min-w-0">
            <span class="w-1.5 h-1.5 rounded-full shrink-0 {isOltActive ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' : 'bg-rose-500 animate-pulse'}"></span>
            <span class="font-mono font-black text-xs tracking-tight {isDark ? 'text-indigo-300' : 'text-indigo-600'}">{olt.ip}</span>
          </div>

          <div class="flex items-center gap-1 font-mono text-[8.5px] font-black shrink-0">
            {#if losCount > 0}
              <span class="px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-500 border border-rose-500/30">{losCount} LOS</span>
            {/if}
            {#if losiCount > 0}
              <span class="px-1.5 py-0.5 rounded bg-fuchsia-500/15 text-fuchsia-500 border border-fuchsia-500/30">{losiCount} LOSi</span>
            {/if}
          </div>
        </div>

        <!-- ИСПРАВЛЕННЫЙ ИДЕАЛЬНО ИДЕНТИЧНЫЙ ТРЕК ПРОГРЕСС-БАРА -->
        {#if isOltActive}
          <div class="flex items-center gap-2.5 w-full font-mono text-[9px] pt-0.5">
            <div class="flex-1 h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-700/80' : 'bg-slate-200/80'}">
              <div 
                class="bg-gradient-to-r from-indigo-500 via-teal-400 to-emerald-400 h-full rounded-full transition-all duration-300" 
                style="width: {(onlineCount/totalCount)*100}%"
              ></div>
            </div>

            <span class="font-black shrink-0 {isDark ? 'text-slate-100' : 'text-slate-800'}">
              {onlineCount} / {totalCount}
            </span>
          </div>
        {/if}

        <div class="flex justify-between items-center w-full pt-1.5 border-t border-dashed font-mono text-[9px] {isDark ? 'border-slate-700/60' : 'border-slate-200/80'}">
          <button 
            on:click|stopPropagation={() => dispatch('openOltHistory', { contract: `OLT Станция ${olt.ip}`, id: olt.ip })}
            class="px-2.5 py-1 rounded-md border text-[8.5px] font-mono font-extrabold transition-all cursor-pointer shadow-2xs shrink-0 flex items-center gap-1
            {isDark 
              ? 'bg-[#1a263c] border-slate-700/60 text-indigo-300 hover:bg-slate-700 hover:text-white' 
              : 'bg-white border-slate-200/90 text-indigo-600 hover:bg-indigo-50 hover:border-indigo-300'}"
            title="История логов OLT"
          >
            <span>Логи</span>
            <span class="opacity-70 text-[8px]">➔</span>
          </button>

          {#if isOltActive}
            <div class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-mono font-black border shadow-2xs
              {isDark ? 'bg-[#1a263c] border-slate-700/60 text-slate-100' : 'bg-indigo-50/80 border-indigo-200/90 text-indigo-950'}"
            >
              <span class="{isDark ? 'text-indigo-300' : 'text-indigo-600'} font-black text-xs">{healthPercent}%</span>
              <span class="{isDark ? 'text-slate-300' : 'text-slate-500'} text-[8px] uppercase tracking-wider font-bold">онлайн</span>
            </div>
          {:else}
            <div class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[9px] font-mono font-black bg-rose-500/10 text-rose-500 border border-rose-500/20">
              <span>ОФФЛАЙН</span>
            </div>
          {/if}

        </div>
      </div>
    {/each}
  </div>

</div>

<style>
  .cyber-scroll::-webkit-scrollbar {
    width: 4px !important;
  }
  .cyber-scroll::-webkit-scrollbar-track {
    background: transparent !important;
  }
  .cyber-scroll::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%) !important;
    border-radius: 99px !important;
  }
  .cyber-scroll::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #818cf8 0%, #ec4899 100%) !important;
  }
</style>