<template>
  <div class="app">
    <nav class="nav">
      <router-link to="/" class="nav-brand">📚 小杰背单词</router-link>
      <div class="nav-links">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/records" class="nav-link">学习记录</router-link>
        <router-link to="/manage" class="nav-link">词库管理</router-link>
        <router-link to="/articles" class="nav-link">文章背诵</router-link>
        <router-link to="/word-forms" class="nav-link">词形变化</router-link>
        <router-link to="/wrong" class="nav-link">错题本</router-link>
      </div>
    </nav>
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">
      <span>v{{ version }}</span>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from './api/index.js'

export default {
  setup() {
    const version = ref('')
    onMounted(async () => {
      try {
        const data = await api.getVersion()
        version.value = data.version
      } catch {}
    })
    return { version }
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f0f4ff;
  color: #333;
  min-height: 100vh;
}
.app {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 16px;
}
.nav {
  display: flex;
  align-items: center;
  padding: 16px 0;
  border-bottom: 2px solid #e0e7ff;
  margin-bottom: 24px;
}
.nav-brand {
  font-size: 24px;
  font-weight: bold;
  color: #4f46e5;
  text-decoration: none;
  margin-right: 32px;
}
.nav-links { display: flex; gap: 16px; }
.nav-link {
  color: #666;
  text-decoration: none;
  font-size: 16px;
  padding: 4px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}
.nav-link:hover, .nav-link.router-link-active {
  background: #e0e7ff;
  color: #4f46e5;
}
.main { padding-bottom: 40px; }
button {
  cursor: pointer;
  border: none;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.2s;
}
button:hover { opacity: 0.85; }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-success { background: #22c55e; color: #fff; }
.btn-ghost { background: #f3f4f6; color: #666; }
.btn-ghost:hover { background: #e5e7eb; }
input, select {
  padding: 8px 12px;
  border: 2px solid #e0e7ff;
  border-radius: 8px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}
input:focus, select:focus { border-color: #4f46e5; }
.card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.footer {
  text-align: center; padding: 20px 0; font-size: 12px; color: #ccc;
  border-top: 1px solid #f3f4f6; margin-top: 20px;
}
</style>
