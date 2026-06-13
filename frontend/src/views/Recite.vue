<template>
  <div class="recite-page">
    <div v-if="phase === 'loading'" class="loading">加载中...</div>

    <!-- ========== OVERVIEW ========== -->
    <template v-else-if="phase === 'overview'">
      <div v-if="showDraftRestore" class="restore-bar">
        📝 检测到未完成的练习（段落 {{ savedDraftPara + 1 }}）
        <button class="btn-ghost" @click="restoreDraft">恢复</button>
        <button class="btn-ghost" @click="clearDraft">丢弃</button>
      </div>
      <div class="card overview-header">
        <div class="overview-top">
          <h2>{{ article.title }}</h2>
          <router-link to="/articles" class="btn-ghost back-link">← 返回</router-link>
        </div>
        <div class="level-controls">
          <button class="btn-ghost" :disabled="level <= 1" @click="changeLevel(-1)">−</button>
          <span class="level-badge">Level {{ level }} · {{ levelLabels[level] }}</span>
          <button class="btn-ghost" :disabled="level >= 5" @click="changeLevel(1)">+</button>
          <span class="hide-info">隐藏 {{ level * 20 }}%</span>
        </div>
      </div>

      <div class="paragraph-list">
        <div
          v-for="p in paragraphs"
          :key="p.index"
          class="card para-card"
          :class="{ completed: p.progress.completed }"
        >
          <div class="para-header">
            <span class="para-num">段落 {{ p.index + 1 }}</span>
            <span v-if="p.progress.completed" class="badge-completed">✅ 已完成</span>
          </div>
          <div class="para-preview">{{ truncate(p.text, 120) }}</div>
          <div class="para-buttons">
            <button class="btn-primary" @click="startPractice(p.index)">{{ p.progress.completed ? '复习' : '背诵' }}</button>
            <button v-if="hasSpeech" class="btn-success" @click="startDictation(p.index)">🎤 听写</button>
          </div>
        </div>
      </div>

      <div class="card overall-stats">
        <h3>总体统计</h3>
        <p>已完成: {{ doneCount }} / {{ paragraphs.length }} 段</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (doneCount / paragraphs.length * 100) + '%' }"></div>
        </div>
      </div>
    </template>

    <!-- ========== DICTATION ========== -->
    <template v-else-if="phase === 'dictation'">
      <div class="card dictation-header">
        <button class="btn-ghost" @click="backToOverview">← 返回</button>
        <span class="dict-level">段落 {{ dictParaIdx + 1 }}</span>
        <span class="dict-progress">句子 {{ currentSentIdx + 1 }}/{{ sentences.length }}</span>
      </div>

      <div class="card dictation-area">
          <div v-if="!sentResults[currentSentIdx]" class="dict-stage">
            <div class="dict-sentence-num">第 {{ currentSentIdx + 1 }} 句</div>
            <div class="dict-original-text">{{ sentences[currentSentIdx] }}</div>

            <div v-if="transcribed[currentSentIdx]" class="dict-transcribed">
              <div class="dict-label">你的录音：</div>
              <div class="dict-spoken">{{ transcribed[currentSentIdx] }}</div>
            </div>

            <div class="dict-controls">
              <button class="btn-primary" @click="playSentence(currentSentIdx)" :disabled="isPlaying">
                {{ isPlaying ? '🔊 播放中...' : '🔊 播放' }}
              </button>
              <button
                v-if="hasSpeech"
                class="btn-success"
                @click="toggleRecording(currentSentIdx)"
                :disabled="isPlaying"
              >
                {{ isRecording ? '⏹ 停止' : '🎤 录音' }}
              </button>
              <button v-if="!hasSpeech" class="btn-ghost" disabled>当前浏览器不支持语音识别</button>
            </div>
          </div>

        <div v-else class="dict-result-view">
          <div class="dict-original-text">{{ sentences[currentSentIdx] }}</div>
          <div class="dict-match-area">
            <div
              v-for="(w, wi) in sentResults[currentSentIdx]"
              :key="wi"
              class="dict-word"
              :class="w.match ? 'dict-word-correct' : 'dict-word-wrong'"
            >
              <span class="dict-word-text">{{ w.word }}</span>
              <span v-if="!w.match" class="dict-word-spoken">{{ w.spoken || '—' }}</span>
            </div>
          </div>
          <div class="dict-score">
            得分: <strong>{{ sentScores[currentSentIdx] }}</strong> / {{ sentResults[currentSentIdx].length }}
          </div>
        </div>
      </div>

      <div class="card dictation-footer">
        <div v-if="dictFinished" class="dict-final-score">
          <h3>听写完成！</h3>
          <p>总得分: {{ totalDictScore }} / {{ totalDictWords }}</p>
        </div>
        <div class="dict-footer-actions">
          <button
            v-if="!dictFinished"
            class="btn-primary"
            @click="nextDictSentence"
            :disabled="!sentResults[currentSentIdx] && !transcribed[currentSentIdx]"
          >{{ currentSentIdx < sentences.length - 1 ? '下一句 →' : '查看结果' }}</button>
          <button class="btn-ghost" @click="backToOverview">返回概览</button>
        </div>
      </div>
    </template>

    <!-- ========== PRACTICE ========== -->
    <template v-else-if="phase === 'practice'">
      <div class="card practice-header">
        <button class="btn-ghost" @click="backToOverview">← 返回</button>
        <span class="practice-level">Level {{ level }} · 段落 {{ currentParaIdx + 1 }}/{{ paragraphs.length }}</span>
        <span class="practice-progress">已填 {{ filledCount }}/{{ blanksCount }}</span>
        <button v-if="!draftSaved" class="btn-ghost btn-draft" @click="saveDraft">💾 暂存</button>
        <span v-else class="draft-badge">📝 已暂存</span>
      </div>

      <div class="card practice-area">
        <div class="practice-text">
          <span v-for="(token, i) in currentPara.tokens" :key="i" class="token-wrap">
            <span v-if="!currentPara.hidden_indices.includes(i)" class="token-visible">{{ token }}</span>
            <input
              v-else
              ref="inputs"
              :data-idx="i"
              v-model="answers[i]"
              :style="{ width: Math.max(40, token.length * 14 + 16) + 'px' }"
              :class="['token-input', {
                'i-correct': results[i] === 'correct',
                'i-wrong': results[i] === 'wrong'
              }]"
              :disabled="results[i] !== undefined"
              :placeholder="' '.repeat(token.length > 2 ? token.length - 1 : 0)"
              @input="markUnsaved"
              @keydown.enter.prevent="handleEnter(i)"
              @keydown.tab.prevent="handleTab($event, i)"
            />
            <span v-if="results[i] === 'wrong'" class="correct-hint">{{ token }}</span>
          </span>
        </div>
      </div>

      <div class="card practice-actions">
        <span class="result-stats" v-if="submitted">
          正确: <strong>{{ correctCount }}</strong> / {{ blanksCount }}
          ({{ blanksCount > 0 ? Math.round(correctCount / blanksCount * 100) : 0 }}%)
        </span>
        <button v-if="!submitted" class="btn-primary" :disabled="filledCount < blanksCount" @click="submitPractice">
          提交答案
        </button>
        <template v-else>
          <div class="result-badge" :class="passed ? 'pass' : 'fail'">
            {{ passed ? '🎉 通过！正确率 ≥ 80%' : '💪 继续加油！正确率 < 80%' }}
          </div>
          <div class="result-actions">
            <button v-if="passed && currentParaIdx < paragraphs.length - 1" class="btn-success" @click="nextParagraph">
              下一段
            </button>
            <button v-if="passed && currentParaIdx === paragraphs.length - 1" class="btn-success" @click="finishAll">
              全部完成
            </button>
            <button v-if="!passed" class="btn-primary" @click="retryPractice">
              重新练习
            </button>
            <button class="btn-ghost" @click="backToOverview">返回概览</button>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

export default {
  name: 'Recite',
  setup() {
    const route = useRoute()
    const phase = ref('loading')
    const article = ref(null)
    const paragraphs = ref([])
    const level = ref(1)
    const currentParaIdx = ref(0)
    const answers = ref({})
    const results = ref({})
    const submitted = ref(false)
    const draftSaved = ref(false)
    const showDraftRestore = ref(false)
    const savedDraftPara = ref(0)

    const levelLabels = { 1: '简单', 2: '普通', 3: '困难', 4: '挑战', 5: '默写' }

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition
    const hasSpeech = !!SpeechRecognitionAPI

    const dictParaIdx = ref(0)
    const sentences = ref([])
    const currentSentIdx = ref(0)
    const transcribed = ref({})
    const playedAt = ref({})
    const sentResults = ref({})
    const sentScores = ref({})
    const dictFinished = ref(false)
    const isRecording = ref(false)
    const isPlaying = ref(false)
    let recognitionInstance = null
    let currentRecogTargetIdx = -1

    const totalDictScore = computed(() => {
      let s = 0
      for (const k in sentScores.value) s += sentScores.value[k]
      return s
    })
    const totalDictWords = computed(() => {
      let s = 0
      for (const k in sentResults.value) s += sentResults.value[k].length
      return s
    })

    const currentPara = computed(() => paragraphs.value[currentParaIdx.value])
    const blanksCount = computed(() => currentPara.value ? currentPara.value.hidden_indices.length : 0)
    const filledCount = computed(() => Object.keys(answers.value).length)
    const correctCount = computed(() => Object.values(results.value).filter(v => v === 'correct').length)
    const passed = computed(() => blanksCount.value > 0 && correctCount.value / blanksCount.value >= 0.8)
    const doneCount = computed(() => paragraphs.value.filter(p => p.progress.completed).length)

    const DRAFT_PREFIX = 'recite_draft_'
    const articleId = () => parseInt(route.query.articleId)
    const currentAid = () => articleId() || parseInt(new URLSearchParams(window.location.search).get('articleId'))

    const saveDraft = () => {
      if (phase.value !== 'practice' || submitted.value) return
      const data = {
        articleId: currentAid(),
        level: level.value,
        currentParaIdx: currentParaIdx.value,
        answers: { ...answers.value },
        results: { ...results.value },
        submitted: submitted.value,
        _savedAt: Date.now()
      }
      localStorage.setItem(DRAFT_PREFIX + window.location.search, JSON.stringify(data))
      draftSaved.value = true
    }

    const loadDraft = () => {
      const raw = localStorage.getItem(DRAFT_PREFIX + window.location.search)
      if (!raw) return null
      try { return JSON.parse(raw) } catch { return null }
    }

    const clearDraft = () => {
      localStorage.removeItem(DRAFT_PREFIX + window.location.search)
      draftSaved.value = false
      showDraftRestore.value = false
    }

    const restoreDraft = async () => {
      const draft = loadDraft()
      if (!draft) return
      try {
        const data = await api.getReciteData(draft.articleId, draft.level)
        article.value = data
        paragraphs.value = data.paragraphs
        level.value = draft.level
        currentParaIdx.value = draft.currentParaIdx
        answers.value = draft.answers || {}
        results.value = draft.results || {}
        submitted.value = draft.submitted || false
        showDraftRestore.value = false
        draftSaved.value = true
        phase.value = 'practice'
        nextTick(() => {
          if (!submitted.value) focusFirstBlank()
        })
      } catch {}
    }

    const checkDraft = () => {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (!key || !key.startsWith(DRAFT_PREFIX)) continue
        try {
          const draft = JSON.parse(localStorage.getItem(key))
          if (draft && draft.articleId === currentAid() && !draft.submitted) {
            savedDraftPara.value = draft.currentParaIdx
            showDraftRestore.value = true
            return
          }
        } catch {}
      }
    }

    const loadData = async (lvl) => {
      const aid = articleId()
      if (!aid) return
      try {
        const data = await api.getReciteData(aid, lvl)
        article.value = data
        paragraphs.value = data.paragraphs
        level.value = data.level
        phase.value = 'overview'
      } catch {}
    }

    const changeLevel = (delta) => {
      const newLevel = level.value + delta
      if (newLevel < 1 || newLevel > 5) return
      level.value = newLevel
      clearDraft()
      loadData(newLevel)
    }

    const startPractice = (idx) => {
      clearDraft()
      currentParaIdx.value = idx
      answers.value = {}
      results.value = {}
      submitted.value = false
      phase.value = 'practice'
      nextTick(() => focusFirstBlank())
    }

    const backToOverview = () => {
      phase.value = 'overview'
      loadData(level.value)
    }

    const focusFirstBlank = () => {
      const el = document.querySelector('.token-input:not([disabled])')
      if (el) el.focus()
    }

    const markUnsaved = () => {
      draftSaved.value = false
    }

    const handleEnter = (i) => {
      validateBlank(i)
      if (results.value[i] === 'wrong') return
      moveToNext(i)
    }

    const handleTab = (e, i) => {
      if (results.value[i] === undefined) {
        validateBlank(i)
      }
      const next = findNextBlank(i)
      if (next !== -1) {
        const el = document.querySelector(`.token-input[data-idx="${next}"]`)
        if (el) el.focus()
      } else {
        e.preventDefault()
        const submitBtn = document.querySelector('.btn-primary')
        if (submitBtn && !submitBtn.disabled) submitBtn.click()
      }
    }

    const findNextBlank = (current) => {
      const hidden = currentPara.value.hidden_indices
      const ci = hidden.indexOf(current)
      for (let j = ci + 1; j < hidden.length; j++) {
        if (results.value[hidden[j]] === undefined) return hidden[j]
      }
      return -1
    }

    const validateBlank = (i) => {
      const val = (answers.value[i] || '').trim()
      const correct = currentPara.value.tokens[i].trim()
      if (!val) return
      if (val.toLowerCase() === correct.toLowerCase()) {
        results.value[i] = 'correct'
      } else {
        results.value[i] = 'wrong'
      }
    }

    const moveToNext = (i) => {
      const next = findNextBlank(i)
      if (next !== -1) {
        const el = document.querySelector(`.token-input[data-idx="${next}"]`)
        if (el) el.focus()
      } else {
        const submitBtn = document.querySelector('.btn-primary')
        if (submitBtn && !submitBtn.disabled) submitBtn.click()
      }
    }

    const submitPractice = async () => {
      submitted.value = true
      clearDraft()
      const total = blanksCount.value
      let correct = 0
      let wrong = 0
      for (const i of currentPara.value.hidden_indices) {
        if (results.value[i] === 'correct') correct++
        else if (results.value[i] === 'wrong') wrong++
        else {
          const val = (answers.value[i] || '').trim()
          const correctToken = currentPara.value.tokens[i].trim()
          if (val.toLowerCase() === correctToken.toLowerCase()) {
            results.value[i] = 'correct'
            correct++
          } else {
            results.value[i] = 'wrong'
            wrong++
          }
        }
      }
      try {
        await api.submitPractice(article.value.id, {
          paragraph_index: currentParaIdx.value,
          level: level.value,
          total_blanks: total,
          correct,
          wrong,
          completed: passed.value
        })
        if (passed.value) {
          paragraphs.value[currentParaIdx.value].progress.completed = true
        }
      } catch {}
    }

    const nextParagraph = () => {
      clearDraft()
      currentParaIdx.value++
      answers.value = {}
      results.value = {}
      submitted.value = false
      nextTick(() => focusFirstBlank())
    }

    const retryPractice = () => {
      clearDraft()
      answers.value = {}
      results.value = {}
      submitted.value = false
      nextTick(() => focusFirstBlank())
    }

    const finishAll = () => {
      backToOverview()
    }

    const truncate = (text, n) => {
      return text.length > n ? text.slice(0, n) + '…' : text
    }

    /* ----- Dictation ----- */
    const splitSentences = (text) => {
      if (article.value.language === 'zh') {
        const m = text.match(/[^。！？]+[。！？]/g)
        return m && m.length ? m : [text]
      }
      const m = text.match(/[^.!?]+[.!?]/g)
      return m && m.length ? m : [text]
    }

    const startDictation = (paraIdx) => {
      dictParaIdx.value = paraIdx
      const paraText = paragraphs.value[paraIdx].text
      sentences.value = splitSentences(paraText)
      currentSentIdx.value = 0
      transcribed.value = {}
      playedAt.value = {}
      sentResults.value = {}
      sentScores.value = {}
      dictFinished.value = false
      phase.value = 'dictation'
    }

    const playSentence = (idx) => {
      if (isPlaying.value) return
      const text = sentences.value[idx]
      if (!text) return
      isPlaying.value = true
      playedAt.value = { ...playedAt.value, [idx]: true }
      const lang = article.value.language === 'zh' ? 'zh-CN' : 'en-US'
      const utter = new SpeechSynthesisUtterance(text)
      utter.lang = lang
      utter.rate = 0.8
      utter.onend = () => { isPlaying.value = false }
      utter.onerror = () => { isPlaying.value = false }
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(utter)
    }

    const toggleRecording = (idx) => {
      if (isRecording.value) {
        stopRecording()
      } else {
        startRecording(idx)
      }
    }

    const startRecording = (idx) => {
      if (!SpeechRecognitionAPI) return
      currentRecogTargetIdx = idx
      recognitionInstance = new SpeechRecognitionAPI()
      const lang = article.value.language === 'zh' ? 'zh-CN' : 'en-US'
      recognitionInstance.lang = lang
      recognitionInstance.continuous = false
      recognitionInstance.interimResults = false
      recognitionInstance.maxAlternatives = 1

      recognitionInstance.onresult = (e) => {
        const text = e.results[0][0].transcript.trim()
        transcribed.value = { ...transcribed.value, [idx]: text }
        compareSentence(idx, text)
        stopRecording()
      }

      recognitionInstance.onerror = () => { stopRecording() }
      recognitionInstance.onend = () => { isRecording.value = false }

      try {
        recognitionInstance.start()
        isRecording.value = true
      } catch { isRecording.value = false }
    }

    const stopRecording = () => {
      if (recognitionInstance) {
        try { recognitionInstance.stop() } catch {}
        recognitionInstance = null
      }
      isRecording.value = false
    }

    const compareSentence = (idx, spoken) => {
      const original = sentences.value[idx]
      const origTokens = tokenizeSimple(original, article.value.language)
      const spokenTokens = tokenizeSimple(spoken, article.value.language)

      const matched = []
      let score = 0
      for (let i = 0; i < origTokens.length; i++) {
        const ot = origTokens[i]
        const foundIdx = spokenTokens.findIndex(st => st.toLowerCase() === ot.toLowerCase())
        if (foundIdx !== -1) {
          matched.push({ word: ot, match: true, spoken: spokenTokens[foundIdx] })
          spokenTokens.splice(foundIdx, 1)
          score++
        } else {
          matched.push({ word: ot, match: false, spoken: null })
        }
      }
      sentResults.value = { ...sentResults.value, [idx]: matched }
      sentScores.value = { ...sentScores.value, [idx]: score }
    }

    const tokenizeSimple = (text, lang) => {
      if (lang === 'zh') {
        return text.replace(/[，。！？、；：""''（）\s]+/g, ' ').trim().split(/\s+/)
      }
      return text.replace(/[.,!?;:'"()\s]+/g, ' ').trim().split(/\s+/)
    }

    const nextDictSentence = () => {
      if (currentSentIdx.value < sentences.value.length - 1) {
        currentSentIdx.value++
        window.speechSynthesis.cancel()
      } else {
        dictFinished.value = true
      }
    }

    watch(() => route.query.articleId, () => {
      if (route.name === 'Recite') loadData(level.value)
    })

    onMounted(async () => {
      await loadData(level.value)
      checkDraft()
    })

    return {
      phase, article, paragraphs, level, currentParaIdx,
      answers, results, submitted, draftSaved,
      showDraftRestore, savedDraftPara,
      levelLabels, currentPara, blanksCount, filledCount,
      correctCount, passed, doneCount,
      changeLevel, startPractice, backToOverview,
      handleEnter, handleTab, submitPractice, markUnsaved, saveDraft,
      nextParagraph, retryPractice, finishAll, truncate,
      restoreDraft, clearDraft,
      hasSpeech, dictParaIdx, sentences, currentSentIdx,
      transcribed, playedAt, sentResults, sentScores,
      dictFinished, isRecording, isPlaying,
      totalDictScore, totalDictWords,
      startDictation, playSentence, toggleRecording, nextDictSentence
    }
  }
}
</script>

<style scoped>
.recite-page { display: flex; flex-direction: column; gap: 16px; }
.loading { text-align: center; padding: 60px; color: #999; }

/* OVERVIEW */
.overview-header { display: flex; flex-direction: column; gap: 12px; }
.overview-top { display: flex; justify-content: space-between; align-items: center; }
.overview-top h2 { font-size: 22px; color: #333; }
.back-link { text-decoration: none; }
.level-controls { display: flex; align-items: center; gap: 8px; }
.level-badge { font-weight: bold; color: #4f46e5; font-size: 16px; min-width: 120px; text-align: center; }
.hide-info { font-size: 13px; color: #999; margin-left: 8px; }
.paragraph-list { display: flex; flex-direction: column; gap: 12px; }
.para-card { display: flex; flex-direction: column; gap: 8px; border-left: 4px solid #e0e7ff; }
.para-card.completed { border-left-color: #22c55e; }
.para-header { display: flex; align-items: center; gap: 8px; }
.para-num { font-weight: bold; color: #4f46e5; font-size: 14px; }
.badge-completed { font-size: 12px; color: #22c55e; }
.para-preview { font-size: 14px; color: #666; line-height: 1.6; }
.overall-stats { text-align: center; }
.overall-stats h3 { margin-bottom: 8px; }
.overall-stats p { font-size: 14px; color: #666; margin-bottom: 8px; }
.progress-bar { height: 8px; background: #e0e7ff; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #4f46e5; border-radius: 4px; transition: width 0.3s; }

/* PRACTICE */
.practice-header { display: flex; align-items: center; gap: 16px; font-size: 14px; }
.practice-level { font-weight: bold; color: #4f46e5; }
.practice-progress { color: #999; margin-left: auto; }
.practice-area { line-height: 2.4; font-size: 18px; }
.practice-text {
  display: inline; white-space: pre-wrap; word-break: break-word;
  font-size: 18px; line-height: 2.8;
}
.token-wrap { display: inline; white-space: pre; }
.token-visible { color: #333; }
.token-input {
  display: inline-block;
  padding: 2px 6px;
  border: none;
  border-bottom: 2px solid #4f46e5;
  background: transparent;
  font-size: 18px;
  font-family: inherit;
  text-align: center;
  outline: none;
  transition: all 0.2s;
}
.token-input:focus { border-bottom-color: #4f46e5; background: #eef2ff; }
.token-input.i-correct { border-bottom-color: #22c55e; background: #f0fdf4; }
.token-input.i-wrong { border-bottom-color: #ef4444; background: #fef2f2; }
.correct-hint { font-size: 14px; color: #22c55e; margin-left: 2px; font-weight: bold; }

.practice-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.result-stats { font-size: 15px; color: #666; }
.result-badge { font-size: 16px; font-weight: bold; }
.result-badge.pass { color: #22c55e; }
.result-badge.fail { color: #ef4444; }
.result-actions { display: flex; gap: 8px; }
.draft-badge { font-size: 11px; color: #d97706; background: #fef3c7; padding: 2px 6px; border-radius: 4px; margin-left: auto; }
.restore-bar { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: #fef3c7; border-radius: 12px; font-size: 14px; color: #92400e; }
.restore-bar button { font-size: 12px; padding: 4px 10px; }
.para-buttons { display: flex; gap: 8px; margin-top: 4px; }

/* DICTATION */
.dictation-header { display: flex; align-items: center; gap: 16px; font-size: 14px; }
.dict-level { font-weight: bold; color: #22c55e; }
.dict-progress { color: #999; margin-left: auto; }
.dictation-area { text-align: center; min-height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20px; }
.dict-stage { display: flex; flex-direction: column; align-items: center; gap: 16px; width: 100%; }
.dict-sentence-num { font-size: 13px; color: #999; }
.dict-original-text { font-size: 20px; color: #333; line-height: 1.8; padding: 12px 20px; background: #f0fdf4; border-radius: 12px; width: 100%; }
.dict-hidden-hint { font-size: 16px; color: #ccc; padding: 20px; }
.dict-transcribed { width: 100%; }
.dict-label { font-size: 13px; color: #999; margin-bottom: 4px; }
.dict-spoken { font-size: 18px; color: #4f46e5; padding: 8px 16px; background: #eef2ff; border-radius: 8px; }
.dict-controls { display: flex; gap: 12px; }
.dict-result-view { width: 100%; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.dict-match-area { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.dict-word { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 4px 10px; border-radius: 8px; font-size: 16px; }
.dict-word-correct { background: #f0fdf4; color: #22c55e; }
.dict-word-wrong { background: #fef2f2; color: #ef4444; }
.dict-word-text { font-weight: bold; }
.dict-word-spoken { font-size: 11px; color: #999; }
.dict-score { font-size: 16px; color: #333; }
.dictation-footer { text-align: center; }
.dict-final-score { margin-bottom: 12px; }
.dict-final-score h3 { color: #22c55e; margin-bottom: 4px; }
.dict-final-score p { font-size: 14px; color: #666; }
.dict-footer-actions { display: flex; gap: 8px; justify-content: center; }
</style>
