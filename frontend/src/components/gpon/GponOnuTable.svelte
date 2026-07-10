<!-- frontend\src\components\GponOnuTable.svelte -->
<script>
  import { slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;
  export let pOnus = [];
  export let currentOltIp = "";
  export let currentUnixTime = Math.floor(Date.now() / 1000);
  export let subFilter = 'all'; 
  
  let onuPage = 1;
  const onusPerPage = 20;

  let sortField = 'id';
  let sortDirection = 'asc';
  let copiedKey = null;

  const dispatch = createEventDispatcher();

  function copyText(text, key) {
    if (!text || text === '—') return;
    navigator.clipboard.writeText(text).then(() => {
      copiedKey = key;
      setTimeout(() => {
        if (copiedKey === key) copiedKey = null;
      }, 1500);
    }).catch(err => console.error("Ошибка копирования:", err));
  }

  function getStatusWeight(state) {
    if (!state) return 0;
    const s = state.trim().toLowerCase();
    if (s === 'working' || s === 'host is alive') return 0;
    if (s === 'offline') return 1;
    if (s === 'dyinggasp') return 2;
    if (s === 'losi') return 3;
    return 4;
  }

  function getCustomDotColor(state) {
    if (!state) return 'bg-slate-500';
    const s = state.trim().toLowerCase();
    if (s === 'working' || s === 'host is alive') return 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
    if (s === 'dyinggasp') return 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]';
    if (s === 'losi') return 'bg-fuchsia-400 shadow-[0_0_8px_rgba(217,70,239,0.5)]';
    return 'bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.5)] animate-pulse';
  }

  function getCustomStatusColor(state) {
    if (!state) return 'text-slate-500';
    const s = state.trim().toLowerCase();
    if (s === 'working' || s === 'host is alive') return 'text-emerald-400';
    if (s === 'dyinggasp') return 'text-amber-500';
    if (s === 'losi') return 'text-fuchsia-400';
    if (s === 'offline') return 'text-slate-400 dark:text-slate-500';
    return 'text-rose-500';
  }

  function toggleSort(field) {
    if (sortField === field) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortField = field;
      sortDirection = 'asc';
    }
    onuPage = 1;
  }

  $: filteredOnus = pOnus.filter(o => {
    const s = (o.state || '').trim().toLowerCase();
    if (subFilter === 'online') return s === 'working';
    if (subFilter === 'los') return ['los', 'down'].includes(s);
    if (subFilter === 'losi') return s === 'losi';
    if (subFilter === 'dying') return s === 'dyinggasp';
    if (subFilter === 'offline') return s === 'offline';
    return true;
  });

  $: sortedOnus = [...filteredOnus].sort((a, b) => {
    let valA, valB;
    if (sortField === 'id') {
      valA = parseInt(a.id.split(':').pop(), 10) || 0;
      valB = parseInt(b.id.split(':').pop(), 10) || 0;
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    } else if (sortField === 'contract') {
      valA = (a.contract || '').toLowerCase();
      valB = (b.contract || '').toLowerCase();
      return sortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
    } else if (sortField === 'status') {
      valA = getStatusWeight(a.state);
      valB = getStatusWeight(b.state);
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    } else if (sortField === 'downtime') {
      valA = a.los_time || 0;
      valB = b.los_time || 0;
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    }
    return 0;
  });

  $: totalOnuPages = Math.ceil(sortedOnus.length / onusPerPage);
  $: paginatedOnus = sortedOnus.slice((onuPage - 1) * onusPerPage, onuPage * onusPerPage);
</script>

<div class="flex select-none font-mono text-[9px] font-bold items-center justify-between mb-4 pb-2 border-b border-dashed {isDark ? 'border-white/[0.04]' : 'border-slate-100'}">
  <div class="flex flex-wrap gap-1">
    {#each [
      { id: 'all', label: 'Все', count: pOnus.length, activeDark: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/25', activeLight: 'bg-indigo-50 text-indigo-600 border-indigo-200' },
      { id: 'online', label: 'В сети', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'working').length, activeDark: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25', activeLight: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
      { id: 'los', label: 'LOS', count: pOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length, activeDark: 'bg-rose-500/10 text-rose-400 border-rose-500/25 shadow-[0_2px_10px_rgba(244,63,94,0.1)]', activeLight: 'bg-rose-50 text-rose-600 border-rose-200' },
      { id: 'losi', label: 'LOSi', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length, activeDark: 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/25 shadow-[0_2px_10px_rgba(217,70,239,0.1)]', activeLight: 'bg-fuchsia-50 text-fuchsia-600 border-fuchsia-200' },
      { id: 'dying', label: 'DyingGasp', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'dyinggasp').length, activeDark: 'bg-amber-500/10 text-amber-500 border-amber-500/25', activeLight: 'bg-amber-50 text-amber-600 border-amber-200' },
      { id: 'offline', label: 'Offline', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'offline').length, activeDark: 'bg-slate-500/15 text-slate-400 border-slate-500/25', activeLight: 'bg-slate-100 text-slate-600 border-slate-200' }
    ] as filter}
      <button on:click={() => { subFilter = filter.id; onuPage = 1; }}
        class="px-2.5 py-1.5 rounded-lg border text-[10px] font-bold tracking-wide transition-all duration-150 uppercase font-mono
        {subFilter === filter.id 
          ? (isDark ? filter.activeDark : filter.activeLight) 
          : (isDark 
              ? 'bg-transparent border-transparent text-slate-500 hover:text-slate-300 hover:bg-white/[0.02]' 
              : 'bg-transparent border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50')}"
      >
        {filter.label} <span class="opacity-60 font-semibold font-sans">({filter.count})</span>
      </button>
    {/each}
  </div>

  {#if totalOnuPages > 1}
    <div class="flex items-center gap-1.5 text-[9px] font-bold shrink-0">
      <button on:click={() => onuPage = Math.max(1, onuPage - 1)} disabled={onuPage === 1}
        class="px-2.5 py-1 rounded bg-black/10 dark:bg-black/25 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-35 transition-all text-[9px]"
      >
        ← НАЗАД
      </button>
      <span class="text-slate-400 px-1 font-mono">{onuPage} / {totalOnuPages}</span>
      <button on:click={() => onuPage = Math.min(totalOnuPages, onuPage + 1)} disabled={onuPage === totalOnuPages}
        class="px-2.5 py-1 rounded bg-black/10 dark:bg-black/25 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-35 transition-all text-[9px]"
      >
        ВПЕРЁД →
      </button>
    </div>
  {/if}
</div>

<!-- ИСПРАВЛЕНО: Белый благородный цвет подложки таблицы вместо серого в светлой теме (bg-white) -->
<div class="overflow-hidden w-full border rounded-2xl shadow-sm mt-3
  {isDark ? 'border-slate-800 bg-[#121724]/30' : 'border-slate-200/80 bg-white'}"
>
  <table class="w-full text-left border-collapse table-fixed select-none">
    <thead>
      <!-- ИСПРАВЛЕНО: Убран серый грязный фон заголовка таблицы в светлой теме (bg-slate-50 с высоким контрастом текста) -->
      <tr class="border-b text-[10px] font-black uppercase tracking-widest text-slate-450 dark:text-slate-500 select-none
        {isDark ? 'bg-black/20 text-slate-500' : 'bg-slate-50 text-slate-600'}"
      >
        <th class="py-3 px-5 w-[14%] cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('id')}>
          <div class="flex items-center gap-1">
            <span>ONU</span>
            {#if sortField === 'id'}
              <span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>
            {/if}
          </div>
        </th>

        <th class="py-3 px-5 w-[33%] cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('contract')}>
          <div class="flex items-center gap-1">
            <span>Договор / Адрес</span>
            {#if sortField === 'contract'}
              <span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>
            {/if}
          </div>
        </th>

        <th class="py-3 px-5 w-[20%] text-slate-500 dark:text-slate-500">История</th>

        <th class="py-3 px-5 w-[18%] cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('status')}>
          <div class="flex items-center gap-1">
            <span>Статус</span>
            {#if sortField === 'status'}
              <span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>
            {/if}
          </div>
        </th>

        <th class="py-3 px-5 w-[15%] text-right cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('downtime')}>
          <div class="flex items-center gap-1.5 justify-end">
            <span>Простой</span>
            {#if sortField === 'downtime'}
              <span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>
            {/if}
          </div>
        </th>
      </tr>
    </thead>
    <tbody>
      {#each paginatedOnus as onu, index}
        {@const descParts = onu.contract ? onu.contract.split('|') : []}
        {@const address = descParts[0] ? descParts[0].trim() : '—'}
        {@const stateLower = (onu.state||'').trim().toLowerCase()}
        {@const isUp = ['working', 'host is alive'].includes(stateLower)}

        <!-- ИСПРАВЛЕНО: Чередующиеся строки используют белый и нежный бело-серый тон без грязных оттенков -->
        <tr class="border-b last:border-0 text-xs transition-colors duration-150
          {isDark 
            ? 'border-slate-800/35 hover:bg-indigo-500/[0.02]' 
            : 'border-slate-100 hover:bg-slate-100/60'}
          {isDark 
            ? (index % 2 === 0 ? 'bg-[#151b29]/40' : 'bg-transparent') 
            : (index % 2 === 0 ? 'bg-slate-50/40' : 'bg-transparent')}"
        >
          <td class="py-2.5 px-5 font-mono font-bold text-slate-400">
            #{onu.id.split(':').pop()}
          </td>

          <td class="py-2.5 px-5">
            {#if address === '—'}
              <span class="text-slate-500 font-bold ml-1">—</span>
            {:else}
              <div class="flex items-center gap-1.5 w-fit py-0.5 px-2 rounded-md transition-all select-all font-mono border
                {isDark 
                  ? 'bg-black/15 border-white/[0.03] hover:border-indigo-500/25 group/copy' 
                  : 'bg-slate-100/40 border-slate-200/50 hover:border-indigo-300 group/copy'}"
              >
                <span class="font-mono font-extrabold text-[11px] tracking-tight select-all
                  {isDark ? 'text-slate-100' : 'text-slate-800'}"
                >
                  {address}
                </span>
                
                <button on:click|stopPropagation={() => copyText(address, onu.id)}
                  class="opacity-0 group-hover/copy:opacity-100 p-0.5 rounded transition-all duration-150
                  {isDark ? 'text-slate-500 hover:text-indigo-400 hover:bg-white/[0.06]' : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-200'}"
                  title="Копировать"
                >
                  {#if copiedKey === onu.id}
                    <svg class="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" stroke-width="3.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  {:else}
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08M3.75 18h11.25A2.25 2.25 0 0015 15.75V9.25A2.25 2.25 0 0012.75 7H3.75A2.25 2.25 0 001.5 9.25v6.5A2.25 2.25 0 003.75 18z" />
                    </svg>
                  {/if}
                </button>
              </div>
            {/if}
          </td>

          <td class="py-2.5 px-5">
            <button on:click|stopPropagation={() => dispatch('openHistory', { contract: onu.contract, id: `${currentOltIp}:${onu.id}`, type: 'onu' })}
              class="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md border text-[10px] font-bold font-mono transition-all duration-150
              {isDark 
                ? 'bg-[#121724] border-slate-800/80 hover:bg-indigo-500/10 hover:border-indigo-500/30 text-indigo-400 hover:text-indigo-300' 
                : 'bg-indigo-50 border-indigo-200 text-indigo-600 hover:bg-indigo-600 hover:text-white hover:border-indigo-600 shadow-sm'}"
            >
              <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Логи</span>
            </button>
          </td>

          <td class="py-2.5 px-5">
            <div class="flex items-center gap-1.5 w-fit px-2.5 py-0.5 rounded-full border text-[9px] font-black tracking-widest font-mono uppercase shadow-sm select-none
              {stateLower === 'working' || stateLower === 'host is alive' 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                : stateLower === 'losi'
                  ? 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/20 shadow-fuchsia-500/5'
                  : stateLower === 'dyinggasp'
                    ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                    : stateLower === 'offline'
                      ? 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-rose-500/5'}"
            >
              <span class="w-1 h-1 rounded-full {getCustomDotColor(onu.state)}"></span>
              {onu.state}
            </div>
          </td>

          <td class="py-2.5 px-5 text-right font-mono font-bold text-[10px]">
            {#if !isUp && onu.los_time}
              <span class="px-2 py-0.5 rounded-md border text-rose-400 bg-rose-500/5 border-rose-500/15 shadow-[0_2px_8px_rgba(244,63,94,0.05)]">
                ⏱ {formatLosTime(onu.los_time, currentUnixTime)}
              </span>
            {:else}
              <span class="text-emerald-500 select-none mr-3">✓</span>
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<!-- НИЖНИЙ БЛОК ПАГИНАЦИИ -->
{#if totalOnuPages > 1}
  <div class="flex items-center justify-end gap-1.5 mt-3.5 select-none">
    <button on:click={() => onuPage = Math.max(1, onuPage - 1)}
      disabled={onuPage === 1}
      class="px-2.5 py-1 rounded bg-black/10 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-35 transition-all text-[9px] font-bold"
    >
      ← НАЗАД
    </button>
    <span class="text-slate-400 px-1 font-mono text-[9px]">{onuPage} / {totalOnuPages}</span>
    <button on:click={() => onuPage = Math.min(totalOnuPages, onuPage + 1)}
      disabled={onuPage === totalOnuPages}
      class="px-2.5 py-1 rounded bg-black/10 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-35 transition-all text-[9px] font-bold"
    >
      ВЕРЁД →
    </button>
  </div>
{/if}