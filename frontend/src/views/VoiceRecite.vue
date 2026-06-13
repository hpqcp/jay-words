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
            <span v-if="p.voiceProgress" class="badge-accuracy">
              最高 {{ (p.voiceProgress.best_accuracy * 100).toFixed(0) }}%
            </span>
          </div>
          <div v-if="p.voiceProgress" class="voice-progress">
            <span>最近 {{ (p.voiceProgress.latest_accuracy * 100).toFixed(0) }}%</span>
            <span>练习 {{ p.voiceProgress.attempts }} 次</span>
            <span v-if="p.voiceProgress.best_duration_ms">最佳用时 {{ Math.round(p.voiceProgress.best_duration_ms / 1000) }}s</span>
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
        <span v-else-if="recognitionStatus" class="recognition-status">{{ recognitionStatus }}</span>
      </div>
      <div v-if="recognitionError" class="card browser-warning">
        {{ recognitionError }}
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
                ✅ 结束并纠错
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
        <div v-if="correctedText" class="card practice-area">
          <div class="section-label">纠错后</div>
          <div class="text-display corrected-text">{{ correctedText }}</div>
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
                ✅ 结束并纠错
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
        <div v-if="sentenceCorrectedText" class="card practice-area">
          <div class="section-label">纠错后</div>
          <div class="text-display corrected-text">{{ sentenceCorrectedText }}</div>
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
import {
  LEVEL_CONFIG,
  buildDisplayTokens,
  compareWithCorrection,
  selectHiddenByLevel,
  splitTokenSentences,
} from '../utils/voiceRecite.js'

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

    const levelLabels = Object.fromEntries(Object.entries(LEVEL_CONFIG).map(([k, v]) => [k, v.label]))
    const levelDesc = Object.fromEntries(Object.entries(LEVEL_CONFIG).map(([k, v]) => [k, v.description]))

    const currentPara = computed(() => paragraphs.value[currentParaIdx.value] || {})

    const loadData = async (lvl) => {
      const aid = parseInt(route.query.articleId)
      if (!aid) return
      try {
        const data = await api.getReciteData(aid, lvl)
        article.value = data
        level.value = data.level
        paragraphs.value = data.paragraphs.map((p) => ({ ...p, mode: 'full', voiceProgress: null }))
        const progress = await api.getVoiceProgress(aid)
        for (const p of progress) {
          const para = paragraphs.value[p.paragraph_index]
          if (para && p.level === level.value) para.voiceProgress = p
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
    const correctedText = ref('')
    const accuracy = ref(0)
    const correctWords = ref(0)
    const totalWords = ref(0)
    const duration = ref(0)
    const fullDisplayTokens = ref([])
    const recognitionStatus = ref('')
    const recognitionError = ref('')
    const resultClass = computed(() => accuracy.value >= 0.8 ? 'pass' : 'fail')

    let recognitionInstance = null
    let timer = null
    let startTime = 0
    let practiceStartTime = 0
    let finalTranscript = ''
    let resultFinalized = false
    let manualEnding = false
    let recognitionSessionId = 0

    const getSpeechErrorMessage = (event) => {
      const code = event && event.error
      if (code === 'not-allowed' || code === 'service-not-allowed') return '麦克风权限被拒绝，请允许浏览器使用麦克风后重试。'
      if (code === 'no-speech') return '没有识别到语音，请靠近麦克风后重试。'
      if (code === 'audio-capture') return '没有检测到可用麦克风，请检查设备连接。'
      if (code === 'network') return '语音识别网络异常，请稍后重试。'
      return '语音识别失败，请重新练习。'
    }

    const finishRecognition = (reason = 'manual') => {
      if (reason !== 'manual' && !manualEnding) return
      if (resultFinalized) return
      resultFinalized = true
      recording.value = false
      clearInterval(timer)
      recognitionInstance = null

      const text = currentPara.value.mode === 'sentence' ? sentenceRecognized.value.trim() : recognizedText.value.trim()
      if (!text) {
        recognitionStatus.value = '未识别到内容'
        recognitionError.value = recognitionError.value || '未识别到朗读内容，请重新录音。'
        return
      }
      recognitionStatus.value = '识别完成'
      if (currentPara.value.mode === 'sentence') doSentenceCompare()
      else doCompare()
    }

    const renderFullPrompt = () => {
      const para = currentPara.value
      if (!para || para.mode !== 'full') return
      const tokens = para.tokens || [para.text]
      const hiddenIndices = para.hidden_indices || selectHiddenByLevel(tokens, article.value.language, level.value)
      fullDisplayTokens.value = buildDisplayTokens(tokens, hiddenIndices, {}, level.value, article.value.language)
    }

    const startRecording = () => {
      if (!SpeechRecognition) {
        supported.value = false
        recognitionError.value = '当前浏览器不支持语音识别，请使用 Chrome 或 Edge。'
        return
      }
      if (recognitionInstance) {
        const oldInstance = recognitionInstance
        recognitionInstance = null
        try { oldInstance.abort() } catch {}
      }
      recognitionStatus.value = '正在听写'
      recognitionError.value = ''
      resultFinalized = false
      manualEnding = false
      recognitionSessionId += 1
      const sessionId = recognitionSessionId
      finalTranscript = ''
      if (currentPara.value.mode === 'full') {
        recognizedText.value = ''
        correctedText.value = ''
        done.value = false
      } else {
        sentenceRecognized.value = ''
        sentenceCorrectedText.value = ''
        sentenceResult.value = null
        sentenceDone.value = false
      }
      elapsed.value = 0

      const startRecognitionInstance = () => {
        const recog = new SpeechRecognition()
        recog.lang = article.value.language === 'zh' ? 'zh-CN' : 'en-US'
        recog.continuous = true
        recog.interimResults = true
        recog.maxAlternatives = 1

        recog.onresult = (e) => {
          if (sessionId !== recognitionSessionId) return
          let interim = ''
          for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) finalTranscript += e.results[i][0].transcript + ' '
            else interim += e.results[i][0].transcript
          }
          const text = (finalTranscript + interim).trim()
          if (currentPara.value.mode === 'full') recognizedText.value = text
          else sentenceRecognized.value = text
        }

        recog.onend = () => {
          if (sessionId !== recognitionSessionId) return
          if (resultFinalized || manualEnding) return
          recognitionInstance = null
          if (!recording.value) return
          recognitionStatus.value = '正在听写'
          setTimeout(() => {
            if (sessionId !== recognitionSessionId || !recording.value || resultFinalized || manualEnding) return
            startRecognitionInstance()
          }, 120)
        }

        recog.onerror = (event) => {
          if (sessionId !== recognitionSessionId) return
          if (event && event.error === 'no-speech') {
            recognitionStatus.value = '正在听写'
            return
          }
          recognitionError.value = getSpeechErrorMessage(event)
          if (event && ['not-allowed', 'service-not-allowed', 'audio-capture', 'network'].includes(event.error)) {
            resultFinalized = true
            manualEnding = true
            recording.value = false
            clearInterval(timer)
            recognitionInstance = null
          }
        }

        recognitionInstance = recog
        try {
          recog.start()
        } catch {
          recognitionError.value = '语音识别启动失败，请重新练习。'
          resultFinalized = true
          manualEnding = true
          recording.value = false
          clearInterval(timer)
          recognitionInstance = null
        }
      }

      recording.value = true
      startTime = Date.now()
      clearInterval(timer)
      timer = setInterval(() => { elapsed.value = Math.floor((Date.now() - startTime) / 1000) }, 200)
      startRecognitionInstance()
    }

    const stopRecording = () => {
      if (resultFinalized) return
      manualEnding = true
      recognitionStatus.value = '正在纠错并评分...'
      const stoppedInstance = recognitionInstance
      finishRecognition('manual')
      if (stoppedInstance) {
        try {
          stoppedInstance.stop()
        } catch {
          try { stoppedInstance.abort() } catch {}
        }
      }
    }

    const doCompare = () => {
      const para = currentPara.value
      const tokens = para.tokens || [para.text]
      const hiddenIndices = para.hidden_indices || selectHiddenByLevel(tokens, article.value.language, level.value)
      const result = compareWithCorrection(tokens, recognizedText.value, article.value.language)
      correctedText.value = result.correctedText
      fullDisplayTokens.value = buildDisplayTokens(tokens, hiddenIndices, result.tokenStatuses, level.value, article.value.language)
      accuracy.value = result.accuracy
      correctWords.value = result.correct
      totalWords.value = result.total
      duration.value = elapsed.value
      done.value = true
      submitFullResult(result)
    }

    const submitFullResult = (result) => {
      return api.submitVoicePractice(article.value.id, {
        paragraph_index: currentParaIdx.value, mode: 'full', level: level.value,
        total_words: result.total, correct_words: result.correct,
        accuracy: result.accuracy, duration_ms: elapsed.value * 1000
      }).catch(() => {})
    }

    const resetPractice = () => {
      recognizedText.value = ''
      correctedText.value = ''
      fullDisplayTokens.value = []
      recognitionStatus.value = ''
      recognitionError.value = ''
      accuracy.value = 0; correctWords.value = 0; totalWords.value = 0
      duration.value = 0; done.value = false; elapsed.value = 0
      recording.value = false
      clearInterval(timer)
      sentenceIdx.value = 0; sentenceDone.value = false
      sentenceRecognized.value = ''; sentenceCorrectedText.value = ''; sentenceResult.value = null
      showSentenceSummary.value = false
      sentenceResults.value = []
      resultFinalized = true
      manualEnding = true
      recognitionSessionId += 1
      if (recognitionInstance) { recognitionInstance.abort(); recognitionInstance = null }
      renderFullPrompt()
    }

    // ===== Sentence mode =====
    const sentences = ref([])
    const sentenceIdx = ref(0)
    const sentenceDone = ref(false)
    const sentenceRecognized = ref('')
    const sentenceCorrectedText = ref('')
    const sentenceResult = ref(null)
    const showSentenceSummary = ref(false)
    const sentenceResults = ref([])

    const sentenceDisplayTokens = computed(() => {
      if (!sentences.value.length) return []
      const s = sentences.value[sentenceIdx.value]
      if (!s) return []
      const hiddenIndices = s.hidden_indices || selectHiddenByLevel(s.tokens, article.value.language, level.value)
      const statuses = sentenceResult.value ? sentenceResult.value.tokenStatuses : {}
      return buildDisplayTokens(s.tokens, hiddenIndices, statuses, level.value, article.value.language)
    })

    const doSentenceCompare = () => {
      const s = sentences.value[sentenceIdx.value]
      if (!s) return
      const result = compareWithCorrection(s.tokens, sentenceRecognized.value, article.value.language)
      sentenceCorrectedText.value = result.correctedText
      sentenceResult.value = result
      sentenceResults.value.push(result)
      sentenceDone.value = true
      submitSentenceResult(result)
    }

    const submitSentenceResult = (result) => {
      return api.submitVoicePractice(article.value.id, {
        paragraph_index: currentParaIdx.value, sentence_index: sentenceIdx.value,
        mode: 'sentence', level: level.value,
        total_words: result.total, correct_words: result.correct,
        accuracy: result.accuracy, duration_ms: elapsed.value * 1000
      }).catch(() => {})
    }

    const nextSentence = () => {
      sentenceIdx.value++
      sentenceDone.value = false
      sentenceRecognized.value = ''
      sentenceCorrectedText.value = ''
      sentenceResult.value = null
      recognitionStatus.value = ''
      recognitionError.value = ''
    }

    const finishAllSentences = () => {
      showSentenceSummary.value = true
      let cor = 0, tot = 0
      for (const r of sentenceResults.value) { cor += r.correct; tot += r.total }
      accuracy.value = tot > 0 ? cor / tot : 0
      correctWords.value = cor
      totalWords.value = tot
      duration.value = Math.floor((Date.now() - practiceStartTime) / 1000)
      api.submitVoicePractice(article.value.id, {
        paragraph_index: currentParaIdx.value, mode: 'sentence', level: level.value,
        total_words: tot, correct_words: cor, accuracy: accuracy.value, duration_ms: duration.value * 1000
      }).catch(() => {})
    }

    const prepareSentenceMode = (para) => {
      if (para && para.mode === 'sentence') {
        sentences.value = splitTokenSentences(para.tokens || [para.text], article.value.language, para.text)
          .map(s => ({ ...s, hidden_indices: selectHiddenByLevel(s.tokens, article.value.language, level.value) }))
      } else {
        sentences.value = []
      }
    }

    const startPractice = (idx) => {
      currentParaIdx.value = idx
      const para = paragraphs.value[idx]
      prepareSentenceMode(para)
      practiceStartTime = Date.now()
      phase.value = 'practice'
      resetPractice()
    }

    const backToOverview = () => {
      resultFinalized = true
      manualEnding = true
      recognitionSessionId += 1
      recording.value = false
      if (recognitionInstance) recognitionInstance.abort()
      clearInterval(timer)
      phase.value = 'overview'
      loadData(level.value)
    }

    const nextParagraph = () => {
      currentParaIdx.value++
      prepareSentenceMode(paragraphs.value[currentParaIdx.value])
      practiceStartTime = Date.now()
      resetPractice()
    }
    const finishAll = () => { backToOverview() }

    onMounted(async () => {
      supported.value = !!SpeechRecognition
      await loadData(level.value)
    })

    return {
      phase, article, paragraphs, level, currentParaIdx, supported,
      levelLabels, levelDesc, currentPara,
      fullDisplayTokens, recognizedText, correctedText, recording, elapsed, done,
      recognitionStatus, recognitionError,
      accuracy, correctWords, totalWords, duration, resultClass,
      sentences, sentenceIdx, sentenceDone, sentenceRecognized, sentenceCorrectedText,
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
.voice-progress { display: flex; gap: 12px; flex-wrap: wrap; font-size: 12px; color: #64748b; }
.para-preview { font-size: 14px; color: #666; line-height: 1.6; }
.para-modes { display: flex; gap: 16px; font-size: 14px; }
.mode-option { display: flex; align-items: center; gap: 4px; cursor: pointer; padding: 4px 10px; border-radius: 6px; background: #f3f4f6; color: #666; }
.mode-option.active { background: #e0e7ff; color: #4f46e5; font-weight: 600; }
.mode-option input { display: none; }

.practice-header { display: flex; align-items: center; gap: 16px; font-size: 14px; flex-wrap: wrap; }
.practice-level { font-weight: bold; color: #4f46e5; }
.practice-mode { color: #888; font-size: 13px; background: #f3f4f6; padding: 2px 8px; border-radius: 4px; }
.recording-indicator { animation: pulse 1s infinite; color: #ef4444; font-weight: bold; margin-left: auto; }
.recognition-status { color: #64748b; font-size: 13px; margin-left: auto; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.practice-area { line-height: 2.4; }
.section-label { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; font-weight: bold; color: #666; font-size: 14px; }
.record-controls { display: flex; gap: 8px; }
.record-btn { font-size: 16px; padding: 10px 24px; }

.text-display { font-size: 18px; line-height: 2.8; padding: 12px 16px; background: #fafbff; border-radius: 8px; border: 1px solid #e0e7ff; white-space: pre-wrap; word-break: break-word; }
.recognized-text { color: #666; font-style: italic; }
.corrected-text { color: #0f766e; background: #f0fdfa; border-color: #99f6e4; }

.token-display { display: inline; white-space: pre; padding: 1px 0; }
.token-display.correct-word { color: #16a34a; background: #f0fdf4; border-radius: 3px; }
.token-display.corrected-word { color: #0f766e; background: #ccfbf1; border-radius: 3px; }
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
