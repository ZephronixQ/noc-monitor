import { writable, derived } from 'svelte/store';

export const notifications = writable([]);
export const unreadCount = writable(0);
export const showNotifications = writable(false);

// Производный список уведомлений (закрепленные всегда сверху)
export const sortedNotifications = derived(notifications, ($notifications) => {
  return [...$notifications].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return b.time - a.time;
  });
});

export function sendPushNotification(title, body) {
  if (typeof window !== 'undefined' && "Notification" in window && Notification.permission === "granted") {
    const isCritical = title.includes("АВАРИЯ") || title.includes("ПАДЕНИЕ") || title.includes("УПАЛ");
    const options = {
      body,
      icon: '/favicon.ico',
      requireInteraction: isCritical,
      silent: false
    };
    const notification = new Notification(title, options);
    notification.onclick = function() {
      window.focus(); 
      this.close();   
    };
  }
}

export function addNotification(type, title, body) {
  const isMassOutage = title.includes('МАССОВАЯ');
  const id = Date.now() + Math.random(); 
  let timeoutId = null;

  if (isMassOutage) {
    timeoutId = setTimeout(() => {
      removeNotification(id);
    }, 10 * 60 * 1000);
  }

  const newNotif = { id, type, title, body, time: new Date(), pinned: isMassOutage, timeoutId };
  notifications.update(n => [newNotif, ...n].slice(0, 100));
  unreadCount.update(c => c + 1);
  sendPushNotification(title, body);
}

export function removeNotification(id) {
  notifications.update(list => list.filter(n => {
    if (n.id === id && n.timeoutId) clearTimeout(n.timeoutId);
    return n.id !== id;
  }));
}

export function clearAllNotifications() {
  notifications.update(list => {
    list.forEach(n => { if (n.timeoutId) clearTimeout(n.timeoutId); });
    return [];
  });
  unreadCount.set(0);
}

export function toggleNotifications() {
  showNotifications.update(s => {
    const next = !s;
    if (next) unreadCount.set(0);
    return next;
  });
}

// Внутреннее состояние для отслеживания изменений между опросами
let knownState = { massOlt: 0, massSw: 0, downSwitches: new Map(), downOnus: new Map() };
let isFirstLoad = true; 

export function analyzeDataChanges(newData) {
  let currentMassOlt = 0; 
  let currentMassSw = 0;
  let currentDownSwitches = new Map();
  let currentDownOnus = new Map();

  newData.forEach(d => {
    if (d.isSwitch) {
      d.ports.forEach(folder => {
        if (folder.is_mass_outage) currentMassSw++;
        folder.onus.forEach(sw => {
          const state = (sw.state || '').trim().toLowerCase();
          if (!['working', 'host is alive'].includes(state)) {
            currentDownSwitches.set(sw.id, sw.contract || '—');
          }
        });
      });
    } else {
      d.ports.forEach(port => {
        if (port.is_mass_outage) currentMassOlt++;
        port.onus.forEach(onu => {
          const state = (onu.state || '').trim().toLowerCase();
          if (['los', 'down', 'losi'].includes(state)) {
            currentDownOnus.set(`${d.ip}:${onu.id}`, { contract: onu.contract || '—', state: state });
          }
        });
      });
    }
  });

  if (!isFirstLoad) {
    if (currentMassOlt > knownState.massOlt) {
      addNotification('critical', 'МАССОВАЯ АВАРИЯ OLT', `Зафиксировано ${currentMassOlt} очагов GPON.`);
    }
    if (currentMassSw > knownState.massSw) {
      addNotification('critical', 'МАССОВАЯ АВАРИЯ SW', `Зафиксировано ${currentMassSw} локаций коммутаторов.`);
    }

    let newDownSw = []; let upSw = [];
    let newDownOnu = []; let upOnu = [];

    currentDownSwitches.forEach((contract, id) => { if (!knownState.downSwitches.has(id)) newDownSw.push(id); });
    knownState.downSwitches.forEach((contract, id) => { if (!currentDownSwitches.has(id)) upSw.push(id); });
    
    currentDownOnus.forEach((data, id) => { if (!knownState.downOnus.has(id)) newDownOnu.push({id, contract: data.contract, state: data.state}); });
    knownState.downOnus.forEach((data, id) => { if (!currentDownOnus.has(id)) upOnu.push({id, contract: data.contract}); });

    const SW_LIMIT = 5;  
    const ONU_LIMIT = 10; 

    if (newDownSw.length > SW_LIMIT) {
      addNotification('critical', `МАССОВОЕ ПАДЕНИЕ SW`, `Сразу ${newDownSw.length} коммутаторов недоступны.\nВозможно потеря SNMP пакетов или падение магистрали.`);
    } else {
      newDownSw.forEach(id => addNotification('critical', `УПАЛ КОММУТАТОР`, `🔌 IP-адрес: ${id}`));
    }

    if (upSw.length > SW_LIMIT) {
      addNotification('success', `МАССОВОЕ ВОССТАНОВЛЕНИЕ SW`, `Сразу ${upSw.length} коммутаторов вернулись в сеть.`);
    } else {
      upSw.forEach(id => addNotification('success', `КОММУТАТОР В СЕТИ`, `🔌 IP-адрес: ${id}`));
    }

    if (newDownOnu.length > ONU_LIMIT) {
      addNotification('warning', `МАССОВЫЙ ОТВАЛ (GPON)`, `Сразу ${newDownOnu.length} клиентов отвалились (LOS/LOSi).`);
    } else {
      newDownOnu.forEach(onu => {
        const p = onu.id.split(':');
        const route = p.length === 3 ? `[${p[0]}] ➔ [${p[1]}] ➔ ONU ${p[2]}` : onu.id;
        const statusName = onu.state.toUpperCase();
        addNotification('warning', `АВАРИЯ GPON (${statusName})`, `👤 Договор: ${onu.contract}\n🔌 Маршрут: ${route}`);
      });
    }

    if (upOnu.length > ONU_LIMIT) {
      addNotification('success', `МАССОВОЕ ВОССТАНОВЛЕНИЕ GPON`, `Сразу ${upOnu.length} клиентов вернулись в сеть.`);
    } else {
      upOnu.forEach(onu => {
        const p = onu.id.split(':');
        const route = p.length === 3 ? `[${p[0]}] ➔ [${p[1]}] ➔ ONU ${p[2]}` : onu.id;
        addNotification('success', `GPON КЛИЕНТ В СЕТИ`, `👤 Договор: ${onu.contract}\n🔌 Маршрут: ${route}`);
      });
    }
  }

  knownState.massOlt = currentMassOlt;
  knownState.massSw = currentMassSw;
  knownState.downSwitches = currentDownSwitches;
  knownState.downOnus = currentDownOnus;
  isFirstLoad = false;
}