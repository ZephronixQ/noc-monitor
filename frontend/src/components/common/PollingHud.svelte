<!-- frontend/src/components/common/PollingHud.svelte -->
<script>
  import { fly } from 'svelte/transition';
  import { pollingProgress, pollingStatusText, isPollingActive } from '../../stores/networkStore.js';

  export let isDark = false;
</script>

{#if $isPollingActive}
  <div 
    transition:fly={{ y: 25, duration: 250 }}
    class="fixed bottom-6 right-8 z-[100] w-80 p-4 rounded-2xl border shadow-2xl backdrop-blur-2xl select-none flex flex-col gap-2.5 overflow-hidden transition-colors font-sans
    {isDark 
      ? 'bg-[#1e2a40]/95 border-indigo-500/50 text-slate-100 shadow-[0_10px_40px_rgba(0,0,0,0.4)]' 
      : 'bg-white/95 border-indigo-200 text-slate-900 shadow-[0_10px_30px_rgba(99,102,241,0.15)]'}"
  >
    <!-- Радужный неоновый контур сверху -->
    <div class="absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>

    <!-- Заголовок и Процент -->
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-2 font-mono text-[10px] font-black uppercase tracking-wider text-indigo-400">
        <span class="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
        <span>Синхронизация сети</span>
      </div>

      <span class="font-mono font-black text-xs text-indigo-300">
        {$pollingProgress}%
      </span>
    </div>

    <!-- Сообщение о статусе -->
    <div class="text-[11px] font-extrabold truncate text-slate-200 font-sans">
      {$pollingStatusText || 'Инициализация...'}
    </div>

    <!-- Прогресс-Бар -->
    <div class="w-full h-1.5 bg-slate-700/80 rounded-full overflow-hidden">
      <div 
        class="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-300 rounded-full"
        style="width: {$pollingProgress}%"
      ></div>
    </div>
  </div>
{/if}