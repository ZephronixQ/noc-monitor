<!-- frontend/src/components/switches/SwitchSidebar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let isDark = false;
  export let filteredSwitchFolders = [];
  export let activeFolderIndex = 0;

  function getNodesText(count) {
    const num = Math.abs(count) % 100;
    const num10 = num % 10;
    if (num > 10 && num < 20) return `${count} узлов`;
    if (num10 > 1 && num10 < 5) return `${count} узла`;
    if (num10 === 1) return `${count} узел`;
    return `${count} узлов`;
  }
</script>

<div class="w-56 h-full flex flex-col gap-2 overflow-y-auto pr-2 pb-4 cyber-scroll min-h-0 select-none">
  
  <!-- Заголовок -->
  <div class="flex items-center justify-between px-2 py-1 shrink-0">
    <div class="flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-indigo-500"></span>
      <span class="text-[10px] font-black uppercase tracking-widest font-mono {isDark ? 'text-slate-300' : 'text-slate-700'}">
        Локации
      </span>
    </div>

    <span class="font-mono font-black text-[9px] px-2.5 py-0.5 rounded-full border tracking-wider
      {isDark 
        ? 'bg-[#1e2a40] text-indigo-300 border-slate-700/70' 
        : 'bg-indigo-50 text-indigo-700 border-indigo-200'}"
    >
      {filteredSwitchFolders.length} СЕТЕЙ
    </span>
  </div>

  <!-- Обновленный мягкий графитовый контейнер (#1e2a40) -->
  <div class="p-1.5 rounded-2xl border shadow-xs flex flex-col gap-1 transition-colors duration-200
    {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
  >
    {#each filteredSwitchFolders as folder, i}
      {@const downs = folder.onus.filter(s => !['working', 'host is alive'].includes((s.state||'').trim().toLowerCase())).length}
      {@const total = folder.onus.length}
      {@const isActive = activeFolderIndex === i}
      
      <button 
        on:click={() => dispatch('selectFolder', i)} 
        class="w-full px-3 py-2.5 rounded-xl text-left transition-all duration-150 flex items-center justify-between gap-2 group cursor-pointer relative overflow-hidden transform hover:translate-x-1
        {isActive 
          ? (isDark 
              ? 'bg-gradient-to-r from-indigo-500/30 via-purple-500/20 to-transparent border-indigo-500/50 text-white font-black' 
              : 'bg-gradient-to-r from-indigo-50 via-purple-50/70 to-transparent border-indigo-200 text-indigo-950 font-black') 
          : (isDark 
              ? 'text-slate-300 hover:text-white hover:bg-slate-700/60 border border-transparent' 
              : 'text-slate-700 hover:text-slate-900 hover:bg-slate-50 border border-transparent')}"
      >
        {#if isActive}
          <div class="absolute left-0 top-1 bottom-1 w-1 bg-gradient-to-b from-indigo-500 via-purple-500 to-pink-500 rounded-r-full"></div>
        {/if}

        <div class="min-w-0 flex-1 pl-1">
          <div class="text-[11.5px] font-extrabold leading-tight line-clamp-1" title={folder.name}>{folder.name}</div>
          <div class="text-[9px] font-mono opacity-50 font-semibold mt-0.5">{getNodesText(total)}</div>
        </div>

        {#if downs > 0} 
          <span class="text-[9px] font-black font-mono px-2 py-0.5 rounded-md shrink-0
            {isActive 
              ? 'bg-rose-500 text-white' 
              : (isDark ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30' : 'bg-rose-50 text-rose-600 border border-rose-200')}"
          >
            {downs}/{total}
          </span>
        {:else} 
          <span class="text-[9px] font-mono font-extrabold text-emerald-500 shrink-0">
            OK
          </span> 
        {/if}
      </button>
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