<!-- frontend/src/components/dashboard/DashboardAnomalies.svelte -->
<script>
  import { data } from '../../stores/networkStore.js';

  export let isDark = false;

  $: anomalyStats = (() => {
    let los = 0; let losi = 0; let dying = 0; let offline = 0;
    const rawData = $data || [];

    rawData.forEach(d => {
      if (d && !d.isSwitch && d.ports) {
        d.ports.forEach(port => {
          if (port && port.onus) {
            port.onus.forEach(onu => {
              if (onu) {
                const state = (onu.state || '').trim().toLowerCase();
                if (state === 'dyinggasp') dying++;
                else if (state === 'offline') offline++;
                else if (state === 'losi') losi++;
                else if (['los', 'down'].includes(state)) los++;
              }
            });
          }
        });
      }
    });

    const total = los + losi + dying + offline;
    return { los, losi, dying, offline, total };
  })();

  $: topBadLocations = (() => {
    let list = [];
    const rawData = $data || [];
    const swNode = rawData.find(d => d && d.isSwitch);
    if (swNode && swNode.ports) {
      swNode.ports.forEach(folder => {
        const total = folder.onus ? folder.onus.length : 0;
        const down = folder.onus ? folder.onus.filter(sw => {
          const state = (sw.state || '').trim().toLowerCase();
          return state !== 'working' && state !== 'host is alive';
        }).length : 0;

        if (down > 0) {
          list.push({ name: folder.name || 'Общая', down, total });
        }
      });
    }
    return list.sort((a, b) => b.down - a.down);
  })();
</script>

<div class="col-span-3 p-5 rounded-2xl border shadow-xs flex flex-col justify-between relative overflow-hidden font-sans
  {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
>
  <div class="pb-3 mb-1 border-b border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} select-none shrink-0">
    <span class="text-[11px] font-semibold uppercase font-mono tracking-wider {isDark ? 'text-slate-300' : 'text-slate-500'}">Анализ аномалий</span>
  </div>

  <div class="flex-1 flex flex-col justify-between py-2 min-h-0 gap-4">
    
    <div class="space-y-3 font-mono text-xs">
      <span class="text-[10px] font-semibold uppercase tracking-wider block mb-1 {isDark ? 'text-slate-300' : 'text-slate-500'}">Распределение по статусам:</span>
      
      <!-- LOS -->
      <div class="space-y-1">
        <div class="flex justify-between font-semibold text-xs">
          <span class="text-rose-500">LOS (Обрыв сигнала)</span>
          <span class="{isDark ? 'text-slate-100' : 'text-slate-900'}">{anomalyStats?.los || 0} шт</span>
        </div>
        <div class="h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-800' : 'bg-slate-100'}">
          <div class="bg-rose-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.los / anomalyStats.total) * 100 : 0}%"></div>
        </div>
      </div>

      <!-- LOSi -->
      <div class="space-y-1">
        <div class="flex justify-between font-semibold text-xs">
          <span class="text-fuchsia-400">LOSi (Затухание/Изгиб)</span>
          <span class="{isDark ? 'text-slate-100' : 'text-slate-900'}">{anomalyStats?.losi || 0} шт</span>
        </div>
        <div class="h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-800' : 'bg-slate-100'}">
          <div class="bg-fuchsia-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.losi / anomalyStats.total) * 100 : 0}%"></div>
        </div>
      </div>

      <!-- DyingGasp -->
      <div class="space-y-1">
        <div class="flex justify-between font-semibold text-xs">
          <span class="text-amber-400">DyingGasp (Питание)</span>
          <span class="{isDark ? 'text-slate-100' : 'text-slate-900'}">{anomalyStats?.dying || 0} шт</span>
        </div>
        <div class="h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-800' : 'bg-slate-100'}">
          <div class="bg-amber-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.dying / anomalyStats.total) * 100 : 0}%"></div>
        </div>
      </div>

      <!-- Offline -->
      <div class="space-y-1">
        <div class="flex justify-between font-semibold text-xs">
          <span class="{isDark ? 'text-slate-300' : 'text-slate-700'}">Offline (Плановое)</span>
          <span class="{isDark ? 'text-slate-100' : 'text-slate-900'}">{anomalyStats?.offline || 0} шт</span>
        </div>
        <div class="h-1.5 rounded-full overflow-hidden {isDark ? 'bg-slate-800' : 'bg-slate-100'}">
          <div class="bg-slate-500 h-full rounded-full transition-all duration-500" style="width: {anomalyStats.total > 0 ? (anomalyStats.offline / anomalyStats.total) * 100 : 0}%"></div>
        </div>
      </div>
    </div>

    <div class="border-t border-dashed {isDark ? 'border-slate-700/60' : 'border-slate-100'} pt-3 select-none font-mono">
      <span class="text-[10px] font-semibold uppercase tracking-wider block mb-2 {isDark ? 'text-slate-300' : 'text-slate-500'}">Очаги падений в группах SW:</span>
      
      {#if topBadLocations.length === 0}
        <div class="text-xs font-medium text-center text-emerald-500 py-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
          Локальных очагов аварий нет
        </div>
      {:else}
        <div class="space-y-1.5 text-xs max-h-[140px] overflow-y-auto always-visible-scroll pr-1">
          {#each topBadLocations as loc}
            <div class="flex justify-between items-center p-2 rounded-lg border transition-colors
              {isDark ? 'bg-slate-800/80 border-slate-700/60' : 'bg-slate-50 border-slate-200/80'}"
            >
              <span class="font-sans font-medium text-xs truncate pr-2 {isDark ? 'text-slate-200' : 'text-slate-800'}" title={loc.name}>
                {loc.name}
              </span>
              <span class="px-2 py-0.5 rounded-md font-mono font-medium border text-[10px] shrink-0
                {isDark ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' : 'bg-rose-50 text-rose-600 border-rose-200'}"
              >
                {loc.down} / {loc.total} DOWN
              </span>
            </div>
          {/each}
        </div>
      {/if}
    </div>

  </div>
</div>