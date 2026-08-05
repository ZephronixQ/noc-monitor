<!-- frontend/src/components/audit/NightAuditTab.svelte -->
<script>
  import { fade } from 'svelte/transition';
  import { BACKEND_URL } from '../../stores/networkStore.js';
  
  import NightAuditCalendar from './NightAuditCalendar.svelte';
  import NightAuditEventsList from './NightAuditEventsList.svelte';

  export let isDark = false;

  const today = new Date();
  let currentYear = today.getFullYear();
  let currentMonth = today.getMonth() + 1; // 1..12
  let selectedDay = today.getDate();
  let shiftFilter = 'night';

  const monthNames = [
    '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];

  let calendarDays = [];
  let switchIncidents = [];
  let gponHierarchy = [];
  let isLoading = false;
  let lastFetchKey = '';

  async function fetchAuditData(year, month, day, shift) {
    const fetchKey = `${year}-${month}-${day}-${shift}`;
    if (fetchKey === lastFetchKey) return;
    lastFetchKey = fetchKey;
    
    isLoading = true;

    try {
      const token = localStorage.getItem('noc_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const res = await fetch(`${BACKEND_URL}/api/audit/month?year=${year}&month=${month}&day=${day}&shift=${shift}`, { headers });
      if (res.ok) {
        const json = await res.json();
        calendarDays = json.calendar_days || [];
        switchIncidents = json.switches || [];
        gponHierarchy = json.gpon || [];
      } else {
        console.error("Ошибка API аудита:", res.status);
      }
    } catch (e) {
      console.error("Ошибка загрузки ночного аудита:", e);
    } finally {
      isLoading = false;
    }
  }

  $: fetchAuditData(currentYear, currentMonth, selectedDay, shiftFilter);

  $: daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
  $: startDayOfWeek = (() => {
    let day = new Date(currentYear, currentMonth - 1, 1).getDay();
    return day === 0 ? 6 : day - 1;
  })();

  function handleMonthChange(delta) {
    let newMonth = currentMonth + delta;
    let newYear = currentYear;

    if (newMonth < 1) {
      newMonth = 12;
      newYear -= 1;
    } else if (newMonth > 12) {
      newMonth = 1;
      newYear += 1;
    }

    currentMonth = newMonth;
    currentYear = newYear;

    const maxDays = new Date(currentYear, currentMonth, 0).getDate();
    selectedDay = Math.min(selectedDay, maxDays);
  }
</script>

<div class="flex-1 flex gap-5 overflow-hidden min-h-0" in:fade={{ duration: 150 }}>
  
  <NightAuditCalendar
    {isDark}
    {currentYear}
    currentMonth={currentMonth - 1}
    {selectedDay}
    {calendarDays}
    {startDayOfWeek}
    on:selectDay={(e) => selectedDay = e.detail}
    on:changeMonth={(e) => handleMonthChange(e.detail)}
  />

  <NightAuditEventsList
    {isDark}
    {selectedDay}
    monthName={monthNames[currentMonth]}
    bind:shiftFilter
    {switchIncidents}
    {gponHierarchy}
    {isLoading}
    on:openHistory
  />

</div>