<!-- frontend/src/components/dashboard/DashboardTab.svelte -->
<script>
  import { fade } from 'svelte/transition';
  import DashboardMetrics from './DashboardMetrics.svelte';
  import DashboardCrisisConsole from './DashboardCrisisConsole.svelte';
  import DashboardAnomalies from './DashboardAnomalies.svelte';

  export let isDark = false;
  export let dailyStats = { total_24h: 0, avg_repair_minutes: 0, active_now: 0 };
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0, massOlt: 0, massSw: 0 };
</script>

<div class="flex flex-col gap-5 h-full min-h-0 z-10 relative" in:fade={{ duration: 150 }}>
  <DashboardMetrics {isDark} {dailyStats} {totalStats} />

  <div class="flex-1 min-h-0 grid grid-cols-10 gap-5">
    <DashboardCrisisConsole {isDark} />
    <DashboardAnomalies {isDark} />
  </div>
</div>