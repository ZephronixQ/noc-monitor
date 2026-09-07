<!-- frontend/src/components/switches/SwitchCard.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { formatLosTime } from '../../utils/helpers.js';

  export let sw = {};
  export let isDark = false;
  export let currentUnixTime = Math.floor(Date.now() / 1000);
  export let isSearchMode = false;

  const dispatch = createEventDispatcher();
  let copied = false;

  $: isUp = ['working', 'host is alive'].includes((sw.state || '').trim().toLowerCase());
  $: descParts = sw.contract ? sw.contract.split('|') : [];
  $: address = descParts[0] ? descParts[0].trim() : '—';
  $: deviceModel = descParts[1] ? descParts[1].trim() : (descParts[0]?.includes('MES') ? descParts[0] : 'L2 Switch');
  $: proto = sw.proto || 'SNMP'; // "SNMP" или "PING"

  function copyIp(e) {
    e.stopPropagation();
    navigator.clipboard.writeText(sw.id);
    copied = true;
    setTimeout(() => { copied = false; }, 1200);
  }
</script>

<div 
  on:click={() => dispatch('openHistory', { contract: sw.contract, id: sw.id })}
  class="group relative p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer select-none flex flex-col justify-between overflow-hidden min-h-[124px]
  {isUp 
    ? (isDark 
        ? 'bg-[#223046]/80 hover:bg-[#283952] border-slate-700/60 hover:border-slate-600 shadow-md' 
        : 'bg-white hover:bg-slate-50/90 border-slate-200 hover:border-slate-300 shadow-2xs') 
    : (isDark 
        ? 'bg-[#223046]/95 hover:bg-[#283952] border-rose-500/50 hover:border-rose-400 shadow-md' 
        : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-rose-300 shadow-2xs')}"
>
  <!-- ВЕРХНИЙ СВЕТОВОЙ ИНДИКАТОР -->
  <div class="absolute top-0 inset-x-0 h-[2.5px] {isUp ? (isDark ? 'bg-emerald-500' : 'bg-emerald-600') : 'bg-rose-500'}"></div>

  <!-- ВЕРХ: IP + ПРОТОКОЛ (SNMP / PING) + СТАТУС -->
  <div class="flex items-center justify-between gap-2 pt-0.5">
    <div class="flex items-center gap-1.5 font-mono">
      <span class="font-bold text-xs px-2.5 py-0.5 rounded-lg border tracking-wide transition-colors
        {isDark ? 'bg-[#182335] text-indigo-300 border-slate-600/70' : 'bg-slate-100 text-indigo-800 border border-slate-200'}">
        {sw.id}
      </span>
      <button 
        on:click={copyIp}
        class="opacity-60 group-hover:opacity-100 text-[10px] text-slate-400 hover:text-indigo-400 transition-opacity p-0.5 cursor-pointer"
        title="Копировать IP"
      >
        {copied ? '✓' : '⧉'}
      </button>
    </div>

    <!-- БЛОК СТАТУСА И ПРОТОКОЛА -->
    <div class="flex items-center gap-1.5 font-mono">
      {#if !isUp}
        <div class="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9.5px] font-bold uppercase tracking-wider
          {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
          <span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span>
          <span>DOWN</span>
        </div>
      {:else}
        <!-- БЕЙДЖ ПРОТОКОЛА: SNMP или PING -->
        {#if proto === 'PING'}
          <span class="px-1.5 py-0.2 rounded text-[8.5px] font-bold border tracking-wider
            {isDark ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-amber-50 text-amber-700 border-amber-200'}"
            title="SNMP не ответил. Узел работает по ICMP Ping">
            PING
          </span>
        {:else}
          <span class="px-1.5 py-0.2 rounded text-[8.5px] font-bold border tracking-wider
            {isDark ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40' : 'bg-indigo-50 text-indigo-700 border-indigo-200'}"
            title="Опрос по протоколу SNMP">
            SNMP
          </span>
        {/if}

        <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[9.5px] font-bold uppercase tracking-wider
          {isDark ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'}">
          <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-emerald-400' : 'bg-emerald-600'}"></span>
          <span>ONLINE</span>
        </div>
      {/if}
    </div>
  </div>

  <!-- СЕРЕДИНА: АДРЕС УЗЛА -->
  <div class="my-2">
    <div class="text-[13px] font-bold leading-snug tracking-tight truncate transition-colors
      {isDark ? 'text-slate-100 group-hover:text-indigo-300' : 'text-slate-900 group-hover:text-indigo-700'}" 
      title={address}
    >
      {address}
    </div>
    
    {#if isSearchMode && sw.folderName}
      <div class="text-[10px] font-mono {isDark ? 'text-slate-400' : 'text-slate-600'} mt-1 font-semibold flex items-center gap-1 truncate">
        <span>📁 {sw.folderName}</span>
      </div>
    {/if}
  </div>

  <!-- НИЗ: МОДЕЛЬ + ТАЙМЕР -->
  <div class="flex items-center justify-between pt-2 border-t font-mono text-[10px]
    {isDark ? 'border-slate-700/60' : 'border-slate-100'}"
  >
    <div class="flex items-center gap-1.5 font-medium truncate max-w-[170px] {isDark ? 'text-slate-400' : 'text-slate-600'}" title={deviceModel}>
      <span class="{isDark ? 'text-indigo-400' : 'text-indigo-600'} font-bold">⑂</span>
      <span class="truncate text-[9.5px] uppercase tracking-wider font-semibold">{deviceModel}</span>
    </div>

    {#if !isUp && sw.los_time}
      <span class="font-bold tabular-nums px-2 py-0.5 rounded-md border
        {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
        ⏱ {formatLosTime(sw.los_time, currentUnixTime)}
      </span>
    {/if}
  </div>
</div>