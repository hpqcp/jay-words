<template>
  <div class="records-page">
    <h1>学习记录</h1>

    <div v-if="!stats" class="empty"><p>加载中...</p></div>

    <template v-else>
      <div class="summary-cards">
        <div class="card summary-card">
          <div class="summary-num">{{ stats.streak }}</div>
          <div class="summary-label">连续学习天数</div>
        </div>
        <div class="card summary-card">
          <div class="summary-num">{{ stats.total_count }}</div>
          <div class="summary-label">总学习次数</div>
        </div>
        <div class="card summary-card">
          <div class="summary-num">{{ totalAccuracy }}%</div>
          <div class="summary-label">总正确率</div>
        </div>
        <div class="card summary-card">
          <div class="summary-num">{{ stats.today_count }}</div>
          <div class="summary-label">今日学习</div>
        </div>
      </div>

      <div class="card">
        <h2>今日统计</h2>
        <div class="today-bar">
          <div class="bar-segment correct" :style="{ flex: stats.today_correct }"></div>
          <div class="bar-segment wrong" :style="{ flex: stats.today_wrong || 0.1 }"></div>
        </div>
        <div class="bar-labels">
          <span>✅ 正确 {{ stats.today_correct }}</span>
          <span>❌ 错误 {{ stats.today_wrong }}</span>
        </div>
      </div>

      <div class="card">
        <h2>近两周学习趋势</h2>
        <div class="chart">
          <div v-for="d in stats.daily" :key="d.date" class="chart-col" :title="d.date">
            <div class="chart-bar-wrap">
              <div class="chart-bar correct" :style="{ height: barHeight(d.count) }"></div>
            </div>
            <div class="chart-label">{{ d.date.slice(5) }}</div>
          </div>
        </div>
      </div>

      <div class="card" v-if="stats.modes && stats.modes.length > 0">
        <h2>各模式统计</h2>
        <div class="mode-list">
          <div v-for="m in stats.modes" :key="m.mode" class="mode-row">
            <span class="mode-name">{{ modeLabel(m.mode) }}</span>
            <span class="mode-count">{{ m.count }} 次</span>
            <span class="mode-accuracy">{{ m.correct > 0 ? Math.round(m.correct / m.count * 100) : 0 }}%</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/index.js'

export default {
  name: 'LearningRecords',
  setup() {
    const stats = ref(null)

    const load = async () => {
      stats.value = await api.getStats()
    }

    const totalAccuracy = computed(() => {
      if (!stats.value || stats.value.total_count === 0) return 0
      return Math.round(stats.value.total_correct / stats.value.total_count * 100)
    })

    const maxCount = computed(() => {
      if (!stats.value) return 1
      return Math.max(...stats.value.daily.map(d => d.count), 1)
    })

    const barHeight = (count) => {
      const pct = count / maxCount.value * 100
      return Math.max(pct, count > 0 ? 8 : 0) + '%'
    }

    const modeLabel = (mode) => {
      const map = { flashcard: '翻卡片', quiz: '拼写测验', completion: '补全单词', choice: '选择正确' }
      return map[mode] || mode
    }

    onMounted(load)

    return { stats, totalAccuracy, maxCount, barHeight, modeLabel }
  }
}
</script>

<style scoped>
.records-page { max-width: 700px; margin: 0 auto; }
.records-page h1 { margin-bottom: 20px; }
.empty { text-align: center; padding: 40px; color: #999; }
.summary-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.summary-card { text-align: center; padding: 20px; }
.summary-num { font-size: 32px; font-weight: bold; color: #4f46e5; }
.summary-label { font-size: 13px; color: #888; margin-top: 4px; }
.card h2 { font-size: 16px; color: #666; margin-bottom: 16px; }
.today-bar { display: flex; height: 24px; border-radius: 12px; overflow: hidden; background: #f3f4f6; }
.bar-segment { transition: flex 0.3s; }
.bar-segment.correct { background: #22c55e; }
.bar-segment.wrong { background: #ef4444; }
.bar-labels { display: flex; justify-content: space-between; font-size: 13px; color: #888; margin-top: 8px; }
.chart { display: flex; gap: 4px; align-items: flex-end; height: 120px; }
.chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.chart-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.chart-bar { width: 60%; border-radius: 4px 4px 0 0; transition: height 0.3s; min-height: 2px; }
.chart-bar.correct { background: #4f46e5; }
.chart-label { font-size: 10px; color: #999; transform: rotate(-30deg); white-space: nowrap; }
.mode-list { display: flex; flex-direction: column; gap: 8px; }
.mode-row { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }
.mode-row:last-child { border-bottom: none; }
.mode-name { flex: 1; font-weight: 600; color: #333; }
.mode-count { color: #888; margin-right: 16px; }
.mode-accuracy { color: #4f46e5; font-weight: 600; min-width: 40px; text-align: right; }
</style>
