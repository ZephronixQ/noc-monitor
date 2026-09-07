<!-- frontend/src/components/dashboard/DashboardAnomalies.svelte -->
<script>
  import { data } from '../../stores/networkStore.js';

  export let isDark = false;
  export let totalStats = { onus: 0, online: 0, los: 0, losi: 0, swUp: 0, switches: 0 };

  $: onusCount = totalStats?.onus || 0;
  $: onlineCount = totalStats?.online || 0;
  $: switchesCount = totalStats?.switches || 0;
  $: swUpCount = totalStats?.swUp || 0;

  $: gponHealth = onusCount > 0 ? (onlineCount / onusCount) * 100 : 100;
  $: swHealth = switchesCount > 0 ? (swUpCount / switchesCount) * 100 : 100;
  $: downSwitches = switchesCount - swUpCount;
  $: offlineOnus = Math.max(0, onusCount - onlineCount);

  // Длина окружности (R = 64) -> 2 * PI * 64 = 402.12
  const C = 402.12;

  $: segments = (() => {
    const total = onusCount > 0 ? onusCount : 1;
    
    // Пропорциональные длины дуг
    const lenOnline = (onlineCount / total) * C;
    const lenDying = (gponStats.dying / total) * C;
    const lenLos = (gponStats.los / total) * C;
    const lenLosi = (gponStats.losi / total) * C;
    const lenOffline = (gponStats.offline / total) * C;

    // Смещения по часовой стрелке
    const offsetOnline = 0;
    const offsetDying = -lenOnline;
    const offsetLos = -(lenOnline + lenDying);
    const offsetLosi = -(lenOnline + lenDying + lenLos);
    const offsetOffline = -(lenOnline + lenDying + lenLos + lenLosi);

    return {
      lenOnline, offsetOnline,
      lenDying, offsetDying,
      lenLos, offsetLos,
      lenLosi, offsetLosi,
      lenOffline, offsetOffline
    };
  })();

  // 1. СТАТИСТИКА GPON СИГНАЛОВ
  $: gponStats = (() => {
    let los = 0;
    let losi = 0;
    let dying = 0;
    let offline = 0;

    const rawData = $data || [];

    rawData.filter(d => !d.isSwitch).forEach(olt => {
      olt?.ports?.forEach(port => {
        port?.onus?.forEach(onu => {
          if (!onu) return;
          const state = (onu.state || '').trim().toLowerCase();
          if (state === 'dyinggasp') dying++;
          else if (state === 'offline') offline++;
          else if (state === 'losi') losi++;
          else if (['los', 'down'].includes(state)) los++;
        });
      });
    });

    const total = los + losi + dying + offline;
    return { los, losi, dying, offline, total };
  })();
</script>

<div class="col-span-3 p-3.5 rounded-2xl border transition-all duration-300 flex flex-col justify-between relative overflow-hidden font-sans h-full min-h-0
  {isDark 
    ? 'bg-[#1e2a3e] border-slate-700/70 text-slate-200 shadow-xl' 
    : 'bg-white border-slate-200/90 text-slate-800 shadow-sm'}"
>
  <!-- ШАПКА ПАНЕЛИ -->
  <div class="px-3.5 py-2.5 border-b {isDark ? 'border-slate-700/70 bg-[#24334a]/60 -mx-3.5 -mt-3.5 mb-3' : 'border-slate-100 bg-slate-50/80 -mx-3.5 -mt-3.5 mb-3'} flex items-center justify-between select-none shrink-0">
    <div class="flex items-center gap-2">
      <span class="text-sm">📊</span>
      <h2 class="text-xs font-bold uppercase font-mono tracking-wider {isDark ? 'text-slate-100' : 'text-slate-900'}">
        Телеметрия & Метрики
      </h2>
    </div>
    <span class="text-[9px] font-mono px-2 py-0.5 rounded-md font-bold tracking-wide
      {isDark ? 'bg-[#293a52] text-slate-300 border border-slate-600/60' : 'bg-slate-200/70 text-slate-700 border border-slate-300'}">
      GPON + L2
    </span>
  </div>

  <div class="flex-1 flex flex-col justify-between min-h-0 gap-3">
    
    <!-- ================= КАРТОЧКА 1: GPON ФЛОТ С ВЫРАЗИТЕЛЬНЫМ СПИДОМЕТРОМ ================= -->
    <div class="p-4 rounded-xl border flex flex-col justify-between flex-1 min-h-0 transition-colors
      {isDark ? 'bg-[#223046]/70 border-slate-700/60' : 'bg-slate-50/90 border-slate-200/90 shadow-2xs'}">
      
      <!-- ВЕРХ: ЗАГОЛОВОК И ЕМКОСТЬ -->
      <div class="flex items-center justify-between shrink-0">
        <div class="flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wide {isDark ? 'text-indigo-400' : 'text-indigo-700'}">
          <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-indigo-400' : 'bg-indigo-600'}"></span>
          <span>GPON Флот</span>
        </div>
        <div class="text-[10px] font-mono {isDark ? 'text-slate-400' : 'text-slate-600'}">
          Зарегистрировано: <span class="font-bold {isDark ? 'text-slate-200' : 'text-slate-900'}">{onusCount}</span> ONU
        </div>
      </div>

      <!-- ЦЕНТР: БОЛЬШОЙ МУЛЬТИ-СЕГМЕНТНЫЙ DONUT-СПИДОМЕТР -->
      <div class="flex items-center justify-between my-auto py-2 shrink-0 px-1">
        
        <!-- ЛЕВЫЙ БЛОК: ОНЛАЙН -->
        <div class="flex flex-col text-left font-mono min-w-[70px]">
          <span class="text-[9px] font-bold {isDark ? 'text-emerald-400' : 'text-emerald-700'} uppercase tracking-wider flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-emerald-400' : 'bg-emerald-600'}"></span> ОНЛАЙН
          </span>
          <span class="text-2xl font-black {isDark ? 'text-white' : 'text-slate-900'} tabular-nums mt-1">{onlineCount}</span>
          <span class="text-[10px] {isDark ? 'text-slate-400' : 'text-slate-600'} font-semibold">{gponHealth.toFixed(1)}% базы</span>
        </div>

        <!-- КРУГОВОЙ ДАТЧИК -->
        <div class="relative w-38 h-38 flex items-center justify-center shrink-0">
          <svg class="w-full h-full transform -rotate-90" viewBox="0 0 150 150">
            
            <!-- БАЗОВОЕ ФОНОВОЕ КОЛЬЦО -->
            <circle cx="75" cy="75" r="64" 
              stroke={isDark ? "rgba(255,255,255,0.06)" : "#e2e8f0"} 
              stroke-width="12" 
              fill="none" 
            />
            
            <!-- 1. ЗЕЛЕНЫЙ СЕГМЕНТ: ОНЛАЙН -->
            <circle cx="75" cy="75" r="64" 
              stroke={isDark ? "#10b981" : "#059669"} 
              stroke-width="12" 
              fill="none"
              stroke-dasharray="{segments.lenOnline} {C}"
              stroke-dashoffset="{segments.offsetOnline}"
              class="transition-all duration-700 ease-out"
            />

            <!-- 2. ЖЕЛТЫЙ СЕГМЕНТ: DYINGGASP (СВЕТ/ПИТАНИЕ) -->
            {#if gponStats.dying > 0}
              <circle cx="75" cy="75" r="64" 
                stroke={isDark ? "#f59e0b" : "#d97706"} 
                stroke-width="12" 
                fill="none"
                stroke-dasharray="{segments.lenDying} {C}"
                stroke-dashoffset="{segments.offsetDying}"
                class="transition-all duration-700 ease-out"
              />
            {/if}

            <!-- 3. КРАСНЫЙ СЕГМЕНТ: LOS (ОБРЫВ) -->
            {#if gponStats.los > 0}
              <circle cx="75" cy="75" r="64" 
                stroke={isDark ? "#f43f5e" : "#e11d48"} 
                stroke-width="12" 
                fill="none"
                stroke-dasharray="{segments.lenLos} {C}"
                stroke-dashoffset="{segments.offsetLos}"
                class="transition-all duration-700 ease-out"
              />
            {/if}

            <!-- 4. ФИОЛЕТОВЫЙ СЕГМЕНТ: LOSi (ЗАТУХАНИЕ) -->
            {#if gponStats.losi > 0}
              <circle cx="75" cy="75" r="64" 
                stroke={isDark ? "#c084fc" : "#9333ea"} 
                stroke-width="12" 
                fill="none"
                stroke-dasharray="{segments.lenLosi} {C}"
                stroke-dashoffset="{segments.offsetLosi}"
                class="transition-all duration-700 ease-out"
              />
            {/if}

            <!-- 5. СЕРЫЙ СЕГМЕНТ: OFFLINE (ПЛАН) -->
            {#if gponStats.offline > 0}
              <circle cx="75" cy="75" r="64" 
                stroke={isDark ? "#64748b" : "#94a3b8"} 
                stroke-width="12" 
                fill="none"
                stroke-dasharray="{segments.lenOffline} {C}"
                stroke-dashoffset="{segments.offsetOffline}"
                class="transition-all duration-700 ease-out"
              />
            {/if}
          </svg>

          <!-- ЦЕНТР ДАТЧИКА -->
          <div class="absolute inset-0 flex flex-col items-center justify-center leading-none text-center select-none font-mono">
            <span class="text-3xl font-black tracking-tight {isDark ? 'text-white' : 'text-slate-900'}">
              {gponHealth.toFixed(1)}%<span class="text-sm font-bold {isDark ? 'text-slate-400' : 'text-slate-600'}"></span>
            </span>
            <span class="text-[9px] font-bold mt-1.5 {isDark ? 'text-slate-400' : 'text-slate-600'} uppercase tracking-wider">
              HEALTH
            </span>
          </div>
        </div>

        <!-- ПРАВЫЙ БЛОК: ОФФЛАЙН -->
        <div class="flex flex-col text-right font-mono min-w-[70px]">
          <span class="text-[9px] font-bold {isDark ? 'text-rose-400' : 'text-rose-700'} uppercase tracking-wider flex items-center justify-end gap-1">
            ОФФЛАЙН <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-rose-500' : 'bg-rose-600'}"></span>
          </span>
          <span class="text-2xl font-black {isDark ? 'text-white' : 'text-slate-900'} tabular-nums mt-1">{offlineOnus}</span>
          <span class="text-[10px] {isDark ? 'text-slate-400' : 'text-slate-600'} font-semibold">{(100 - gponHealth).toFixed(1)}% потерь</span>
        </div>
      </div>

      <!-- НИЖНЯЯ ЧАСТЬ: СПЕКТР-БАР И ПЛИТКИ С ВЫСОКИМ КОНТРАСТОМ -->
      <div class="shrink-0 space-y-2.5">
        
        <!-- СПЕКТР-БАР -->
        <div>
          <div class="flex justify-between text-[10px] font-mono {isDark ? 'text-slate-300' : 'text-slate-700'} mb-1.5 font-semibold">
            <span>Спектр аномалий</span>
            <span>Всего: <b class="{isDark ? 'text-slate-100' : 'text-slate-900'} font-bold">{gponStats.total}</b> шт</span>
          </div>
          <div class="h-2 rounded-full overflow-hidden flex {isDark ? 'bg-slate-700/40 border-slate-700/60' : 'bg-slate-200 border-slate-300'} gap-0.5 p-0.5 border">
            {#if gponStats.total === 0}
              <div class="h-full w-full rounded-full bg-emerald-500"></div>
            {:else}
              {#if gponStats.los > 0}
                <div class="h-full rounded-full bg-rose-500" style="width: {(gponStats.los / gponStats.total) * 100}%" title="LOS: {gponStats.los}"></div>
              {/if}
              {#if gponStats.losi > 0}
                <div class="h-full rounded-full bg-purple-500" style="width: {(gponStats.losi / gponStats.total) * 100}%" title="LOSi: {gponStats.losi}"></div>
              {/if}
              {#if gponStats.dying > 0}
                <div class="h-full rounded-full bg-amber-500" style="width: {(gponStats.dying / gponStats.total) * 100}%" title="DyingGasp: {gponStats.dying}"></div>
              {/if}
              {#if gponStats.offline > 0}
                <div class="h-full rounded-full bg-slate-500" style="width: {(gponStats.offline / gponStats.total) * 100}%" title="Offline: {gponStats.offline}"></div>
              {/if}
            {/if}
          </div>
        </div>

        <!-- 4 ПЛИТКИ АНОМАЛИЙ (ЧЕТКИЙ КОНТУР И ТЕКСТ В ОБЕИХ ТЕМАХ) -->
        <div class="grid grid-cols-2 gap-2 font-mono">
          
          <!-- LOS -->
          <div class="p-2.5 rounded-xl border flex items-center justify-between {isDark ? 'bg-[#1b2638] border-slate-700/60' : 'bg-white border-slate-200 shadow-2xs'}">
            <div class="flex items-center gap-1.5 min-w-0 pr-1">
              <span class="w-2 h-2 rounded-full bg-rose-500 shrink-0"></span>
              <span class="text-[10px] {isDark ? 'text-rose-400' : 'text-rose-700'} font-bold truncate">LOS (Обрыв)</span>
            </div>
            <span class="text-xs font-black tabular-nums {isDark ? 'text-slate-100' : 'text-slate-900'}">{gponStats.los}</span>
          </div>

          <!-- LOSi -->
          <div class="p-2.5 rounded-xl border flex items-center justify-between {isDark ? 'bg-[#1b2638] border-slate-700/60' : 'bg-white border-slate-200 shadow-2xs'}">
            <div class="flex items-center gap-1.5 min-w-0 pr-1">
              <span class="w-2 h-2 rounded-full bg-purple-500 shrink-0"></span>
              <span class="text-[10px] {isDark ? 'text-purple-300' : 'text-purple-700'} font-bold truncate">LOSi (Изгиб)</span>
            </div>
            <span class="text-xs font-black tabular-nums {isDark ? 'text-slate-100' : 'text-slate-900'}">{gponStats.losi}</span>
          </div>

          <!-- DyingGasp -->
          <div class="p-2.5 rounded-xl border flex items-center justify-between {isDark ? 'bg-[#1b2638] border-slate-700/60' : 'bg-white border-slate-200 shadow-2xs'}">
            <div class="flex items-center gap-1.5 min-w-0 pr-1">
              <span class="w-2 h-2 rounded-full bg-amber-500 shrink-0"></span>
              <span class="text-[10px] {isDark ? 'text-amber-300' : 'text-amber-700'} font-bold truncate">DyingGasp (Свет)</span>
            </div>
            <span class="text-xs font-black tabular-nums {isDark ? 'text-slate-100' : 'text-slate-900'}">{gponStats.dying}</span>
          </div>

          <!-- Offline -->
          <div class="p-2.5 rounded-xl border flex items-center justify-between {isDark ? 'bg-[#1b2638] border-slate-700/60' : 'bg-white border-slate-200 shadow-2xs'}">
            <div class="flex items-center gap-1.5 min-w-0 pr-1">
              <span class="w-2 h-2 rounded-full bg-slate-500 shrink-0"></span>
              <span class="text-[10px] {isDark ? 'text-slate-400' : 'text-slate-600'} font-bold truncate">Offline (План)</span>
            </div>
            <span class="text-xs font-black tabular-nums {isDark ? 'text-slate-100' : 'text-slate-900'}">{gponStats.offline}</span>
          </div>

        </div>

      </div>

    </div>

    <!-- ================= КАРТОЧКА 2: МАГИСТРАЛЬНЫЕ КОММУТАТОРЫ (L2/L3) ================= -->
    <div class="p-3.5 rounded-xl border flex items-center justify-between transition-colors shrink-0
      {isDark ? 'bg-[#223046]/70 border-slate-700/60' : 'bg-slate-50/90 border-slate-200/90 shadow-2xs'}">
      
      <div class="min-w-0 pr-2">
        <div class="flex items-center gap-1.5 font-mono text-[10px] font-bold uppercase tracking-wide {isDark ? 'text-cyan-400' : 'text-cyan-700'}">
          <span class="w-1.5 h-1.5 rounded-full {isDark ? 'bg-cyan-400' : 'bg-cyan-600'}"></span>
          <span>Магистрали & SW</span>
        </div>

        <div class="flex items-baseline gap-1.5 mt-1 font-mono">
          <span class="text-xl font-black {isDark ? 'text-white' : 'text-slate-900'}">
            {swUpCount}
          </span>
          <span class="text-xs font-semibold {isDark ? 'text-slate-400' : 'text-slate-600'}">/ {switchesCount} узлов</span>
        </div>
      </div>

      <!-- СТАТУС-ЧИП DOWN / OK С ЧЕТКИМ КОНТРАСТОМ -->
      <div class="flex items-center gap-2 shrink-0">
        {#if downSwitches > 0}
          <div class="px-2.5 py-1 rounded-lg font-mono text-xs font-bold flex items-center gap-1.5
            {isDark 
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
              : 'bg-rose-100 text-rose-800 border border-rose-300 shadow-2xs'}">
            <span class="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse"></span>
            <span>{downSwitches} DOWN</span>
          </div>
        {:else}
          <div class="px-2.5 py-1 rounded-lg font-mono text-xs font-bold flex items-center gap-1.5
            {isDark 
              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' 
              : 'bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs'}">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            <span>ВСЕ В СЕТИ</span>
          </div>
        {/if}

        <div class="px-2 py-1 rounded-lg font-mono text-xs font-bold border 
          {isDark ? 'bg-[#1b2638] border-slate-700/60 text-slate-300' : 'bg-white border-slate-300 text-slate-800 shadow-2xs'}">
          {swHealth.toFixed(1)}%
        </div>
      </div>

    </div>

  </div>
</div>