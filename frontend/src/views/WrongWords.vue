<template>
  <div class="wrong-page">
    <h1>错题本</h1>

    <div v-if="words.length === 0" class="empty">
      <p>🎉 没有错题，继续保持！</p>
      <router-link to="/">返回首页</router-link>
    </div>

    <template v-else>
      <div class="toolbar">
        <span class="count">共 {{ words.length }} 个错题</span>
        <button class="btn-danger" @click="clearAll">清空错题本</button>
      </div>

      <div class="wrong-list">
        <div v-for="w in words" :key="w.wrong_id" class="card wrong-item">
          <div class="wrong-content">
            <div class="wrong-word">
              <strong>{{ w.english }}</strong>
              <span class="wrong-chinese">{{ w.chinese }}</span>
              <span v-if="w.phonetic" class="wrong-phonetic">{{ w.phonetic }}</span>
            </div>
            <div class="wrong-path">
              {{ w.grade_name }} / {{ w.lesson_name }} / {{ w.section_name }}
            </div>
            <div class="wrong-meta">
              错误 {{ w.wrong_count }} 次 · {{ formatTime(w.last_wrong_at) }}
            </div>
          </div>
          <div class="wrong-actions">
            <button class="btn-ghost" @click="speak(w)">🔊</button>
            <button class="btn-success" @click="remove(w.wrong_id)">✓ 已掌握</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../api/index.js'

export default {
  name: 'WrongWords',
  setup() {
    const words = ref([])

    const load = async () => {
      words.value = await api.getWrongWords()
    }

    const remove = async (id) => {
      await api.removeWrongWord(id)
      await load()
    }

    const clearAll = async () => {
      if (!confirm('确定清空所有错题吗？')) return
      await api.clearWrongWords()
      await load()
    }

    const speak = (w) => {
      if (!window.speechSynthesis) return
      const utter = new SpeechSynthesisUtterance(w.english)
      utter.lang = 'en-US'
      utter.rate = 0.9
      speechSynthesis.speak(utter)
    }

    const formatTime = (t) => {
      if (!t) return ''
      return new Date(t).toLocaleString('zh-CN')
    }

    onMounted(load)

    return { words, remove, clearAll, speak, formatTime }
  }
}
</script>

<style scoped>
.wrong-page { max-width: 700px; margin: 0 auto; }
.wrong-page h1 { margin-bottom: 16px; }
.empty { text-align: center; padding: 60px 0; color: #999; }
.empty a { color: #4f46e5; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.count { color: #666; font-size: 14px; }
.wrong-list { display: flex; flex-direction: column; gap: 12px; }
.wrong-item { display: flex; justify-content: space-between; align-items: center; }
.wrong-content { flex: 1; }
.wrong-word { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; margin-bottom: 4px; }
.wrong-word strong { font-size: 18px; color: #333; }
.wrong-chinese { color: #666; }
.wrong-phonetic { color: #bbb; font-size: 13px; }
.wrong-path { font-size: 12px; color: #999; margin-bottom: 2px; }
.wrong-meta { font-size: 12px; color: #ccc; }
.wrong-actions { display: flex; gap: 8px; margin-left: 16px; }
</style>
