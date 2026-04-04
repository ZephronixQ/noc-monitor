import { mount } from 'svelte';
import './app.css'; /* <--- ЭТО САМАЯ ВАЖНАЯ СТРОКА */
import App from './App.svelte';

const app = mount(App, {
  target: document.getElementById('app'),
});

export default app;
