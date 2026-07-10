<!-- frontend\src\components\DashboardChart.svelte -->
<svelte:head>
  <script src="https://cdn.jsdelivr.net/npm/chart.js" on:load={handleChartLoaded}></script>
</svelte:head>

<script>
  import { onMount, onDestroy } from 'svelte';

  export let isDark = false;
  export let historyLabels = [];
  export let historyData = [];

  let chartCanvas;
  let chartInstance = null;
  let scriptLoaded = false;

  function handleChartLoaded() {
    scriptLoaded = true;
    initChart();
  }

  $: if (scriptLoaded && isDark !== undefined) {
    initChart();
  }

  $: if (chartInstance && (historyLabels || historyData)) {
    redrawChart();
  }

  onMount(() => {
    if (window.Chart) {
      scriptLoaded = true;
      initChart();
    }
  });

  onDestroy(() => {
    if (chartInstance) {
      chartInstance.destroy();
    }
  });

  function initChart() {
    if (!chartCanvas || !window.Chart) return;
    
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }

    const dark = isDark;
    const gridColor = dark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(15, 23, 42, 0.04)';
    const textColor = dark ? '#64748b' : '#94a3b8';
    const lineColor = dark ? '#6366f1' : '#4f46e5';

    let gradient = 'rgba(99, 102, 241, 0)';
    try {
      const ctx = chartCanvas.getContext('2d');
      if (ctx) {
        gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, dark ? 'rgba(99, 102, 241, 0.2)' : 'rgba(79, 70, 229, 0.08)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
      }
    } catch (e) {
      console.error("Ошибка генерации градиента:", e);
    }

    try {
      chartInstance = new window.Chart(chartCanvas, {
        type: 'line',
        data: { 
          labels: historyLabels || [], 
          datasets: [{ 
            label: 'Потери', 
            data: historyData || [], 
            fill: true, 
            tension: 0.35, 
            borderWidth: 2.5, 
            borderColor: lineColor,
            backgroundColor: gradient,
            pointRadius: 1,
            pointHitRadius: 15,
            pointHoverRadius: 6,
            pointHoverBorderWidth: 3,
            pointBackgroundColor: dark ? '#161f33' : '#ffffff',
            pointHoverBorderColor: lineColor
          }] 
        },
        options: { 
          responsive: true, 
          maintainAspectRatio: false, 
          animation: { duration: 200 }, 
          plugins: { 
            legend: { display: false }, 
            tooltip: { 
              backgroundColor: dark ? '#1e293b' : '#ffffff',
              titleColor: dark ? '#94a3b8' : '#334155',
              bodyColor: dark ? '#f8fafc' : '#0f172a',
              borderColor: dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)',
              borderWidth: 1,
              padding: 12,
              cornerRadius: 12,
              titleFont: { size: 11, weight: '600' },
              bodyFont: { size: 13, weight: 'bold' },
              displayColors: false,
              mode: 'index', 
              intersect: false 
            } 
          }, 
          scales: {
            x: { 
              grid: { display: false },
              ticks: { color: textColor, font: { size: 10 } }
            },
            y: { 
              beginAtZero: true, 
              suggestedMin: 0,
              grid: { color: gridColor },
              ticks: { color: textColor, font: { size: 10 } }
            }
          },
          interaction: { mode: 'nearest', axis: 'x', intersect: false } 
        }
      });
    } catch (e) {
      print(e);
    }
  }

  function redrawChart() {
    if (chartInstance) {
      chartInstance.data.labels = historyLabels || [];
      chartInstance.data.datasets[0].data = historyData || [];
      chartInstance.update('none');
    }
  }
</script>

<div class="flex-1 p-6 min-h-0 rounded-[24px] border shadow-sm flex flex-col relative 
  {isDark 
    ? 'bg-[#161f33] border border-slate-800 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.25)]' 
    : 'bg-white border border-slate-200/60 shadow-[0_12px_30px_-5px_rgba(0,0,0,0.02)]'}"
>
  <div class="flex items-center justify-between mb-2">
    <div class="flex items-center gap-2">
      <span class="w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
      <span class="text-[10px] font-black text-slate-400 dark:text-slate-400 uppercase tracking-wider">Динамика потерь (LOS+LOSi)</span>
    </div>
  </div>
  <div class="flex-1 w-full relative min-h-[200px]">
    <canvas bind:this={chartCanvas} class="absolute inset-0 w-full h-full"></canvas>
  </div>
</div>