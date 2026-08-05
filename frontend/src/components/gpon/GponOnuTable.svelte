<!-- frontend/src/components/gpon/GponOnuTable.svelte -->
<script>
  import { createEventDispatcher, tick } from 'svelte';
  import { formatLosTime } from '../../utils/helpers.js';

  export let isDark = false;
  export let pOnus = [];
  export let currentOltIp = "";
  export let currentUnixTime = Math.floor(Date.now() / 1000);
  export let subFilter = 'all';

  let onuPage = 1;
  const onusPerPage = 15;

  let sortField = 'id';
  let sortDirection = 'asc';
  let copiedKey = null;
  let tableHeaderRef;

  const dispatch = createEventDispatcher();

  async function scrollToTop() {
    await tick();
    if (tableHeaderRef) {
      tableHeaderRef.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function handlePageChange(newPage) {
    onuPage = newPage;
    scrollToTop();
  }

  function handleFilterChange(newFilter) {
    subFilter = newFilter;
    onuPage = 1;
    scrollToTop();
  }

  function copyText(text, key) {
    if (!text || text === '—') return;
    navigator.clipboard.writeText(text).then(() => {
      copiedKey = key;
      setTimeout(() => {
        if (copiedKey === key) copiedKey = null;
      }, 1500);
    }).catch(err => console.error("Ошибка копирования:", err));
  }

  function getStatusConfig(state) {
    const s = (state || '').trim().toLowerCase();
    if (s === 'working' || s === 'host is alive') {
      return { label: 'WORKING', color: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20', dot: 'bg-emerald-400', weight: 0 };
    }
    if (s === 'losi') {
      return { label: 'LOSi', color: 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/20', dot: 'bg-fuchsia-400', weight: 3 };
    }
    if (s === 'dyinggasp') {
      return { label: 'DYINGGASP', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20', dot: 'bg-amber-500', weight: 2 };
    }
    if (s === 'offline') {
      return { label: 'OFFLINE', color: 'bg-slate-500/10 text-slate-400 border-slate-500/20', dot: 'bg-slate-400', weight: 1 };
    }
    return { label: 'LOS', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20 animate-pulse', dot: 'bg-rose-500', weight: 4 };
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
      valA = getStatusConfig(a.state).weight;
      valB = getStatusConfig(b.state).weight;
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

<div bind:this={tableHeaderRef} class="p-4 border-t border-dashed scroll-mt-20 {isDark ? 'border-slate-700/60 bg-[#1a263c]' : 'border-slate-200 bg-slate-50/50'}">
  
  <!-- ЛИПКАЯ ШАПКА ФИЛЬТРОВ И ПАГИНАЦИИ (STICKY TOP) -->
  <div class="sticky top-[58px] z-20 py-2.5 px-3 rounded-xl backdrop-blur-xl border shadow-md flex select-none font-mono text-[10px] font-black items-center justify-between mb-3.5
    {isDark ? 'bg-[#18253f]/95 border-slate-700/80 shadow-black/40' : 'bg-white/95 border-slate-200/90 shadow-slate-200/50'}"
  >
    <div class="flex flex-wrap gap-2">
      {#each [
        { id: 'all', label: 'ВСЕ', count: pOnus.length, activeLight: 'bg-indigo-600 text-white border-indigo-600 shadow-sm', activeDark: 'bg-indigo-500/25 text-indigo-300 border-indigo-500/50' },
        { id: 'online', label: 'В СЕТИ', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'working').length, activeLight: 'bg-emerald-600 text-white border-emerald-600 shadow-sm', activeDark: 'bg-emerald-500/25 text-emerald-400 border-emerald-500/50' },
        { id: 'los', label: 'LOS', count: pOnus.filter(o => ['los', 'down'].includes((o.state||'').trim().toLowerCase())).length, activeLight: 'bg-rose-600 text-white border-rose-600 shadow-sm', activeDark: 'bg-rose-500/25 text-rose-400 border-rose-500/50' },
        { id: 'losi', label: 'LOSi', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'losi').length, activeLight: 'bg-fuchsia-600 text-white border-fuchsia-600 shadow-sm', activeDark: 'bg-fuchsia-500/25 text-fuchsia-400 border-fuchsia-500/50' },
        { id: 'dying', label: 'DYINGGASP', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'dyinggasp').length, activeLight: 'bg-amber-600 text-white border-amber-600 shadow-sm', activeDark: 'bg-amber-500/25 text-amber-400 border-amber-500/50' },
        { id: 'offline', label: 'OFFLINE', count: pOnus.filter(o => (o.state||'').trim().toLowerCase() === 'offline').length, activeLight: 'bg-slate-700 text-white border-slate-700 shadow-sm', activeDark: 'bg-slate-500/25 text-slate-300 border-slate-500/50' }
      ] as filter}
        <button on:click={() => handleFilterChange(filter.id)}
          class="px-3 py-1.5 rounded-xl border text-[10px] font-black tracking-wider transition-all duration-150 uppercase font-mono cursor-pointer shadow-2xs flex items-center gap-1.5
          {subFilter === filter.id 
            ? (isDark ? filter.activeDark : filter.activeLight) 
            : (isDark 
                ? 'bg-[#1e2a40] border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-700/60' 
                : 'bg-slate-100/90 border-slate-200/90 text-slate-800 hover:text-slate-950 hover:bg-slate-200/80')}"
        >
          <span>{filter.label}</span>
          <span class="font-extrabold font-mono px-1.5 py-0.2 rounded-md
            {subFilter === filter.id ? 'bg-white/20 text-white' : (isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-200/80 text-slate-900')}"
          >
            {filter.count}
          </span>
        </button>
      {/each}
    </div>

    <!-- УДОБНОЕ ПЕРЕКЛЮЧЕНИЕ СТРАНИЦ С АВТОПРОКРУТКОЙ НАВЕРХ -->
    {#if totalOnuPages > 1}
      <div class="flex items-center gap-2 text-[10px] font-bold shrink-0 font-mono">
        <button on:click={() => handlePageChange(Math.max(1, onuPage - 1))} disabled={onuPage === 1}
          class="px-3 py-1.5 rounded-xl border font-black transition-all disabled:opacity-35 cursor-pointer shadow-2xs
          {isDark ? 'bg-[#1e2a40] border-slate-700 text-indigo-300 hover:bg-slate-700 hover:text-white' : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
        >
          ← НАЗАД
        </button>
        
        <span class="text-indigo-400 font-extrabold px-1.5 py-0.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10">
          {onuPage} / {totalOnuPages}
        </span>

        <button on:click={() => handlePageChange(Math.min(totalOnuPages, onuPage + 1))} disabled={onuPage === totalOnuPages}
          class="px-3 py-1.5 rounded-xl border font-black transition-all disabled:opacity-35 cursor-pointer shadow-2xs
          {isDark ? 'bg-[#1e2a40] border-slate-700 text-indigo-300 hover:bg-slate-700 hover:text-white' : 'bg-slate-50 border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
        >
          ВПЕРЁД →
        </button>
      </div>
    {/if}
  </div>

  <!-- ТАБЛИЦА АБОНЕНТОВ -->
  <div class="overflow-hidden w-full border rounded-xl shadow-2xs
    {isDark ? 'border-slate-700/80 bg-[#1e2a40]' : 'border-slate-200 bg-white'}"
  >
    <table class="w-full text-left border-collapse table-fixed select-none font-mono">
      <thead>
        <tr class="border-b text-[9.5px] font-black uppercase tracking-widest select-none
          {isDark ? 'bg-[#1a263c] border-slate-700/80 text-slate-200' : 'bg-slate-100/80 border-slate-200 text-slate-700'}"
        >
          <th class="py-2.5 px-4 w-[12%] cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('id')}>
            <div class="flex items-center gap-1">
              <span>ONU</span>
              {#if sortField === 'id'}<span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>{/if}
            </div>
          </th>

          <th class="py-2.5 px-4 w-[38%] cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('contract')}>
            <div class="flex items-center gap-1">
              <span>Договор / Адрес</span>
              {#if sortField === 'contract'}<span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>{/if}
            </div>
          </th>

          <th class="py-2.5 px-4 w-[18%]">Логи</th>

          <th class="py-2.5 px-4 w-[18%] cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('status')}>
            <div class="flex items-center gap-1">
              <span>Статус</span>
              {#if sortField === 'status'}<span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>{/if}
            </div>
          </th>

          <th class="py-2.5 px-4 w-[14%] text-right cursor-pointer hover:text-indigo-400 transition-colors" on:click={() => toggleSort('downtime')}>
            <div class="flex items-center gap-1 justify-end">
              <span>Простой</span>
              {#if sortField === 'downtime'}<span class="text-[9px] text-indigo-400">{sortDirection === 'asc' ? '▲' : '▼'}</span>{/if}
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        {#each paginatedOnus as onu}
          {@const descParts = onu.contract ? onu.contract.split('|') : []}
          {@const address = descParts[0] ? descParts[0].trim() : '—'}
          {@const cfg = getStatusConfig(onu.state)}
          {@const stateLower = (onu.state||'').trim().toLowerCase()}
          {@const isUp = ['working', 'host is alive'].includes(stateLower)}

          <tr class="border-b last:border-0 text-xs transition-colors duration-150
            {isDark ? 'border-slate-700/60 hover:bg-slate-700/40' : 'border-slate-100 hover:bg-slate-50'}"
          >
            <td class="py-2.5 px-4 font-mono font-black text-[11px] text-indigo-300">
              #{onu.id.split(':').pop()}
            </td>

            <td class="py-2.5 px-4">
              {#if address === '—'}
                <span class="text-slate-400 font-bold ml-1">—</span>
              {:else}
                <div class="flex items-center gap-2 w-fit py-0.5 px-2 rounded-md transition-all select-all font-mono border
                  {isDark ? 'bg-[#1a263c] border-slate-700/60 group/copy' : 'bg-slate-50 border-slate-200 group/copy'}"
                >
                  <span class="font-mono font-bold text-[11px] tracking-tight select-all {isDark ? 'text-slate-100' : 'text-slate-800'}">
                    {address}
                  </span>
                  
                  <button on:click|stopPropagation={() => copyText(address, onu.id)}
                    class="opacity-0 group-hover/copy:opacity-100 p-0.5 rounded transition-all duration-150 cursor-pointer
                    {isDark ? 'text-slate-400 hover:text-indigo-300' : 'text-slate-400 hover:text-indigo-600'}"
                    title="Копировать адрес"
                  >
                    {#if copiedKey === onu.id}
                      <span class="text-[9px] font-black text-emerald-400">✓</span>
                    {:else}
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08M3.75 18h11.25A2.25 2.25 0 0015 15.75V9.25A2.25 2.25 0 0012.75 7H3.75A2.25 2.25 0 001.5 9.25v6.5A2.25 2.25 0 003.75 18z" />
                      </svg>
                    {/if}
                  </button>
                </div>
              {/if}
            </td>

            <td class="py-2.5 px-4">
              <button on:click|stopPropagation={() => dispatch('openHistory', { contract: onu.contract, id: `${currentOltIp}:${onu.id}`, type: 'onu' })}
                class="flex items-center gap-1 px-2 py-0.5 rounded-md border text-[9px] font-bold font-mono transition-all duration-150 cursor-pointer shadow-2xs
                {isDark 
                  ? 'bg-[#1a263c] border-slate-700/60 text-indigo-300 hover:bg-slate-700 hover:text-white' 
                  : 'bg-white border-slate-200 text-indigo-600 hover:bg-indigo-50'}"
              >
                <span>Логи</span>
                <span class="opacity-60 text-[8px]">➔</span>
              </button>
            </td>

            <td class="py-2.5 px-4">
              <div class="flex items-center gap-1.5 w-fit px-2 py-0.5 rounded-full border text-[8.5px] font-black tracking-widest font-mono uppercase shadow-2xs select-none {cfg.color}">
                <span class="w-1 h-1 rounded-full {cfg.dot}"></span>
                <span>{cfg.label}</span>
              </div>
            </td>

            <td class="py-2.5 px-4 text-right font-mono font-extrabold text-[10px]">
              {#if !isUp && onu.los_time}
                <span class="px-2 py-0.5 rounded-md border text-rose-400 bg-rose-500/10 border-rose-500/20">
                  ⏱ {formatLosTime(onu.los_time, currentUnixTime)}
                </span>
              {:else}
                <span class="text-emerald-500 select-none mr-2 font-black">✓</span>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

</div>