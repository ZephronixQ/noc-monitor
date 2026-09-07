<!-- frontend/src/components/audit/NightAuditSwitchItem.svelte -->
<script>
  import { slide } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { createEventDispatcher } from 'svelte';

  export let event = {};
  export let isDark = false;

  const dispatch = createEventDispatcher();
  let isClusterExpanded = false;
  let copied = false;

  function toggleCluster() {
    isClusterExpanded = !isClusterExpanded;
  }

  function copyIp(e) {
    e.stopPropagation();
    if (!event.id) return;
    navigator.clipboard.writeText(event.id);
    copied = true;
    setTimeout(() => { copied = false; }, 1200);
  }

  // Определение: является ли узел головной OLT станцией (172.31.2.11 - 172.31.2.19)
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

  $: isOlt = isOltDevice(event.id, event.contract);
  $: isCluster = event.is_cluster ?? event.isCluster ?? false;
  $: timeStart = event.time_start || event.timeStart || '';
  $: timeEnd = event.time_end || event.timeEnd || '';
  $: contract = event.contract || '—';
  
  $: rawAddress = contract.split('|')[0]?.trim();
  $: address = (() => {
    if (rawAddress && rawAddress !== '—') return rawAddress;
    if (isOlt) return `OLT станция`;
    return 'Узел без описания в биллинге';
  })();

  $: historyList = event.history || [];
</script>

<!-- КАРТОЧКА УЗЛА: МЯГКИЙ СВЕТЛЫЙ ФОН #2a3a52 В ТЁМНОЙ ТЕМЕ БЕЗ ТЁМНЫХ ПРОВАЛОВ -->
<div class="p-3 rounded-xl border flex flex-col gap-2 transition-all duration-150 group
  {isDark 
    ? 'bg-[#2a3a52] border-slate-600/70 hover:border-indigo-400/50 text-slate-100 shadow-sm' 
    : 'bg-white border-slate-200 hover:border-slate-300 shadow-2xs text-slate-900'}"
>
  <div class="flex items-center justify-between gap-3">
    
    <!-- ЛЕВАЯ ЧАСТЬ: IP + БЕЙДЖИ + АДРЕС -->
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-1.5 mb-1 flex-wrap select-none font-mono">
        <span class="font-bold text-[11px] px-2 py-0.5 rounded-lg border tracking-wide transition-colors
          {isDark 
            ? (isOlt ? 'bg-[#24334a] text-purple-300 border-purple-500/40' : 'bg-[#24334a] text-indigo-300 border-slate-500/70') 
            : (isOlt ? 'bg-purple-50 text-purple-800 border-purple-200' : 'bg-slate-100 text-indigo-800 border-slate-200')}">
          {event.id}
        </span>

        <button 
          on:click={copyIp}
          class="opacity-60 group-hover:opacity-100 text-[10px] text-slate-400 hover:text-indigo-400 transition-opacity p-0.5 cursor-pointer"
          title="Копировать IP"
        >
          {copied ? '✓' : '⧉'}
        </button>
        
        {#if isCluster}
          <button 
            on:click|stopPropagation={toggleCluster}
            class="text-[9.5px] font-extrabold px-2 py-0.5 rounded-md uppercase font-mono border cursor-pointer transition-all flex items-center gap-1 active:scale-95
            {isDark 
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30' 
              : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'}"
          >
            <span>⚠️ Дребезг: {historyList.length} сбоев</span>
            <span class="text-[8px]">{isClusterExpanded ? '▲' : '▼'}</span>
          </button>
        {:else if isOlt}
          <span class="text-[9px] font-extrabold px-2 py-0.5 rounded-md uppercase font-mono border
            {isDark ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' : 'bg-purple-100 text-purple-800 border border-purple-300'}">
            ⚙️ GPON OLT
          </span>
        {:else}
          <span class="text-[9px] font-bold px-1.5 py-0.2 rounded uppercase font-mono border
            {isDark ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30' : 'bg-indigo-50 text-indigo-700 border-indigo-200'}">
            L2 Свитч
          </span>
        {/if}
      </div>
      
      <!-- НАЗВАНИЕ / АДРЕС УЗЛА -->
      <div class="text-xs font-bold leading-snug truncate mt-0.5
        {isDark ? 'text-slate-100' : 'text-slate-900'} 
        {address.startsWith('Головная OLT') ? (isDark ? 'text-purple-300' : 'text-purple-800') : ''}
        {address === 'Узел без описания в биллинге' ? 'opacity-60 italic text-[11px]' : ''}" 
        title={address}
      >
        {address}
      </div>
    </div>

    <!-- ПРАВАЯ ЧАСТЬ: ПЕРИОД + КНОПКА ЛОГОВ -->
    <div class="flex items-center gap-2.5 shrink-0 select-none">
      <div class="text-right font-mono text-[10px] leading-tight">
        <span class="text-slate-400 font-bold text-[8px] uppercase tracking-wider block">период</span>
        <span class="text-rose-500 font-bold block">{timeStart}</span>
        <span class="text-slate-400 block text-[9px]">({timeEnd})</span>
      </div>

      <button 
        on:click={() => dispatch('openHistory', { contract: contract || address, id: event.id, type: isOlt ? 'olt' : 'sw' })}
        class="px-2.5 py-1 rounded-lg border text-[9.5px] font-bold font-mono transition-all cursor-pointer shadow-2xs active:scale-95
        {isDark 
          ? 'bg-[#223046] border-slate-500/70 text-indigo-300 hover:bg-[#283852] hover:text-white' 
          : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
      >
        Логи
      </button>
    </div>
  </div>

  <!-- ВЛОЖЕННЫЙ ТАЙМЛАЙН ХРОНОЛОГИИ ДРЕБЕЗГА (СВЕТЛЫЙ ФОН #24334a БЕЗ ЧЁРНЫХ ПРОВАЛОВ) -->
  {#if isCluster && isClusterExpanded}
    <div transition:slide={{duration: 140, easing: cubicOut}} class="pt-2 mt-1 border-t font-mono space-y-1.5
      {isDark ? 'border-slate-600/60' : 'border-slate-100'}"
    >
      <span class="font-bold text-[9px] uppercase tracking-wider block {isDark ? 'text-amber-400' : 'text-amber-600'}">
        Хронология скачков за смену:
      </span>

      <div class="space-y-1">
        {#each historyList as item, idx}
          {@const subDuration = item.duration_str || item.duration || ''}
          <div class="flex justify-between items-center text-[10px] py-1 px-2.5 rounded-lg border
            {isDark ? 'bg-[#24334a] border-slate-600/70 text-slate-200' : 'bg-slate-50 border-slate-200 text-slate-800'}">
            <div class="flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
              <span class="text-slate-400">Сбой #{idx + 1}:</span>
              <strong class="{isDark ? 'text-rose-400' : 'text-rose-600'} font-bold">{item.start} — {item.end}</strong>
            </div>
            <span class="font-bold tabular-nums text-slate-400">⏱ {subDuration}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>