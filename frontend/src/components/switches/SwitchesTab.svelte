<!-- frontend/src/components/switches/SwitchesTab.svelte -->
<script context="module">
  let savedGlobalSwLosFilter = false;
  let savedSwitchSearchQuery = '';
  let savedActiveFolderIndex = 0;
</script>

<script>
  import { createEventDispatcher } from 'svelte';
  import SwitchSidebar from './SwitchSidebar.svelte';
  import SwitchToolbar from './SwitchToolbar.svelte';
  import SwitchCard from './SwitchCard.svelte';

  export let isDark = false;
  export let switchFolders = [];
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  const dispatch = createEventDispatcher();

  let activeFolderIndex = savedActiveFolderIndex;
  let switchSearchQuery = savedSwitchSearchQuery; 
  let globalSwLosFilter = savedGlobalSwLosFilter;

  $: savedActiveFolderIndex = activeFolderIndex;
  $: savedSwitchSearchQuery = switchSearchQuery;
  $: savedGlobalSwLosFilter = globalSwLosFilter;

  $: filteredSwitchFolders = switchFolders.filter(folder => {
    if (!globalSwLosFilter) return true;
    return folder.onus.some(sw => !['working', 'host is alive'].includes((sw.state||'').trim().toLowerCase()));
  });

  $: if (activeFolderIndex >= filteredSwitchFolders.length) activeFolderIndex = 0;
  $: currentSwitchFolder = filteredSwitchFolders[activeFolderIndex] || { onus: [] };
  $: allSwitchesFlat = switchFolders.flatMap(folder => folder.onus || []);

  $: displayedSwitches = switchSearchQuery 
    ? allSwitchesFlat.filter(sw => sw.id.toLowerCase().includes(switchSearchQuery.toLowerCase()) || (sw.contract || '').toLowerCase().includes(switchSearchQuery.toLowerCase()))
    : (currentSwitchFolder.onus || []).filter(sw => !globalSwLosFilter || !['working', 'host is alive'].includes((sw.state||'').trim().toLowerCase()));
</script>

<div class="flex gap-6 h-full overflow-hidden min-h-0">
  
  {#if !switchSearchQuery}
    <SwitchSidebar 
      {isDark} 
      {filteredSwitchFolders} 
      {activeFolderIndex} 
      on:selectFolder={(e) => activeFolderIndex = e.detail}
    />
  {/if}

  <div class="flex-1 flex flex-col gap-2 h-full min-w-0 min-h-0">
    
    <SwitchToolbar 
      {isDark} 
      bind:switchSearchQuery 
      bind:globalSwLosFilter 
    />
    
    <!-- Сетка из 4-х колонок (lg:grid-cols-4) -->
    <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 overflow-y-auto pt-3 px-1 pb-4 content-start always-visible-scroll min-h-0">
      {#each displayedSwitches as sw (sw.id)}
        <SwitchCard 
          {sw} 
          {isDark} 
          {currentUnixTime} 
          on:openHistory={(e) => dispatch('openHistory', e.detail)}
        />
      {/each}
    </div>

  </div>
</div>