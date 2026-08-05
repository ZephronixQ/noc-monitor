<!-- frontend/src/components/switches/SwitchCard.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { formatLosTime } from '../../utils/helpers.js';

  export let sw = {};
  export let isDark = false;
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();

  $: isUp = ['working', 'host is alive'].includes((sw.state || '').trim().toLowerCase());
  $: descParts = sw.contract ? sw.contract.split('|') : [];
  $: address = descParts[0] ? descParts[0].trim() : '—';
  $: deviceModel = descParts[1] ? descParts[1].trim() : '';
</script>

<div 
  on:click={() => dispatch('openHistory', { contract: sw.contract, id: sw.id })}
  class="group relative px-4 py-3.5 rounded-2xl border transition-all duration-200 transform hover:-translate-y-0.5 cursor-pointer select-none flex flex-col justify-between min-h-[114px] overflow-hidden
  {isUp 
    ? (isDark 
        ? 'bg-[#1e2a40] border-slate-700/70 hover:border-emerald-500/50' 
        : 'bg-white border-slate-200 hover:border-emerald-400 hover:shadow-xs') 
    : (isDark 
        ? 'bg-[#1e2a40] border-slate-700/70 hover:border-rose-500/60' 
        : 'bg-white border-slate-200 hover:border-rose-300 hover:shadow-xs')}"
>
  {#if !isUp}
    <div class="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-rose-500 via-purple-500 to-amber-500"></div>
  {:else}
    <div class="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-emerald-400 via-teal-400 to-indigo-500"></div>
  {/if}

  <div class="flex items-center justify-between gap-3 pt-0.5 relative z-10">
    <span class="font-mono font-bold text-xs px-2.5 py-0.5 rounded-lg tracking-wide transition-all
      {isDark 
        ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30' 
        : 'bg-indigo-50 text-indigo-700 border border-indigo-100'}"
    >
      {sw.id}
    </span>

    {#if !isUp}
      <div class="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold text-rose-500 bg-rose-500/10 border border-rose-500/25 uppercase tracking-wider">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
        </span>
        <span>{sw.state ? sw.state.toUpperCase() : 'LOS'}</span>
      </div>
    {:else}
      <div class="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold text-emerald-500 bg-emerald-500/10 border border-emerald-500/25 uppercase tracking-wider">
        <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
        <span>ONLINE</span>
      </div>
    {/if}
  </div>

  <div class="my-2 relative z-10">
    <div class="text-[13px] font-bold leading-snug tracking-tight truncate transition-colors
      {isDark ? 'text-slate-100 group-hover:text-indigo-300' : 'text-slate-800 group-hover:text-indigo-600'}" 
      title={address}
    >
      {address}
    </div>
  </div>

  <div class="flex items-center justify-between pt-2 border-t border-dashed font-mono text-[10px] relative z-10
    {isDark ? 'border-slate-700/60' : 'border-slate-100'}"
  >
    <div class="flex items-center gap-1 font-medium text-slate-400 truncate max-w-[200px]" title={deviceModel}>
      <span class="text-indigo-500 dark:text-indigo-400 font-bold text-[10px]">⑂</span>
      <span class="truncate text-[9px] uppercase tracking-wider">{deviceModel || 'Коммутатор'}</span>
    </div>

    {#if !isUp && sw.los_time}
      <span class="font-semibold text-rose-500 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-md border border-rose-500/20">
        ⏱ {formatLosTime(sw.los_time, currentUnixTime)}
      </span>
    {/if}
  </div>
</div>