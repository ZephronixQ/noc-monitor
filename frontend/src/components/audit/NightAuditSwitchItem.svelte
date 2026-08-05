<!-- frontend/src/components/audit/NightAuditSwitchItem.svelte -->
<script>
  import { slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';

  export let event = {};
  export let isDark = false;

  const dispatch = createEventDispatcher();
  let isClusterExpanded = false;

  function toggleCluster() {
    isClusterExpanded = !isClusterExpanded;
  }

  $: isCluster = event.is_cluster ?? event.isCluster ?? false;
  $: timeStart = event.time_start || event.timeStart || '';
  $: timeEnd = event.time_end || event.timeEnd || '';
  $: contract = event.contract || '—';
  $: historyList = event.history || [];
</script>

<div class="p-3 rounded-xl border flex flex-col gap-2 transition-colors
  {isDark ? 'bg-[#1a263c] border-slate-700/60' : 'bg-white border-slate-200 shadow-2xs'}"
>
  <div class="flex items-center justify-between gap-3">
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-1.5 mb-1 flex-wrap select-none">
        <span class="font-mono font-bold text-[10px] px-2 py-0.5 rounded border
          {isDark ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30' : 'bg-indigo-50 text-indigo-700 border-indigo-100'}"
        >
          {event.id}
        </span>
        
        {#if isCluster}
          <button on:click|stopPropagation={toggleCluster}
            class="text-[9px] font-bold px-2 py-0.5 rounded-md uppercase font-mono border cursor-pointer transition-colors
            {isDark 
              ? 'bg-amber-500/15 text-amber-300 border-amber-500/30 hover:bg-amber-500/25' 
              : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'}"
          >
            ⚠️ Дребезг: {historyList.length} сбоев {isClusterExpanded ? '▲' : '▼'}
          </button>
        {:else}
          <span class="text-[9px] font-bold bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded uppercase font-mono">
            свитч
          </span>
        {/if}
      </div>
      
      <div class="text-xs font-semibold truncate mt-1 {isDark ? 'text-slate-100' : 'text-slate-800'}" title={contract.split('|')[0].trim()}>
        {contract.split('|')[0].trim()}
      </div>
    </div>

    <div class="flex items-center gap-3 shrink-0 select-none">
      <div class="text-right font-mono text-[10px] leading-tight">
        <span class="text-slate-400 font-medium text-[8px] uppercase tracking-wider block">период</span>
        <span class="text-rose-500 font-bold block">{timeStart}</span>
        <span class="text-slate-400 block text-[9px]">({timeEnd})</span>
      </div>

      <button on:click={() => dispatch('openHistory', { contract: contract, id: event.id, type: 'sw' })}
        class="px-2.5 py-1 rounded-lg border text-[10px] font-bold font-mono transition-colors cursor-pointer
        {isDark ? 'bg-[#1e2a40] border-slate-700 text-indigo-400 hover:text-white hover:bg-slate-700' : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
      >
        Логи
      </button>
    </div>
  </div>

  {#if isCluster && isClusterExpanded}
    <div transition:slide={{duration: 150}} class="pt-2 mt-1 border-t border-dashed text-xs font-mono space-y-1
      {isDark ? 'border-slate-700/60' : 'border-slate-200'}"
    >
      <span class="font-bold text-[9px] uppercase block mb-1 {isDark ? 'text-amber-400' : 'text-amber-600'}">
        Хронология падений за смену:
      </span>
      {#each historyList as item, idx}
        {@const subDuration = item.duration_str || item.duration || ''}
        <div class="flex justify-between text-[10.5px] py-1 px-2 rounded border border-dashed text-slate-300 last:border-0 {isDark ? 'bg-[#1e2a40] border-slate-700/60' : 'bg-slate-50 border-slate-100'}">
          <span>Падение #{idx + 1}: <strong class={isDark ? 'text-rose-400' : 'text-rose-600'}>{item.start} - {item.end}</strong></span>
          <span class="font-bold text-slate-300">⏱ {subDuration}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>