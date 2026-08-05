// frontend/src/utils/security.js

export function initSecurityGuards() {
  if (typeof window === 'undefined') return;

  // 1. Блокировка правого клика (контекстного меню)
  document.addEventListener('contextmenu', (e) => e.preventDefault());

  // 2. Блокировка горячих клавиш F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U, Ctrl+S
  document.addEventListener('keydown', (e) => {
    if (
      e.key === 'F12' ||
      (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) ||
      (e.ctrlKey && (e.key === 'U' || e.key === 'u' || e.key === 'S' || e.key === 's'))
    ) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  });

  // 3. Защита через анти-отладчик (зависание DevTools при попытке открыть консоль)
  setInterval(() => {
    const startTime = performance.now();
    debugger; // Если DevTools открыты, выполнение встанет на паузу
    const endTime = performance.now();
    if (endTime - startTime > 100) {
      console.clear();
    }
  }, 1000);
}