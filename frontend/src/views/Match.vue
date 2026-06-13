<template>
  <div class="match-page">
    <div v-if="words.length === 0" class="empty">
      <p>该章节暂无单词</p>
      <router-link to="/">返回首页</router-link>
    </div>
    <template v-else>
      <div class="progress-info">
        <span>{{ currentRound + 1 }} / {{ totalRounds }} 组</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: ((currentRound + 1) / totalRounds * 100) + '%' }"></div>
        </div>
      </div>

      <div v-if="isComplete" class="card result-card">
        <h2>🎉 全部完成！</h2>
        <p class="result-text">共 {{ words.length }} 词</p>
        <div class="result-actions">
          <button class="btn-primary" @click="restart">重新学习</button>
          <router-link to="/" class="btn-ghost" style="padding:8px 20px;border-radius:8px;text-decoration:none">返回首页</router-link>
        </div>
      </div>

      <template v-else>
        <div class="word-label">第 {{ currentRound + 1 }}/{{ totalRounds }} 组 · 将单词与中文连线</div>

        <div class="match-area" ref="matchAreaRef">
          <svg class="line-svg" ref="svgRef">
            <line v-for="(l, i) in lines" :key="i"
              :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2" />
          </svg>

          <div class="column left">
            <div
              v-for="(w, i) in roundWords" :key="'e'+i"
              class="match-item eng-item"
              :class="itemEngClass(i)"
              :data-ei="i"
              @click="selectEnglish(i)"
            >
              <span class="item-num">{{ i + 1 }}</span>
              {{ w.english }}
            </div>
          </div>

          <div class="column right">
            <div
              v-for="(ch, i) in shuffledChinese" :key="'c'+i"
              class="match-item chn-item"
              :class="itemChnClass(i)"
              :data-ci="i"
              @click="selectChinese(i)"
            >
              {{ ch }}
            </div>
          </div>
        </div>

        <div v-if="allMatched" class="next-round">
          <button class="btn-primary" @click="nextRound">下一组 →</button>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

const PER_ROUND = 10

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export default {
  name: 'Match',
  setup() {
    const route = useRoute()
    const words = ref([])
    const currentRound = ref(0)
    const roundWords = ref([])
    const shuffledChinese = ref([])
    const selectedEng = ref(-1)
    const matches = ref({})
    const wrongFlash = ref(null)
    const lines = ref([])
    const matchAreaRef = ref(null)
    const svgRef = ref(null)

    const totalRounds = computed(() => Math.ceil(words.value.length / PER_ROUND))
    const isComplete = ref(false)

    const matchedEngSet = computed(() => new Set(Object.keys(matches.value).map(Number)))
    const matchedChnSet = computed(() => new Set(Object.values(matches.value)))
    const allMatched = computed(() => roundWords.value.length > 0 && matchedEngSet.value.size === roundWords.value.length)

    const loadWords = async () => {
      const sectionId = parseInt(route.query.sectionId)
      if (!sectionId) return
      words.value = await api.getSectionWords(sectionId)
      currentRound.value = 0
      isComplete.value = false
      lines.value = []
      setupRound()
    }

    const setupRound = () => {
      const start = currentRound.value * PER_ROUND
      const chunk = words.value.slice(start, start + PER_ROUND)
      roundWords.value = chunk.length > 0 ? shuffle(chunk) : []
      shuffledChinese.value = chunk.length > 0 ? shuffle(chunk.map(w => w.chinese)) : []
      selectedEng.value = -1
      matches.value = {}
      wrongFlash.value = null
      lines.value = []
    }

    const selectEnglish = (ei) => {
      if (matchedEngSet.value.has(ei) || allMatched.value) return
      selectedEng.value = selectedEng.value === ei ? -1 : ei
    }

    const selectChinese = async (ci) => {
      if (matchedChnSet.value.has(ci) || allMatched.value) return
      if (selectedEng.value === -1) return

      const word = roundWords.value[selectedEng.value]
      const isCorrect = shuffledChinese.value[ci] === word.chinese

      if (isCorrect) {
        matches.value = { ...matches.value, [selectedEng.value]: ci }
        selectedEng.value = -1
        await api.submitRecord(word.id, 'match', 1)
        nextTick(() => drawLines())
        if (allMatched.value) {
          // already matched, show next button
        }
      } else {
        wrongFlash.value = { ei: selectedEng.value, ci }
        await api.submitRecord(word.id, 'match', 0)
        setTimeout(() => {
          wrongFlash.value = null
          selectedEng.value = -1
        }, 600)
      }
    }

    const drawLines = () => {
      const area = matchAreaRef.value
      if (!area) return
      const areaRect = area.getBoundingClientRect()
      const newLines = []
      for (const [ei, ci] of Object.entries(matches.value)) {
        const engEl = area.querySelector(`[data-ei="${ei}"]`)
        const chnEl = area.querySelector(`[data-ci="${ci}"]`)
        if (!engEl || !chnEl) continue
        const er = engEl.getBoundingClientRect()
        const cr = chnEl.getBoundingClientRect()
        newLines.push({
          x1: er.right - areaRect.left,
          y1: er.top + er.height / 2 - areaRect.top,
          x2: cr.left - areaRect.left,
          y2: cr.top + cr.height / 2 - areaRect.top,
        })
      }
      lines.value = newLines
    }

    const nextRound = () => {
      const next = currentRound.value + 1
      if (next * PER_ROUND < words.value.length) {
        currentRound.value = next
        setupRound()
        nextTick(() => drawLines())
      } else {
        isComplete.value = true
      }
    }

    const restart = () => {
      currentRound.value = 0
      isComplete.value = false
      lines.value = []
      setupRound()
    }

    const itemEngClass = (ei) => ({
      selected: selectedEng.value === ei,
      matched: matchedEngSet.value.has(ei),
      wrong: wrongFlash.value?.ei === ei,
    })

    const itemChnClass = (ci) => ({
      selected: selectedEng.value !== -1 && !matchedChnSet.value.has(ci),
      matched: matchedChnSet.value.has(ci),
      wrong: wrongFlash.value?.ci === ci,
    })

    const onResize = () => { nextTick(() => drawLines()) }

    watch(() => route.query.sectionId, loadWords)
    onMounted(() => {
      loadWords()
      window.addEventListener('resize', onResize)
    })
    onUnmounted(() => window.removeEventListener('resize', onResize))

    return {
      words, currentRound, totalRounds, roundWords, shuffledChinese,
      selectedEng, matches, wrongFlash, lines, matchAreaRef, svgRef,
      isComplete, allMatched,
      selectEnglish, selectChinese, nextRound, restart,
      itemEngClass, itemChnClass,
    }
  }
}
</script>

<style scoped>
.match-page { max-width: 600px; margin: 0 auto; text-align: center; }
.empty { text-align: center; padding: 40px; color: #999; }
.empty a { color: #4f46e5; }
.progress-info { margin-bottom: 8px; color: #666; font-size: 14px; }
.progress-bar { height: 6px; background: #e0e7ff; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.progress-fill { height: 100%; background: #8b5cf6; transition: width 0.3s; border-radius: 3px; }
.word-label { font-size: 13px; color: #999; margin-bottom: 16px; }

.match-area {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 40px;
  padding: 20px 0;
}
.line-svg {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 1;
}
.line-svg line {
  stroke: #8b5cf6; stroke-width: 2.5; stroke-linecap: round;
  opacity: 0.6;
}

.column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 2;
}

.match-item {
  padding: 14px 16px;
  border-radius: 12px;
  border: 2.5px solid #e0e7ff;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 17px;
  text-align: left;
  user-select: none;
}
.match-item:hover:not(.matched) { border-color: #8b5cf6; background: #f5f3ff; }
.match-item.selected { border-color: #8b5cf6; background: #ede9fe; box-shadow: 0 0 0 3px rgba(139,92,246,0.2); }
.match-item.matched { border-color: #22c55e; background: #f0fdf4; cursor: default; opacity: 0.8; }
.match-item.wrong { border-color: #ef4444; background: #fef2f2; animation: shake 0.4s; }

.item-num {
  display: inline-block; width: 24px; height: 24px; line-height: 24px;
  text-align: center; border-radius: 50%; background: #f3f4f6;
  font-size: 12px; color: #666; margin-right: 10px; font-weight: 600;
}
.match-item.matched .item-num { background: #22c55e; color: #fff; }
.match-item.selected .item-num { background: #8b5cf6; color: #fff; }

.next-round { margin-top: 24px; }
.next-round button { font-size: 18px; padding: 12px 40px; }

.result-card { text-align: center; padding: 40px; margin-top: 40px; }
.result-text { font-size: 18px; color: #666; margin: 16px 0; }
.result-actions { display: flex; gap: 16px; justify-content: center; margin-top: 24px; }

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
</style>
