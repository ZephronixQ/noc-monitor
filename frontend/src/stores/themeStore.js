import { writable } from 'svelte/store';

const storedTheme = localStorage.getItem('noc-theme');
const initialTheme = storedTheme 
  ? storedTheme === 'dark' 
  : (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches);

export const isDark = writable(initialTheme);

isDark.subscribe(value => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('noc-theme', value ? 'dark' : 'light');
  }
});

export function toggleTheme() {
  isDark.update(d => !d);
}