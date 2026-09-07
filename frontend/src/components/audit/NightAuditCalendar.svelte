<!-- frontend/src/components/audit/NightAuditCalendar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let isDark = false;
  export let currentYear = 2026;
  export let currentMonth = 8; // 0..11
  export let selectedDay = 3;
  export let calendarDays = [];
  export let startDayOfWeek = 0;

  const monthNames = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];

  $: totalMonthIncidents = calendarDays.reduce((sum, d) => sum + (d.count || 0), 0);
  $: problemDaysCount = calendarDays.filter(d => (d.count || 0) > 0).length;
</script>

<div class="w-[320px] rounded-2xl border flex flex-col justify-between shrink-0 select-none font-sans transition-all shadow-md overflow-hidden
  {isDark ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200' : 'bg-white border-slate-200/90 text-slate-800'}"
>
  <!-- ВЕРХ КАРТОЧКИ: НАВИГАЦИЯ ПО МЕСЯЦАМ -->
  <div>
    <div class="px-4 py-3 border-b flex items-center justify-between shrink-0
      {isDark ? 'border-slate-700/70 bg-[#24334a]/60' : 'border-slate-100 bg-slate-50/80'}">
      
      <button 
        on:click={() => dispatch('changeMonth', -1)} 
        class="w-7 h-7 rounded-lg border flex items-center justify-center transition-all cursor-pointer active:scale-95 shadow-2xs
        {isDark ? 'border-slate-600/70 bg-[#182335] text-slate-300 hover:text-white hover:bg-slate-700' : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-100'}"
        title="Предыдущий месяц"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
      </button>

      <div class="flex flex-col items-center">
        <span class="text-xs font-black font-mono uppercase tracking-wider {isDark ? 'text-white' : 'text-slate-900'}">
          {monthNames[currentMonth]} {currentYear}
        </span>
        <span class="text-[9px] font-mono font-bold {isDark ? 'text-indigo-400' : 'text-indigo-600'}">
          {totalMonthIncidents} аварий в архиве
        </span>
      </div>

      <button 
        on:click={() => dispatch('changeMonth', 1)} 
        class="w-7 h-7 rounded-lg border flex items-center justify-center transition-all cursor-pointer active:scale-95 shadow-2xs
        {isDark ? 'border-slate-600/70 bg-[#182335] text-slate-300 hover:text-white hover:bg-slate-700' : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-100'}"
        title="Следующий месяц"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </button>
    </div>

    <!-- СЕТКА ДНЕЙ -->
    <div class="p-3">
      <!-- Заголовки дней недели -->
      <div class="grid grid-cols-7 gap-1 text-center font-black text-[9px] text-slate-400 font-mono mb-2 uppercase tracking-widest">
        <span>пн</span><span>вт</span><span>ср</span><span>чт</span><span>пт</span><span class="text-rose-400">сб</span><span class="text-rose-400">вс</span>
      </div>

      <div class="grid grid-cols-7 gap-1.5">
        {#each Array(startDayOfWeek) as _}
          <div class="h-9"></div>
        {/each}

        {#each calendarDays as item}
          {@const isSelected = selectedDay === item.day}
          {@const count = item.count || 0}
          {@const hasProblem = count > 0}
          
          <button 
            on:click={() => dispatch('selectDay', item.day)}
            class="h-9 rounded-xl border flex flex-col items-center justify-between p-1 transition-all duration-150 cursor-pointer active:scale-95 select-none relative
            {isSelected 
              ? (isDark ? 'bg-indigo-600 border-indigo-400 text-white shadow-md shadow-indigo-600/30 font-black ring-2 ring-indigo-400/40' : 'bg-indigo-600 border-indigo-600 text-white shadow-md font-black') 
              : (hasProblem
                  ? (isDark 
                      ? 'bg-[#223046] hover:bg-[#2a3c57] border-slate-700 text-slate-100' 
                      : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-900 shadow-2xs')
                  : (isDark 
                      ? 'bg-[#182335]/40 hover:bg-[#202d42] border-slate-800/80 text-slate-400 hover:text-slate-200' 
                      : 'bg-slate-50/70 hover:bg-slate-100 border-slate-200/60 text-slate-600'))}"
          >
            <span class="text-[11px] font-mono leading-none">{item.day}</span>

            {#if hasProblem}
              <span class="px-1.5 py-0.2 rounded font-mono font-black text-[8px] leading-none shrink-0 border tabular-nums
                {isSelected 
                  ? 'bg-white text-indigo-900 border-white' 
                  : (count >= 50
                      ? (isDark ? 'bg-rose-500 text-white border-rose-400' : 'bg-rose-600 text-white border-rose-600')
                      : (isDark ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' : 'bg-rose-100 text-rose-800 border border-rose-300'))}"
              >
                {count}
              </span>
            {:else}
              <!-- Минималистичная спокойная черта вместо раздражающих зелёных точек -->
              <span class="w-2 h-0.5 rounded-full {isSelected ? 'bg-white/60' : (isDark ? 'bg-slate-700' : 'bg-slate-200')} mb-0.5"></span>
            {/if}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- НИЗ: СВОДКА МЕСЯЦА -->
  <div class="p-3 border-t font-mono text-[10px] {isDark ? 'border-slate-700/60 bg-[#182335]/60' : 'border-slate-100 bg-slate-50/60'}">
    <div class="flex items-center justify-between text-slate-400">
      <span>Дней со сбоями:</span>
      <span class="font-bold {isDark ? 'text-rose-400' : 'text-rose-600'}">{problemDaysCount} дн.</span>
    </div>
    <div class="flex items-center justify-between text-slate-400 mt-1">
      <span>Спокойных смен:</span>
      <span class="font-bold {isDark ? 'text-emerald-400' : 'text-emerald-600'}">{calendarDays.length - problemDaysCount} дн.</span>
    </div>
  </div>
</div>