// frontend/src/utils/security.js

export function initSecurityGuards() {
  if (typeof window === 'undefined') return;

  // 1. БЛОКИРОВКА КОНТЕКСТНОГО МЕНЮ (ПКМ)
  const blockContextMenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    return false;
  };
  window.addEventListener('contextmenu', blockContextMenu, true);
  document.addEventListener('contextmenu', blockContextMenu, true);

  // 2. БРОНЕБОЙНАЯ БЛОКИРОВКА ХОТКЕЕВ DEVTOOLS
  const blockKeys = (e) => {
    const key = (e.key || '').toLowerCase();
    const code = (e.code || '').toLowerCase();
    const keyCode = e.keyCode || e.which;

    // F12
    const isF12 = key === 'f12' || code === 'f12' || keyCode === 123;

    // Ctrl+Shift+I / J / C (Инспектор и Консоль)
    const isCtrlShiftInspector = (e.ctrlKey || e.metaKey) && e.shiftKey && (
      key === 'i' || code === 'keyi' || keyCode === 73 ||
      key === 'j' || code === 'keyj' || keyCode === 74 ||
      key === 'c' || code === 'keyc' || keyCode === 67 ||
      key === 'ш' || key === 'о' || key === 'с' // Русская раскладка!
    );

    // Ctrl+U (Просмотр исходного кода страницы)
    const isCtrlU = (e.ctrlKey || e.metaKey) && (
      key === 'u' || code === 'keyu' || keyCode === 85 ||
      key === 'г' // Русская раскладка!
    );

    // Ctrl+S (Сохранение страницы)
    const isCtrlS = (e.ctrlKey || e.metaKey) && (
      key === 's' || code === 'keys' || keyCode === 83 ||
      key === 'ы' // Русская раскладка!
    );

    // Ctrl+Shift+K (Консоль в Firefox)
    const isCtrlShiftFirefox = (e.ctrlKey || e.metaKey) && e.shiftKey && (
      key === 'k' || code === 'keyk' || keyCode === 75 ||
      key === 'л'
    );

    if (isF12 || isCtrlShiftInspector || isCtrlU || isCtrlS || isCtrlShiftFirefox) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      return false;
    }
  };

  // capture: true ПЕРЕХВАТЫВАЕТ СОБЫТИЕ ДО ВСЕХ ОСТАЛЬНЫХ СКРИПТОВ
  window.addEventListener('keydown', blockKeys, true);
  document.addEventListener('keydown', blockKeys, true);

  // 3. АГРЕССИВНЫЙ АНТИ-ОТЛАДЧИК (DEBUGGER LOOP)
  // Если DevTools открыли через меню браузера, страница намертво встает на паузу
  const antiDebugger = () => {
    function loop() {
      try {
        const start = performance.now();
        // Конструктор Function вызывает debugger, который невозможно обойти простым переопределением
        (function() {}.constructor("debugger")());
        const end = performance.now();
        // Если консоль открыта, вызов debugger занимает более 100мс
        if (end - start > 100) {
          // Принудительно очищаем страницу или вешаем в бесконечный freeze
          window.location.reload();
        }
      } catch (err) {}
      setTimeout(loop, 100);
    }
    loop();
  };

  // Запускаем анти-отладчик
  try {
    antiDebugger();
  } catch (e) {}

  // 4. ДЕТЕКТОР ОТКРЫТИЯ DEVTOOLS ПО ИЗМЕНЕНИЮ РАЗМЕРОВ ЭКРАНА
  let devtoolsOpen = false;
  const threshold = 160;

  const checkDevTools = () => {
    const widthThreshold = window.outerWidth - window.innerWidth > threshold;
    const heightThreshold = window.outerHeight - window.innerHeight > threshold;
    if (widthThreshold || heightThreshold) {
      if (!devtoolsOpen) {
        devtoolsOpen = true;
        // Если открыли инспектор сбоку или снизу
        console.clear();
      }
    } else {
      devtoolsOpen = false;
    }
  };

  window.addEventListener('resize', checkDevTools);
  setInterval(checkDevTools, 500);
}