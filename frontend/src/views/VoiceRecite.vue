<template>
  <div class="voice-recite-page">
    <div v-if="phase === 'loading'" class="loading">加载中...</div>

    <!-- ========== OVERVIEW ========== -->
    <template v-else-if="phase === 'overview'">
      <div class="card overview-header">
        <div class="overview-top">
          <h2>{{ article.title }}</h2>
          <router-link to="/articles" class="btn-ghost back-link">← 返回</router-link>
        </div>
        <div class="level-controls">
          <button class="btn-ghost" :disabled="level <= 1" @click="changeLevel(-1)">−</button>
          <span class="level-badge">Level {{ level }} · {{ levelLabels[level] }}</span>
          <button class="btn-ghost" :disabled="level >= 5" @click="changeLevel(1)">+</button>
          <span class="hide-info">{{ levelDesc[level] }}</span>
        </div>
        <div v-if="!supported" class="browser-warning">
          ⚠️ 当前浏览器不支持语音识别，请使用 Chrome 或 Edge。
        </div>
      </div>

      <div class="paragraph-list">
        <div v-for="p in paragraphs" :key="p.index" class="card para-card">
          <div class="para-header">
            <span class="para-num">段落 {{ p.index + 1 }}</span>
            <span v-if="p.voiceAccuracy" class="badge-accuracy">
              {{ (p.voiceAccuracy * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="para-preview">{{ truncate(p.text, 120) }}</div>
          <div class="para-modes">
            <label class="mode-option" :class="{ active: p.mode === 'full' }">
              <input type="radio" :name="'mode_' + p.index" value="full" v-model="p.mode" />
              整段朗读
            </label>
            <label class="mode-option" :class="{ active: p.mode === 'sentence' }">
              <input type="radio" :name="'mode_' + p.index" value="sentence" v-model="p.mode" />
              逐句朗读
            </label>
          </div>
          <button class="btn-primary" @click="startPractice(p.index)">开始语音背诵</button>
        </div>
      </div>
    </template>

    <!-- ========== PRACTICE ========== -->
    <template v-else-if="phase === 'practice'">
      <div class="card practice-header">
        <button class="btn-ghost" @click="backToOverview">← 返回</button>
        <span class="practice-level">Level {{ level }} · 段落 {{ currentParaIdx + 1 }}/{{ paragraphs.length }}</span>
        <span class="practice-mode">{{ currentPara.mode === 'full' ? '整段朗读' : '逐句朗读' }}</span>
        <span v-if="recording" class="recording-indicator">🔴 录音中 {{ elapsed }}s</span>
      </div>

      <!-- Full paragraph mode -->
      <template v-if="currentPara.mode === 'full'">
        <div class="card practice-area">
          <div class="section-label">
            <span>原文</span>
            <div class="record-controls">
              <button v-if="!recording && !done" class="btn-primary record-btn" @click="startRecording">
                🎤 开始朗读
              </button>
              <button v-if="recording" class="btn-danger record-btn" @click="stopRecording">
                ⏹ 停止录音
              </button>
              <button v-if="done" class="btn-ghost" @click="resetPractice">重新练习</button>
            </div>
          </div>
          <div class="text-display original-text">
            <span v-for="(item, i) in fullDisplayTokens" :key="i"
                  :class="['token-display', item.status]"
                  :title="item.original">
              {{ item.display }}
            </span>
          </div>
        </div>

        <div v-if="recognizedText" class="card practice-area">
          <div class="section-label">识别结果</div>
          <div class="text-display recognized-text">{{ recognizedText }}</div>
        </div>

        <div v-if="done" class="card result-area">
          <div class="result-summary">
            <span :class="resultClass">{{ (accuracy * 100).toFixed(1) }}% 准确率</span>
            <span>正确 {{ correctWords }}/{{ totalWords }} 词</span>
            <span>用时 {{ duration }}s</span>
          </div>
          <div class="result-actions">
            <button v-if="currentParaIdx < paragraphs.length - 1" class="btn-success" @click="nextParagraph">下一段</button>
            <button v-if="currentParaIdx === paragraphs.length - 1" class="btn-success" @click="finishAll">全部完成</button>
            <button class="btn-ghost" @click="resetPractice">重新练习</button>
          </div>
        </div>
      </template>

      <!-- Sentence mode -->
      <template v-if="currentPara.mode === 'sentence'">
        <div class="card practice-area">
          <div class="section-label">
            <span>句子 {{ sentenceIdx + 1 }}/{{ sentences.length }}</span>
            <div class="record-controls">
              <button v-if="!recording && !sentenceDone" class="btn-primary record-btn" @click="startRecording">
                🎤 开始朗读
              </button>
              <button v-if="recording" class="btn-danger record-btn" @click="stopRecording">
                ⏹ 停止录音
              </button>
              <button v-if="sentenceDone && sentenceIdx < sentences.length - 1" class="btn-success" @click="nextSentence">下一句</button>
              <button v-if="sentenceDone && sentenceIdx === sentences.length - 1" class="btn-success" @click="finishAllSentences">查看总评</button>
            </div>
          </div>
          <div class="text-display original-text">
            <span v-for="(item, i) in sentenceDisplayTokens" :key="i"
                  :class="['token-display', item.status]"
                  :title="item.original">
              {{ item.display }}
            </span>
          </div>
        </div>

        <div v-if="sentenceRecognized" class="card practice-area">
          <div class="section-label">识别结果</div>
          <div class="text-display recognized-text">{{ sentenceRecognized }}</div>
        </div>

        <div v-if="sentenceResult" class="card result-area">
          <div class="result-summary">
            <span :class="sentenceResult.accuracy >= 0.8 ? 'pass' : 'fail'">
              {{ (sentenceResult.accuracy * 100).toFixed(0) }}% 准确率
            </span>
          </div>
        </div>

        <div v-if="showSentenceSummary" class="card result-area">
          <h3>总评</h3>
          <div class="result-summary">
            <span :class="resultClass">{{ (accuracy * 100).toFixed(1) }}% 平均准确率</span>
            <span>正确 {{ correctWords }}/{{ totalWords }} 词</span>
            <span>用时 {{ duration }}s</span>
          </div>
          <div class="result-actions">
            <button v-if="currentParaIdx < paragraphs.length - 1" class="btn-success" @click="nextParagraph">下一段</button>
            <button v-if="currentParaIdx === paragraphs.length - 1" class="btn-success" @click="finishAll">全部完成</button>
            <button class="btn-ghost" @click="showSentenceSummary = false; resetPractice()">重新练习</button>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'

function levenshteinAlign(orig, recog) {
  const m = orig.length, n = recog.length
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = 0; i <= m; i++) dp[i][0] = i
  for (let j = 0; j <= n; j++) dp[0][j] = j
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = orig[i - 1].toLowerCase() === recog[j - 1].toLowerCase() ? 0 : 1
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    }
  }
  const alignment = []
  let i = m, j = n
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && dp[i][j] === dp[i - 1][j - 1] && orig[i - 1].toLowerCase() === recog[j - 1].toLowerCase()) {
      alignment.unshift({ word: orig[i - 1], status: 'correct' }); i--; j--
    } else if (i > 0 && j > 0 && dp[i][j] === dp[i - 1][j - 1] + 1) {
      alignment.unshift({ word: orig[i - 1], status: 'wrong', expected: orig[i - 1], got: recog[j - 1] }); i--; j--
    } else if (j > 0 && dp[i][j] === dp[i][j - 1] + 1) {
      alignment.unshift({ word: recog[j - 1], status: 'extra' }); j--
    } else {
      alignment.unshift({ word: orig[i - 1], status: 'missing' }); i--
    }
  }
  return alignment
}

function tokenizeText(text, language) {
  let words = text.split(/\s+/).filter(Boolean)
  if (language === 'zh') {
    words = []
    for (const ch of text) { if (ch.trim()) words.push(ch) }
    if (!words.length) words = text.split(/\s+/).filter(Boolean)
  }
  return words.map(w => w.replace(/^[^\w']+|[^\w']+$/g, '').toLowerCase()).filter(Boolean)
}

function splitSentences(text, language) {
  if (language === 'zh') return text.split(/(?<=[。！？\n])/).map(s => s.trim()).filter(Boolean)
  return text.split(/(?<=[.!?\n])/).map(s => s.trim()).filter(Boolean)
}

function selectHidden(count, ratio) {
  if (count <= 0 || ratio <= 0) return []
  const n = Math.max(1, Math.round(count * ratio))
  if (n >= count) return Array.from({ length: count }, (_, i) => i)
  const step = count / n
  const indices = new Set()
  for (let i = 0; i < n; i++) indices.add(Math.min(Math.round(i * step + step / 2), count - 1))
  return [...indices].sort((a, b) => a - b)
}

function compareTexts(origTokens, recogTokens) {
  const alignment = levenshteinAlign(origTokens, recogTokens)
  let correct = 0, total = 0
  for (const a of alignment) {
    if (a.status !== 'extra') total++
    if (a.status === 'correct') correct++
  }
  return { alignment, correct, total, accuracy: total > 0 ? correct / total : 0 }
}

export default {
  name: 'VoiceRecite',
  setup() {
    const route = useRoute()
    const phase = ref('loading')
    const article = ref(null)
    const paragraphs = ref([])
    const level = ref(1)
    const currentParaIdx = ref(0)
    const supported = ref(true)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    const levelLabels = { 1: '跟读', 2: '简单', 3: '普通', 4: '困难', 5: '默写' }
    const levelDesc = { 1: '全文可见', 2: '每句隐藏 1 词', 3: '每句隐藏 30%', 4: '每句隐藏 70%', 5: '全文隐藏' }

    const currentPara = computed(() => paragraphs.value[currentParaIdx.value] || {})

    const loadData = async (lvl) => {
      const aid = parseInt(route.query.articleId)
      if (!aid) return
      try {
        const data = await api.getReciteData(aid, lvl)
        article.value = data
        level.value = data.level
        paragraphs.value = data.paragraphs.map((p, i) => ({ ...p, mode: 'full', voiceAccuracy: 0 }))
        const progress = await api.getVoiceProgress(aid)
        for (const p of progress) {
          const para = paragraphs.value[p.paragraph_index]
          if (para && p.level === level.value) para.voiceAccuracy = p.accuracy
        }
        phase.value = 'overview'
      } catch { phase.value = 'overview' }
    }

    const changeLevel = (delta) => {
      const newLevel = level.value + delta
      if (newLevel < 1 || newLevel > 5) return
      level.value = newLevel
      loadData(newLevel)
    }

    const truncate = (text, n) => text.length > n ? text.slice(0, n) + '\u2026' : text

    // ===== Practice state =====
    const recording = ref(false)
    const elapsed = ref(0)
    const done = ref(false)
    const recognizedText = ref('')
    const accuracy = ref(0)
    const correctWords = ref(0)
    const totalWords = ref(0)
    const duration = ref(0)
    const fullDisplayTokens = ref([])
    const resultClass = computed(() => accuracy.value >= 0.8 ? 'pass' : 'fail')

    let recognitionInstance = null
    let timer = null
    let startTime = 0

    const buildTokens = (tokens, hiddenIndices, alignment) => {
      return tokens.map((token, i) => {
        const isHidden = hiddenIndices.includes(i)
        const al = alignment ? alignment.find(a => a.word === token) : null
        let display = token, status = ''
        if (level.value === 5) {
          if (al && al.status === 'correct') { display = token; status = 'correct-word' }
          else if (al && al.status === 'wrong') { display = token; status = 'wrong-word' }
          else if (al && al.status === 'missing') { display = token + '?'; status = 'missing-word' }
          else { display = '____'; status = '' }
        } else if (level.value === 1 || !isHidden) {
          if (al) {
            if (al.status === 'correct') status = 'correct-word'
            else if (al.status === 'wrong') status = 'wrong-word'
            else if (al.status === 'missing') { status = 'missing-word'; display = token + '?' }
          }
        } else {
          if (al && al.status === 'correct') { display = token; status = 'correct-word' }
          else if (al && al.status === 'wrong') { display = token; status = 'wrong-word' }
          else { display = '____' }
        }
        return { display, original: token, status }
      })
    }

    const getHiddenIndices = (origTokens) => {
      if (level.value === 1) return []
      if (level.value === 2) return origTokens.length > 0 ? [0] : []
      return selectHidden(origTokens.length, level.value * 0.2)
    }

    const startRecording = () => {
      if (!SpeechRecognition) { supported.value = false; return }
      if (recognitionInstance) recognitionInstance.abort()
      const recog = new SpeechRecognition()
      recog.lang = article.value.language === 'zh' ? 'zh-CN' : 'en-US'
      recog.continuous = true
      recog.interimResults = true
      recog.maxAlternatives = 1

      recog.onresult = (e) => {
        let final = '', interim = ''
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) final += e.results[i][0].transcript + ' '
          else interim += e.results[i][0].transcript
        }
        const text = (final + interim).trim()
        if (currentPara.value.mode === 'full') recognizedText.value = text
        else sentenceRecognized.value = text
      }

      recog.onend = () => {
        if (recording.value) {
          recording.value = false
          clearInterval(timer)
          if (currentPara.value.mode === 'sentence') doSentenceCompare()
          else doCompare()
        }
      }

      recog.onerror = () => { recording.value = false; clearInterval(timer) }

      recording.value = true
      startTime = Date.now()
      timer = setInterval(() => { elapsed.value = Math.floor((Date.now() - startTime) / 1000) }, 200)
      recog.start()
      recognitionInstance = recog
    }

    const stopRecording = () => {
      if (recognitionInstance) { recognitionInstance.stop(); recognitionInstance = null }
      recording.value = false
      clearInterval(timer)
    }

    const doCompare = () => {
      const para = currentPara.value
      const origTokens = tokenizeText(para.text, article.value.language)
      const recogTokens = tokenizeText(recognizedText.value, article.value.language)
      const hiddenIndices = getHiddenIndices(origTokens)
      const result = compareTexts(origTokens, recogTokens)
      fullDisplayTokens.value = buildTokens(origTokens, hiddenIndices, result.alignment)
      accuracy.value = result.accuracy
      correctWords.value = result.correct
      totalWords.value = result.total
      duration.value = elapsed.value
      done.value = true
      api.submitVoicePractice(article.value.id, {
        paragraph_index: currentParaIdx.value, mode: 'full', level: level.value,
        total_words: result.total, correct_words: result.correct,
        accuracy: result.accuracy, duration_ms: elapsed.value * 1000
      }).catch(() => {})
    }

    const resetPractice = () => {
      recognizedText.value = ''
      fullDisplayTokens.value = []
      accuracy.value = 0; correctWords.value = 0; totalWords.value = 0
      duration.value = 0; done.value = false; elapsed.value = 0
      recording.value = false
      sentenceIdx.value = 0; sentenceDone.value = false
      sentenceRecognized.value = ''; sentenceResult.value = null
      showSentenceSummary.value = false
      sentenceResults.value = []
      if (recognitionInstance) { recognitionInstance.abort(); recognitionInstance = null }
    }

    // ===== Sentence mode =====
    const sentences = ref([])
    const sentenceIdx = ref(0)
    const sentenceDone = ref(false)
    const sentenceRecognized = ref('')
    const sentenceResult = ref(null)
    const showSentenceSummary = ref(false)
    const sentenceResults = ref([])

    const sentenceDisplayTokens = computed(() => {
      if (!sentences.value.length) return []
      const s = sentences.value[sentenceIdx.value]
      if (!s) return []
      const origTokens = tokenizeText(s, article.value.language)
      const hiddenIndices = getHiddenIndices(origTokens)
      return buildTokens(origTokens, hiddenIndices, sentenceResult.value ? sentenceResult.value.alignment : null)
    })

    const doSentenceCompare = () => {
      const s = sentences.value[sentenceIdx.value]
      if (!s) return
      const origTokens = tokenizeText(s, article.value.language)
      const recogTokens = tokenizeText(sentenceRecognized.value, article.value.language)
      const result = compareTexts(origTokens, recogTokens)
      sentenceResult.value = result
      sentenceResults.value.push(result)
      sentenceDone.value = true
    }

    const nextSentence = () => {
      sentenceIdx.value++
      sentenceDone.value = false
      sentenceRecognized.value = ''
      sentenceResult.value = null
    }

    const finishAllSentences = () => {
      showSentenceSummary.value = true
      let cor = 0, tot = 0
      for (const r of sentenceResults.value) { cor += r.correct; tot += r.total }
      accuracy.value = tot > 0 ? cor / tot : 0
      correctWords.value = cor
      totalWords.value = tot
      duration.value = Math.floor((Date.now() - startTime) / 1000)
      api.submitVoicePractice(article.value.id, {
        paragraph_index: currentParaIdx.value, mode: 'sentence', level: level.value,
        total_words: tot, correct_words: cor, accuracy: accuracy.value, duration_ms: duration.value * 1000
      }).catch(() => {})
    }

    const startPractice = (idx) => {
      currentParaIdx.value = idx
      const para = paragraphs.value[idx]
      if (para.mode === 'sentence') sentences.value = splitSentences(para.text, article.value.language)
      phase.value = 'practice'
      resetPractice()
    }

    const backToOverview = () => {
      if (recognitionInstance) recognitionInstance.abort()
      clearInterval(timer)
      phase.value = 'overview'
      loadData(level.value)
    }

    const nextParagraph = () => { currentParaIdx.value++; resetPractice() }
    const finishAll = () => { backToOverview() }

    onMounted(async () => {
      supported.value = !!SpeechRecognition
      await loadData(level.value)
    })

    return {
      phase, article, paragraphs, level, currentParaIdx, supported,
      levelLabels, levelDesc, currentPara,
      fullDisplayTokens, recognizedText, recording, elapsed, done,
      accuracy, correctWords, totalWords, duration, resultClass,
      sentences, sentenceIdx, sentenceDone, sentenceRecognized,
      sentenceResult, sentenceDisplayTokens, showSentenceSummary,
      changeLevel, startPractice, backToOverview, truncate,
      startRecording, stopRecording, resetPractice,
      nextParagraph, finishAll,
      nextSentence, finishAllSentences
    }
  }
}
</script>

<style scoped>
.voice-recite-page { display: flex; flex-direction: column; gap: 16px; }
.loading { text-align: center; padding: 60px; color: #999; }

.overview-header { display: flex; flex-direction: column; gap: 12px; }
.overview-top { display: flex; justify-content: space-between; align-items: center; }
.overview-top h2 { font-size: 22px; color: #333; }
.back-link { text-decoration: none; }
.level-controls { display: flex; align-items: center; gap: 8px; }
.level-badge { font-weight: bold; color: #4f46e5; font-size: 16px; min-width: 120px; text-align: center; }
.hide-info { font-size: 13px; color: #999; margin-left: 8px; }
.browser-warning { background: #fef3c7; color: #92400e; padding: 8px 12px; border-radius: 8px; font-size: 13px; }

.paragraph-list { display: flex; flex-direction: column; gap: 12px; }
.para-card { display: flex; flex-direction: column; gap: 8px; border-left: 4px solid #e0e7ff; }
.para-header { display: flex; align-items: center; gap: 8px; }
.para-num { font-weight: bold; color: #4f46e5; font-size: 14px; }
.badge-accuracy { font-size: 12px; color: #22c55e; background: #f0fdf4; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
.para-preview { font-size: 14px; color: #666; line-height: 1.6; }
.para-modes { display: flex; gap: 16px; font-size: 14px; }
.mode-option { display: flex; align-items: center; gap: 4px; cursor: pointer; padding: 4px 10px; border-radius: 6px; background: #f3f4f6; color: #666; }
.mode-option.active { background: #e0e7ff; color: #4f46e5; font-weight: 600; }
.mode-option input { display: none; }

.practice-header { display: flex; align-items: center; gap: 16px; font-size: 14px; flex-wrap: wrap; }
.practice-level { font-weight: bold; color: #4f46e5; }
.practice-mode { color: #888; font-size: 13px; background: #f3f4f6; padding: 2px 8px; border-radius: 4px; }
.recording-indicator { animation: pulse 1s infinite; color: #ef4444; font-weight: bold; margin-left: auto; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.practice-area { line-height: 2.4; }
.section-label { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; font-weight: bold; color: #666; font-size: 14px; }
.record-controls { display: flex; gap: 8px; }
.record-btn { font-size: 16px; padding: 10px 24px; }

.text-display { font-size: 18px; line-height: 2.8; padding: 12px 16px; background: #fafbff; border-radius: 8px; border: 1px solid #e0e7ff; white-space: pre-wrap; word-break: break-word; }
.recognized-text { color: #666; font-style: italic; }

.token-display { display: inline; white-space: pre; padding: 1px 0; }
.token-display.correct-word { color: #16a34a; background: #f0fdf4; border-radius: 3px; }
.token-display.wrong-word { color: #dc2626; background: #fef2f2; border-radius: 3px; text-decoration: line-through; }
.token-display.missing-word { color: #dc2626; background: #fef2f2; border-radius: 3px; font-style: italic; }
.token-display.extra-word { color: #9333ea; background: #faf5ff; border-radius: 3px; text-decoration: underline; }

.result-area { text-align: center; }
.result-area h3 { margin-bottom: 12px; }
.result-summary { display: flex; justify-content: center; gap: 24px; font-size: 18px; margin-bottom: 16px; flex-wrap: wrap; }
.result-summary .pass { color: #16a34a; font-weight: bold; font-size: 24px; }
.result-summary .fail { color: #dc2626; font-weight: bold; font-size: 24px; }
.result-actions { display: flex; gap: 8px; justify-content: center; }
</style>
