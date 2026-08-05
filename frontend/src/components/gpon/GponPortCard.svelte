<!-- frontend/src/components/gpon/GponPortCard.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import GponOnuTable from './GponOnuTable.svelte';

  export let isDark = false;
  export let port = {};
  export let currentOltIp = '';
  export let currentUnixTime = Math.floor(Date.now() / 1000);
  export let activePort = null;
  export let globalLosFilter = false;
  export let globalLosiFilter = false;

  const dispatch = createEventDispatcher();

  $: pOnus = port.onus || [];
  $: strictLosCount = pOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length;
  $: losiCount = pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length;
  $: isExpanded = activePort === port.name;

  function exportPortCsv(p) {
    let csvContent = "data:text/csv;charset=utf-8,ID,Договор/Адрес,Статус\n";
    (p.onus || []).forEach(o => {
      csvContent += `"${o.id || ''}","${o.contract || ''}","${o.state || ''}"\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `export_port_${p.name}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
</script>

<div class="rounded-2xl shrink-0 border transition-all duration-200 shadow-2xs relative
  {port.is_mass_outage 
    ? (isDark ? 'border-rose-900/80 bg-rose-950/20' : 'border-rose-300 bg-rose-50/50') 
    : (isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200/80')}"
>
  <div 
    class="flex items-center justify-between pr-5 cursor-pointer select-none transition-all duration-150 rounded-2xl
    {isExpanded ? 'sticky top-0 z-30 shadow-md border-b' : ''}
    {port.is_mass_outage 
      ? (isDark ? 'bg-rose-950/95 border-rose-900' : 'bg-rose-50 border-rose-200') 
      : (isDark ? 'bg-[#1e2a40]/95 border-slate-700/80' : 'bg-white/95 border-slate-200')}"
    on:click={(e) => dispatch('togglePort', { name: port.name, event: e })}
  >
    <div class="flex-1 flex items-center gap-6 p-4">
      <div class="flex items-center gap-2">
        <span class="font-mono font-black w-14 text-base {isDark ? 'text-indigo-400' : 'text-indigo-600'}">{port.name}</span>
        <span class="text-xs text-slate-400 transition-transform duration-200 {isExpanded ? 'rotate-180 text-indigo-500 font-bold' : ''}">▼</span>
      </div>
      
      {#if port.is_mass_outage}
        <span class="px-2.5 py-0.5 text-[8px] font-black rounded-md bg-rose-500 text-white shadow-xs animate-pulse uppercase tracking-widest font-mono">Авария платы</span>
      {:else}
        <!-- ИСПРАВЛЕННЫЙ ТРЕК ПРОГРЕСС-БАРА ПЛАТЫ -->
        <div class="w-64 h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-700/80' : 'bg-slate-200/80'}">
          <div class="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full transition-all duration-300" style="width: {pOnus.length > 0 ? ((pOnus.length - (strictLosCount + losiCount))/pOnus.length)*100 : 0}%"></div>
        </div>
      {/if}
      
      <div class="text-[11px] font-bold flex gap-2 font-mono">
        {#if strictLosCount > 0}<span class="text-rose-500">{strictLosCount} LOS</span>{/if}
        {#if losiCount > 0}<span class="text-fuchsia-500">{losiCount} LOSi</span>{/if}
        {#if strictLosCount === 0 && losiCount === 0}<span class="text-emerald-500 font-extrabold">✓ 0 проблем</span>{/if}
        <span class="text-slate-400 select-none">/ {pOnus.length} ONU</span>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      {#if isExpanded}
        <span class="text-[9px] font-mono font-black text-indigo-400 uppercase tracking-wider hidden sm:inline">
          Клик для закрытия
        </span>
      {/if}

      <button on:click|stopPropagation={() => exportPortCsv(port)} 
        class="text-[9px] font-mono font-bold px-2.5 py-1 rounded-lg transition-all border cursor-pointer shadow-2xs
        {isDark ? 'bg-[#152033] border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'}"
      >
        CSV
      </button>
    </div>
  </div>

  {#if isExpanded}
    <GponOnuTable 
      {isDark} 
      {pOnus} 
      {currentOltIp} 
      {currentUnixTime} 
      subFilter={globalLosFilter ? 'los' : (globalLosiFilter ? 'losi' : 'all')}
      on:openHistory
    />
  {/if}
</div>