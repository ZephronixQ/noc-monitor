<!-- frontend/src/components/common/PollingHud.svelte -->
<script>
  import { fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { 
    pollingProgress, 
    pollingStatusText, 
    isPollingActive, 
    pollingDetectedStats 
  } from '../../stores/networkStore.js';

  export let isDark = false;
</script>

{#if $isPollingActive}
  <div 
    transition:fly={{ y: 20, duration: 250, easing: cubicOut }}
    class="fixed bottom-6 right-8 z-[100] w-84 p-3.5 rounded-2xl border backdrop-blur-2xl select-none flex flex-col gap-2 shadow-2xl transition-all font-sans overflow-hidden
    {isDark 
      ? 'bg-[#182335]/95 border-indigo-500/40 text-slate-100 shadow-[0_12px_40px_rgba(0,0,0,0.5)]' 
      : 'bg-white/95 border-indigo-200 text-slate-900 shadow-[0_12px_35px_rgba(99,102,241,0.15)]'}"
  >
    <!-- ВЕРХНЯЯ СУБПИКСЕЛЬНАЯ СВЕТОВАЯ ФАСКА -->
    <div class="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-indigo-500 to-transparent"></div>

    <!-- ВЕРХ: СПИННЕР + ТИТУЛ + ПРОЦЕНТ -->
    <div class="flex items-center justify-between gap-2 font-mono">
      <div class="flex items-center gap-2">
        <svg class="w-3.5 h-3.5 text-indigo-400 animate-spin" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0H4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        <span class="text-[10.5px] font-bold uppercase tracking-wider {isDark ? 'text-indigo-300' : 'text-indigo-700'}">
          Опрос сетевых узлов
        </span>
      </div>

      <span class="text-xs font-black tabular-nums {isDark ? 'text-white' : 'text-slate-900'}">
        {$pollingProgress}%
      </span>
    </div>

    <!-- ТЕКУЩИЙ СТАТУС (ОБРАБАТЫВАЕМАЯ СТАНЦИЯ ИЛИ СВИЧ) -->
    <div class="text-[11.5px] font-semibold truncate {isDark ? 'text-slate-300' : 'text-slate-700'}">
      {$pollingStatusText || 'Инициализация протоколов...'}
    </div>

    <!-- ТОНКАЯ ИНЖЕНЕРНАЯ ШКАЛА ПРОГРЕССА (2.5px) -->
    <div class="w-full h-[2.5px] rounded-xs overflow-hidden {isDark ? 'bg-slate-700/60' : 'bg-slate-200'}">
      <div 
        class="h-full rounded-xs transition-all duration-300 ease-out bg-gradient-to-r from-indigo-500 via-teal-400 to-emerald-400"
        style="width: {$pollingProgress}%"
      ></div>
    </div>

    <!-- ВСПЛЫВАЮЩИЕ АНОМАЛИИ В ПРОЦЕССЕ ОПРОСА (ЕСЛИ ОБНАРУЖЕНЫ) -->
    {#if $pollingDetectedStats?.los > 0 || $pollingDetectedStats?.losi > 0}
      <div class="flex items-center justify-between pt-1.5 mt-0.5 border-t font-mono text-[9px] font-bold {isDark ? 'border-slate-700/60' : 'border-slate-100'}">
        <span class="text-slate-400 uppercase">Обнаружено в цикле:</span>
        <div class="flex items-center gap-1.5">
          {#if $pollingDetectedStats.los > 0}
            <span class="px-1.5 py-0.2 rounded {isDark ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
              {$pollingDetectedStats.los} LOS
            </span>
          {/if}
          {#if $pollingDetectedStats.losi > 0}
            <span class="px-1.5 py-0.2 rounded {isDark ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'bg-purple-100 text-purple-800 border border-purple-300'}">
              {$pollingDetectedStats.losi} LOSi
            </span>
          {/if}
        </div>
      </div>
    {/if}
  </div>
{/if}