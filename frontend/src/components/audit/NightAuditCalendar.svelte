<!-- frontend\src\components\NightAuditCalendar.svelte -->
<script>
  // ИСПРАВЛЕНО: Добавлен явный импорт createEventDispatcher для работы сетки календаря
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let isDark = false;
  export let currentYear = 2026;
  export let currentMonth = 6;
  export let selectedDay = 10;
  export let calendarDays = []; // [{ day, hasProblem, count }]
  export let startDayOfWeek = 2;

  const monthNames = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];
</script>

<div class="w-[380px] p-5 rounded-[24px] border flex flex-col justify-between shrink-0 select-none
  {isDark ? 'bg-[#161f33] border-slate-800/80 shadow-md' : 'bg-white border-slate-200/60 shadow-sm'}"
>
  <div>
    <!-- Выбор месяца -->
    <div class="flex items-center justify-between mb-4 px-1">
      <button on:click={() => dispatch('changeMonth', -1)} class="p-1.5 rounded-lg border hover:bg-black/10 transition-colors {isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-600'}">
        ◀
      </button>
      <span class="text-sm font-black uppercase tracking-wider {isDark ? 'text-slate-100' : 'text-slate-800'}">
        {monthNames[currentMonth]} {currentYear}
      </span>
      <button on:click={() => dispatch('changeMonth', 1)} class="p-1.5 rounded-lg border hover:bg-black/10 transition-colors {isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-600'}">
        ▶
      </button>
    </div>

    <!-- Заголовки дней -->
    <div class="grid grid-cols-7 gap-1 text-center font-bold text-[10px] text-slate-400 dark:text-slate-500 font-mono mb-2 uppercase tracking-wider">
      <span>пн</span><span>вт</span><span>ср</span><span>чт</span><span>пт</span><span>сб</span><span>вс</span>
    </div>

    <!-- Сетка дней -->
    <div class="grid grid-cols-7 gap-1.5">
      {#each Array(startDayOfWeek) as _}
        <div class="h-11"></div>
      {/each}

      {#each calendarDays as item}
        <button on:click={() => dispatch('selectDay', item.day)}
          class="h-11 rounded-xl border flex flex-col items-center justify-between p-1.5 relative transition-all duration-200
          {selectedDay === item.day 
            ? 'bg-indigo-500 text-white border-indigo-500 shadow-[0_4px_12px_rgba(99,102,241,0.35)]' 
            : (isDark 
                ? 'bg-slate-900/40 border-slate-800/50 text-slate-300 hover:bg-slate-800/50' 
                : 'bg-slate-50/50 border-slate-200/50 text-slate-700 hover:bg-slate-100')}"
        >
          <span class="text-xs font-black font-mono leading-none">{item.day}</span>

          {#if item.hasProblem}
            <span class="w-4 h-4 rounded-full flex items-center justify-center font-mono font-bold text-[8px] leading-none shadow-sm
              {selectedDay === item.day 
                ? 'bg-white text-rose-600' 
                : 'bg-rose-500 text-white animate-pulse'}"
            >
              {item.count}
            </span>
          {:else}
            <span class="text-[8px] leading-none text-emerald-400 select-none font-bold">✓</span>
          {/if}
        </button>
      {/each}
    </div>
  </div>

  <div class="p-3.5 rounded-2xl border text-[10px] font-bold text-slate-400 leading-relaxed font-mono mt-4
    {isDark ? 'bg-black/15 border-slate-800/80' : 'bg-slate-50 border-slate-200'}"
  >
    <span class="text-indigo-400">Календарный фильтр:</span> на календаре отмечены только те дни, по которым в базе данных истории NOC зафиксированы сбои.
  </div>
</div>