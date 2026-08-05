<!-- frontend/src/components/audit/NightAuditCalendar.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let isDark = false;
  export let currentYear = 2026;
  export let currentMonth = 6; // 0..11
  export let selectedDay = 10;
  export let calendarDays = [];
  export let startDayOfWeek = 0;

  const monthNames = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];
</script>

<div class="w-[360px] p-5 rounded-2xl border flex flex-col justify-between shrink-0 select-none font-sans transition-colors
  {isDark ? 'bg-[#1e2a40] border-slate-700/70' : 'bg-white border-slate-200'}"
>
  <div>
    <div class="flex items-center justify-between mb-4 px-1">
      <button 
        on:click={() => dispatch('changeMonth', -1)} 
        class="w-8 h-8 rounded-xl border flex items-center justify-center transition-colors cursor-pointer
        {isDark ? 'border-slate-700/80 bg-[#162238] text-slate-300 hover:text-white hover:bg-slate-700' : 'border-slate-200 bg-slate-50 text-slate-600 hover:text-slate-900 hover:bg-slate-100'}"
        title="Предыдущий месяц"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
      </button>

      <span class="text-sm font-bold font-mono uppercase tracking-wider {isDark ? 'text-slate-100' : 'text-slate-800'}">
        {monthNames[currentMonth]} {currentYear}
      </span>

      <button 
        on:click={() => dispatch('changeMonth', 1)} 
        class="w-8 h-8 rounded-xl border flex items-center justify-center transition-colors cursor-pointer
        {isDark ? 'border-slate-700/80 bg-[#162238] text-slate-300 hover:text-white hover:bg-slate-700' : 'border-slate-200 bg-slate-50 text-slate-600 hover:text-slate-900 hover:bg-slate-100'}"
        title="Следующий месяц"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
      </button>
    </div>

    <div class="grid grid-cols-7 gap-1 text-center font-semibold text-[11px] text-slate-400 font-mono mb-2 uppercase tracking-wider">
      <span>пн</span><span>вт</span><span>ср</span><span>чт</span><span>пт</span><span>сб</span><span>вс</span>
    </div>

    <div class="grid grid-cols-7 gap-1.5">
      {#each Array(startDayOfWeek) as _}
        <div class="h-10"></div>
      {/each}

      {#each calendarDays as item}
        {@const isSelected = selectedDay === item.day}
        {@const hasProblem = item.hasProblem || item.has_problem || (item.count > 0)}
        
        <button on:click={() => dispatch('selectDay', item.day)}
          class="h-10 rounded-xl border flex flex-col items-center justify-between p-1 relative transition-all duration-150 cursor-pointer
          {isSelected 
            ? 'bg-indigo-500 text-white border-indigo-500 shadow-2xs font-bold' 
            : (isDark 
                ? 'bg-[#162238] border-slate-700/60 text-slate-200 hover:bg-slate-700/60 hover:text-white' 
                : 'bg-slate-50/60 border-slate-200/80 text-slate-700 hover:bg-slate-100 hover:text-slate-900')}"
        >
          <span class="text-xs font-mono leading-none">{item.day}</span>

          {#if hasProblem}
            <span class="px-1.5 py-0.2 rounded-md font-mono font-bold text-[8.5px] leading-none shrink-0 border
              {isSelected 
                ? 'bg-white text-rose-600 border-white' 
                : 'bg-rose-500 text-white border-rose-600 shadow-2xs'}"
            >
              {item.count}
            </span>
          {:else}
            <span class="text-[9px] leading-none text-emerald-400 font-bold">✓</span>
          {/if}
        </button>
      {/each}
    </div>
  </div>

  <div class="p-3 rounded-xl border text-[10.5px] font-medium leading-relaxed font-mono mt-4
    {isDark ? 'bg-[#162238] border-slate-700/60 text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-500'}"
  >
    <span class="text-indigo-400 font-bold">Календарный фильтр:</span> на календаре отмечены только дни со сбоями.
  </div>
</div>