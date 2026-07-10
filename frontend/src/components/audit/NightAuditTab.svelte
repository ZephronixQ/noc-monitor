<script>
  import { fade } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { data, BACKEND_URL } from '../../stores/networkStore.js';
  import { formatLosTime } from '../../utils/helpers.js';
  
  import NightAuditCalendar from './NightAuditCalendar.svelte';
  import NightAuditEventsList from './NightAuditEventsList.svelte';

  export let isDark = false;
  export let currentUnixTime = Math.floor(Date.now() / 1000);

  let currentYear = 2026;
  let currentMonth = 6; // Июль
  let selectedDay = 10;
  let shiftFilter = 'night';

  const monthNames = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];

  let rawLocalHistory = [];
  try {
    rawLocalHistory = JSON.parse(localStorage.getItem('noc_global_incident_history') || '[]');
  } catch(e) {}

  // Принудительное очищение от любых остатков LOSi перед выводом
  $: localHistory = rawLocalHistory.filter(e => {
    const s = (e.state || '').toLowerCase();
    return s !== 'losi';
  });

  let previousStates = new Map();

  // Реактивный маппинг IP -> Папка (Локация) из БД
  $: swLocationMap = (() => {
    let map = new Map();
    const rawData = $data || [];
    const swNode = rawData.find(d => d.isSwitch);
    if (swNode && swNode.ports) {
      swNode.ports.forEach(folder => {
        if (folder.onus) {
          folder.onus.forEach(sw => {
            if (sw && sw.id) {
              map.set(sw.id, folder.name || 'Общие узлы');
            }
          });
        }
      });
    }
    return map;
  })();

  // Импортер истории из БД
  async function syncAllSwitchesHistory() {
    const rawData = $data || [];
    const swNode = rawData.find(d => d.isSwitch);
    if (!swNode || !swNode.ports) return;

    const allSwitches = swNode.ports.flatMap(p => p.onus || []);
    let updated = false;

    for (let i = 0; i < allSwitches.length; i++) {
      const sw = allSwitches[i];
      if (!sw || !sw.id) continue;

      const hasRecord = rawLocalHistory.some(h => h.id === sw.id);
      if (hasRecord) continue;

      try {
        const res = await fetch(`${BACKEND_URL}/api/history/${encodeURIComponent(sw.id)}?days=3`);
        if (res.ok) {
          const json = await res.json();
          const incidents = json.incidents || json.data || [];
          const locationName = swLocationMap.get(sw.id) || 'Общие узлы';

          incidents.forEach(inc => {
            const isDuplicate = rawLocalHistory.some(h => h.id === sw.id && h.start_time === inc.start_time);
            if (!isDuplicate) {
              rawLocalHistory = [...rawLocalHistory, {
                id: sw.id,
                contract: sw.contract || '—',
                type: 'sw',
                state: 'down',
                start_time: inc.start_time,
                end_time: inc.end_time || null,
                location: locationName
              }];
              updated = true;
            }
          });
        }
      } catch (e) {
        console.error('Ошибка импорта истории для:', sw.id, e);
      }

      if (i % 5 === 0) {
        await new Promise(r => setTimeout(r, 50));
      }
    }

    if (updated) {
      rawLocalHistory = Array.from(new Set(rawLocalHistory.map(JSON.stringify))).map(JSON.parse);
      localStorage.setItem('noc_global_incident_history', JSON.stringify(rawLocalHistory));
    }
  }

  // Регистратор событий (строго без учета LOSi)
  $: if ($data && $data.length > 0) {
    let updated = false;
    const now = Math.floor(Date.now() / 1000);

    const swNode = $data.find(d => d.isSwitch);
    if (swNode && swNode.ports) {
      swNode.ports.forEach(folder => {
        if (folder.onus) {
          folder.onus.forEach(sw => {
            if (sw && sw.id) {
              const state = (sw.state || '').trim().toLowerCase();
              const isDown = state !== 'working' && state !== 'host is alive';
              const prevState = previousStates.get(sw.id);

              if (isDown && (!prevState || prevState === 'working')) {
                const isDuplicate = rawLocalHistory.some(h => h.id === sw.id && h.start_time === (sw.los_time || now));
                if (!isDuplicate) {
                  rawLocalHistory = [...rawLocalHistory, {
                    id: sw.id,
                    contract: sw.contract || '—',
                    type: 'sw',
                    state: sw.state,
                    start_time: sw.los_time || now,
                    end_time: null
                  }];
                  updated = true;
                }
              } else if (!isDown && prevState && prevState !== 'working') {
                const lastInc = [...rawLocalHistory].reverse().find(i => i.id === sw.id && !i.end_time);
                if (lastInc) {
                  lastInc.end_time = now;
                  updated = true;
                }
              }
              previousStates.set(sw.id, isDown ? 'down' : 'working');
            }
          });
        }
      });
    }

    const olts = $data.filter(d => !d.isSwitch);
    olts.forEach(olt => {
      if (olt.ports) {
        olt.ports.forEach(port => {
          if (port.onus) {
            port.onus.forEach(onu => {
              if (onu && onu.id) {
                // ИСПРАВЛЕНО: Ключ пишется как IP:ONU_ID, так как onu.id уже содержит в себе имя платы
                const key = `${olt.ip}:${onu.id}`;
                const state = (onu.state || '').trim().toLowerCase();
                const isDown = ['los', 'down'].includes(state); // СТРОГО БЕЗ LOSi
                const prevState = previousStates.get(key);

                if (isDown && (!prevState || prevState === 'working')) {
                  const isDuplicate = rawLocalHistory.some(h => h.id === key && h.start_time === (onu.los_time || now));
                  if (!isDuplicate) {
                    rawLocalHistory = [...rawLocalHistory, {
                      id: key,
                      contract: onu.contract || '—',
                      type: 'onu',
                      state: onu.state,
                      start_time: onu.los_time || now,
                      end_time: null
                    }];
                    updated = true;
                  }
                } else if (!isDown && prevState && prevState !== 'working') {
                  const lastInc = [...rawLocalHistory].reverse().find(i => i.id === key && !i.end_time);
                  if (lastInc) {
                    lastInc.end_time = now;
                    updated = true;
                  }
                }
                previousStates.set(key, isDown ? state : 'working');
              }
            });
          }
        });
      }
    });

    if (updated) {
      rawLocalHistory = rawLocalHistory.slice(-2000);
      try {
        localStorage.setItem('noc_global_incident_history', JSON.stringify(rawLocalHistory));
      } catch(e) {}
    }
  }

  $: daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  $: startDayOfWeek = (() => {
    let day = new Date(currentYear, currentMonth, 1).getDay();
    return day === 0 ? 6 : day - 1;
  })();

  function isIncidentActiveInDay(start_time, end_time, day, mode, nowUnix) {
    if (!start_time) return false;

    let startLimit, endLimit;
    if (mode === 'night') {
      startLimit = new Date(currentYear, currentMonth, day, 17, 0, 0).getTime() / 1000;
      endLimit = new Date(currentYear, currentMonth, day + 1, 9, 0, 0).getTime() / 1000;
    } else {
      startLimit = new Date(currentYear, currentMonth, day, 0, 0, 0).getTime() / 1000;
      endLimit = new Date(currentYear, currentMonth, day, 23, 59, 59).getTime() / 1000;
    }

    if (startLimit > nowUnix) return false;

    const startDate = new Date(start_time * 1000);
    if (startDate.getFullYear() !== currentYear || startDate.getMonth() !== currentMonth) {
      if (end_time) {
        const endsBeforePeriod = end_time < startLimit;
        if (endsBeforePeriod) return false;
      }
    }

    const startedBeforeEnd = start_time < endLimit;
    const isStillActiveNow = !end_time;
    const activeInPeriod = isStillActiveNow 
      ? (start_time < endLimit && nowUnix >= startLimit) 
      : (end_time > startLimit);

    return startedBeforeEnd && activeInPeriod;
  }

  function clusterIncidents(events) {
    let groups = {};
    events.forEach(e => {
      if (!groups[e.id]) groups[e.id] = [];
      groups[e.id].push(e);
    });

    return Object.entries(groups).map(([id, list]) => {
      list.sort((a, b) => a.los_time - b.los_time);

      if (list.length === 1) {
        return { isCluster: false, ...list[0] };
      } else {
        const first = list[0];
        const last = list[list.length - 1];
        const totalDuration = list.reduce((sum, e) => sum + e.durationSec, 0);

        return {
          isCluster: true,
          id: first.id,
          contract: first.contract,
          type: first.type,
          timeStart: first.timeStart,
          timeEnd: last.timeEnd,
          durationSec: totalDuration,
          state: first.state,
          los_time: first.los_time,
          location: first.location,
          history: list.map(item => ({
            start: item.timeStart,
            end: item.timeEnd,
            duration: item.durationSec
          }))
        };
      }
    });
  }

  $: switchIncidents = localHistory.filter(event => 
    event.type === 'sw' && isIncidentActiveInDay(event.start_time, event.end_time, selectedDay, shiftFilter, currentUnixTime)
  ).map(e => ({
    id: e.id,
    contract: e.contract,
    timeStart: new Date(e.start_time * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
    timeEnd: e.end_time ? new Date(e.end_time * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : 'Активен',
    durationSec: e.end_time ? (e.end_time - e.start_time) : (currentUnixTime - e.start_time),
    state: e.state || 'DOWN',
    los_time: e.start_time,
    location: swLocationMap.get(e.id) || 'Общие узлы'
  }));

  $: gponHierarchy = (() => {
    let oltsMap = {};
    const gponEvents = localHistory.filter(event => 
      event.type === 'onu' && isIncidentActiveInDay(event.start_time, event.end_time, selectedDay, shiftFilter, currentUnixTime)
    );

    // Сортируем события по убыванию времени старта (сначала самые новые)
    gponEvents.sort((a, b) => b.start_time - a.start_time);

    gponEvents.forEach(e => {
      const parts = e.id.split(':');
      if (parts.length === 3) {
        const oltIp = parts[0];
        const portName = parts[1];
        const onuId = parts[2];

        if (!oltsMap[oltIp]) oltsMap[oltIp] = {};
        if (!oltsMap[oltIp][portName]) oltsMap[oltIp][portName] = [];

        // Проверяем, не была ли добавлена эта ONU ранее, отсекая дубликаты из-за частого флапинга
        const alreadyExists = oltsMap[oltIp][portName].some(o => o.id === onuId);
        if (!alreadyExists) {
          oltsMap[oltIp][portName].push({
            id: onuId,
            contract: e.contract,
            state: e.state || 'LOS',
            timeStart: new Date(e.start_time * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
            timeEnd: e.end_time ? new Date(e.end_time * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : 'Активен',
            durationSec: e.end_time ? (e.end_time - e.start_time) : (currentUnixTime - e.start_time),
            los_time: e.start_time
          });
        }
      }
    });

    return Object.entries(oltsMap).map(([oltIp, portsMap]) => {
      const ports = Object.entries(portsMap).map(([portName, onus]) => ({
        portName,
        onus
      }));
      return { oltIp, ports };
    });
  })();

  $: calendarDays = Array.from({ length: daysInMonth }, (_, i) => {
    const day = i + 1;
    const swCount = localHistory.filter(e => e.type === 'sw' && isIncidentActiveInDay(e.start_time, e.end_time, day, shiftFilter, currentUnixTime)).length;
    const gponCount = localHistory.filter(e => e.type === 'onu' && isIncidentActiveInDay(e.start_time, e.end_time, day, shiftFilter, currentUnixTime)).length;
    const totalCount = swCount + gponCount;

    return {
      day,
      hasProblem: totalCount > 0,
      count: totalCount
    };
  });

  onMount(() => {
    // ИСПРАВЛЕНО: Автоматический сборщик мусора вычищает из кэша все старые ошибочно сдублированные записи GPON с именами портов
    rawLocalHistory = rawLocalHistory.filter((item) => {
      if (item.type === 'onu') {
        const parts = item.id.split(':');
        if (parts.length > 3) return false; // удаляем кривые дубликаты
      }
      return true;
    });

    rawLocalHistory = rawLocalHistory.filter((item, index, self) =>
      index === self.findIndex(t => t.id === item.id && t.start_time === item.start_time)
    );
    localStorage.setItem('noc_global_incident_history', JSON.stringify(rawLocalHistory));

    syncAllSwitchesHistory();
  });
</script>

<div class="flex-1 flex gap-6 overflow-hidden min-h-0" in:fade>
  
  <NightAuditCalendar
    {isDark}
    {currentYear}
    {currentMonth}
    {selectedDay}
    {shiftFilter}
    {calendarDays}
    {startDayOfWeek}
    on:selectDay={(e) => selectedDay = e.detail}
    on:changeMonth={(e) => {
      currentMonth += e.detail;
      if (currentMonth < 0) {
        currentMonth = 11;
        currentYear -= 1;
      } else if (currentMonth > 11) {
        currentMonth = 0;
        currentYear += 1;
      }
      selectedDay = 1;
    }}
  />

  <NightAuditEventsList
    {isDark}
    {selectedDay}
    monthName={monthNames[currentMonth]}
    bind:shiftFilter
    {switchIncidents}
    {gponHierarchy}
    {currentUnixTime}
    on:openHistory
  />

</div>