<!-- frontend/src/components/dashboard/DashboardTab.svelte -->
<script>
  import { fade } from 'svelte/transition';
  import DashboardAnomalies from './DashboardAnomalies.svelte';
  import DashboardCrisisConsole from './DashboardCrisisConsole.svelte';

  export let isDark = false;
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0, massOlt: 0, massSw: 0 };
</script>

<div class="flex-1 h-full min-h-0 grid grid-cols-10 gap-5 z-10 relative" in:fade={{ duration: 150 }}>
  <!-- 1. СЛЕВА: ТЕЛЕМЕТРИЯ И АНОМАЛИИ (3/10 ШИРИНЫ) -->
  <DashboardAnomalies {isDark} {totalStats} />

  <!-- 2. СПРАВА: ОПЕРАТИВНАЯ КОНСОЛЬ РЕАГИРОВАНИЯ (7/10 ШИРИНЫ) -->
  <DashboardCrisisConsole {isDark} />
</div>