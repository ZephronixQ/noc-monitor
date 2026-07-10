<!-- frontend\src\components\DashboardTab.svelte -->
<script>
  import { fade } from 'svelte/transition';
  import DashboardMetrics from './DashboardMetrics.svelte';
  import DashboardCrisisConsole from './DashboardCrisisConsole.svelte';

  export let isDark = false;
  export let dailyStats = { total_24h: 0, avg_repair_minutes: 0, active_now: 0 };
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0, massOlt: 0, massSw: 0 };

  // Оставляем пустые экспорты для 100% совместимости с App.svelte
  export let historyLabels = [];
  export let historyData = [];
</script>

<div class="flex flex-col gap-6 h-full min-h-0 z-10 relative" in:fade>
  
  <!-- Модуль 1: Четыре верхние Bento-карточки со встроенными кольцами здоровья и "Критическим фокусом" -->
  <DashboardMetrics {isDark} {dailyStats} {totalStats} />

  <!-- Модуль 2: Сплит-консоль иерархических критических инцидентов и аномалий -->
  <DashboardCrisisConsole {isDark} {totalStats} />

</div>