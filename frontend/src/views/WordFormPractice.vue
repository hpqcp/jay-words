<template>
  <div class="wf-page">
    <!-- Phase 0: Tree selector -->
    <div v-if="!selectedSection" class="card">
      <h2>选择词库</h2>
      <div class="tree-browser">
        <div v-for="grade in tree" :key="grade.id" class="tree-item">
          <div class="tree-node" @click="toggleGrade(grade.id)">
            <span class="toggle">{{ expandedGrades.has(grade.id) ? '▼' : '▶' }}</span>
            <span class="node-icon">📁</span>
            <span class="node-name">{{ grade.name }}</span>
          </div>
          <div v-if="expandedGrades.has(grade.id)" class="tree-children">
            <div v-for="lesson in grade.lessons" :key="lesson.id" class="tree-item">
              <div class="tree-node" @click="toggleLesson(lesson.id)">
                <span class="toggle">{{ expandedLessons.has(lesson.id) ? '▼' : '▶' }}</span>
                <span class="node-icon">📂</span>
                <span class="node-name">{{ lesson.name }}</span>
              </div>
              <div v-if="expandedLessons.has(lesson.id)" class="tree-children">
                <div v-for="section in lesson.sections" :key="section.id"
                     class="tree-node section-node"
                     @click="selectSection(grade, lesson, section)">
                  <span class="node-icon">📄</span>
                  <span class="node-name">{{ section.name }}</span>
                  <span class="word-count">{{ section.word_count }}词</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="tree.length === 0" class="empty-hint">
          暂无词库，请先 <router-link to="/manage">导入词库</router-link>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- No word-forms data -->
    <div v-else-if="selectedSection && words.length === 0" class="card empty">
      <p>该章节没有单词或未录入词形数据</p>
      <button class="btn-ghost" @click="backToTree">返回选择</button>
    </div>

    <!-- Phase 1: Study table -->
    <div v-else-if="phase === 'study'" class="card study-card">
      <h2>📐 词形变化学习</h2>
      <p class="section-path">{{ sectionPath }}</p>
      <div class="study-table-wrap">
        <table class="study-table">
          <thead>
            <tr><th>原型</th><th>比较级</th><th>最高级</th><th>中文</th></tr>
          </thead>
          <tbody>
            <tr v-for="w in words" :key="w.id">
              <td class="td-en">{{ w.english }}</td>
              <td class="td-form">{{ w.comparative || '-' }}</td>
              <td class="td-form">{{ w.superlative || '-' }}</td>
              <td class="td-zh">{{ w.chinese }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="filter-panel">
        <div class="filter-group">
          <span class="filter-title">词形类别</span>
          <label class="check-option">
            <input type="checkbox" v-model="enabledForms.comparative" />
            <span>比较级</span>
          </label>
          <label class="check-option">
            <input type="checkbox" v-model="enabledForms.superlative" />
            <span>最高级</span>
          </label>
        </div>
        <div class="filter-group">
          <span class="filter-title">出题方向</span>
          <label class="check-option">
            <input type="checkbox" v-model="enabledDirections.forward" />
            <span>原型 → 词形</span>
          </label>
          <label class="check-option">
            <input type="checkbox" v-model="enabledDirections.reverse" />
            <span>词形 → 原型</span>
          </label>
        </div>
      </div>
      <p v-if="filterHint" class="filter-hint">{{ filterHint }}</p>
      <button class="btn-primary start-btn" :disabled="!canStartQuiz" @click="startQuiz">开始测验 →</button>
      <button class="btn-ghost" @click="backToTree" style="margin-top:8px">返回选择</button>
    </div>

    <!-- Phase 2: Adaptive quiz -->
    <div v-else-if="phase === 'quiz'" class="card question-card">
      <div class="q-header">
        <span class="q-progress">已过 {{ doneCount }} · 剩余 {{ queue.length }}</span>
        <span class="q-type">{{ questionTypeLabel }}</span>
      </div>

      <div class="q-prompt">
        <div class="q-prompt-text">{{ prompt }}</div>
        <div class="q-base-word">{{ displayWord }}</div>
      </div>

      <div class="q-input-area">
        <input
          ref="answerInput"
          v-model="answer"
          placeholder="输入答案..."
          class="q-input"
          :disabled="answered"
          @keyup.enter="submit"
        />
        <button v-if="!answered" class="btn-primary" @click="submit">确认</button>
      </div>

      <div v-if="feedback" class="q-feedback" :class="feedback.correct ? 'fb-correct' : 'fb-wrong'">
        <template v-if="feedback.correct">✅ 正确！</template>
        <template v-else>
          ❌ 正确答案: <strong>{{ feedback.correctAnswer }}</strong> · 已加入待复习
        </template>
        <div v-if="feedback.acceptedAnswers && feedback.acceptedAnswers.length > 1" class="accepted-answers">
          可接受：{{ feedback.acceptedAnswers.join(' / ') }}
        </div>
      </div>

      <button v-if="answered" class="btn-primary" @click="next">下一题 →</button>
    </div>

    <!-- Phase 3: Result -->
    <div v-else-if="phase === 'result'" class="card result-card">
      <h2>📐 词形变化 完成！</h2>
      <div class="result-stats">
        <p>总题数: <strong>{{ totalUnique }}</strong></p>
        <p>首次正确: <strong class="correct">{{ firstCorrect }}</strong></p>
        <p>纠错补答: <strong class="retry">{{ totalUnique - firstCorrect }}</strong></p>
        <p>最终正确率: <strong class="final-pct">100%</strong></p>
      </div>
      <div class="result-actions">
        <button class="btn-primary" @click="restart">再来一次</button>
        <button class="btn-ghost" @click="backToTree">返回选择</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/index.js'

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

export default {
  name: 'WordFormPractice',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const tree = ref([])
    const expandedGrades = ref(new Set())
    const expandedLessons = ref(new Set())
    const selectedSection = ref(null)
    const sectionPath = ref('')
    const words = ref([])
    const loading = ref(true)
    const phase = ref('study') // 'study' | 'quiz' | 'result'
    const queue = ref([])
    const answer = ref('')
    const answered = ref(false)
    const feedback = ref(null)
    const doneCount = ref(0)
    const firstCorrect = ref(0)
    const totalUnique = ref(0)
    const seenCorrectIds = ref(new Set())
    const attemptedIds = ref(new Set())
    const enabledForms = ref({ comparative: true, superlative: true })
    const enabledDirections = ref({ forward: true, reverse: true })

    const answerInput = ref(null)

    const question = computed(() => queue.value[0])
    const questionType = computed(() => question.value ? question.value.type : '')
    const displayWord = computed(() => {
      if (!question.value) return ''
      if (question.value.type === 'to_comparative' || question.value.type === 'to_superlative') return question.value.base
      return question.value.formValue
    })
    const prompt = computed(() => {
      if (!question.value) return ''
      if (question.value.type === 'to_comparative') return '写出比较级：'
      if (question.value.type === 'to_superlative') return '写出最高级：'
      if (question.value.type === 'to_base_from_comp') return '写出原型：'
      if (question.value.type === 'to_base_from_super') return '写出原型：'
      return ''
    })
    const questionTypeLabel = computed(() => {
      if (!question.value) return ''
      if (question.value.type === 'to_comparative') return '原型 → 比较级'
      if (question.value.type === 'to_superlative') return '原型 → 最高级'
      if (question.value.type === 'to_base_from_comp') return '比较级 → 原型'
      if (question.value.type === 'to_base_from_super') return '最高级 → 原型'
      return ''
    })
    const selectedFormCount = computed(() => Number(enabledForms.value.comparative) + Number(enabledForms.value.superlative))
    const selectedDirectionCount = computed(() => Number(enabledDirections.value.forward) + Number(enabledDirections.value.reverse))
    const availableQuestionCount = computed(() => {
      let count = 0
      for (const w of words.value) {
        if (enabledForms.value.comparative && w.comparative) {
          if (enabledDirections.value.forward) count++
          if (enabledDirections.value.reverse) count++
        }
        if (enabledForms.value.superlative && w.superlative) {
          if (enabledDirections.value.forward) count++
          if (enabledDirections.value.reverse) count++
        }
      }
      return count
    })
    const filterHint = computed(() => {
      if (selectedFormCount.value === 0) return '请至少选择一种词形类别'
      if (selectedDirectionCount.value === 0) return '请至少选择一种出题方向'
      if (availableQuestionCount.value === 0) return '当前筛选条件下没有可练题目'
      return ''
    })
    const canStartQuiz = computed(() => availableQuestionCount.value > 0 && !filterHint.value)

    const loadTree = async () => {
      tree.value = await api.getVocabTree()
    }

    const toggleGrade = (id) => {
      if (expandedGrades.value.has(id)) expandedGrades.value.delete(id)
      else expandedGrades.value.add(id)
    }

    const toggleLesson = (id) => {
      if (expandedLessons.value.has(id)) expandedLessons.value.delete(id)
      else expandedLessons.value.add(id)
    }

    const selectSection = async (grade, lesson, section) => {
      selectedSection.value = section
      sectionPath.value = `${grade.name} / ${lesson.name} / ${section.name}`
      loading.value = true
      phase.value = 'study'
      try {
        const all = await api.getSectionWords(section.id)
        words.value = all.filter(w => w.comparative || w.superlative)
      } catch {}
      loading.value = false
    }

    const backToTree = () => {
      selectedSection.value = null
      words.value = []
      phase.value = 'study'
    }

    const buildQueue = () => {
      const seq = []
      for (const w of words.value) {
        if (enabledForms.value.comparative && w.comparative) {
          if (enabledDirections.value.forward) {
            seq.push({ id: `${w.id}_to_comp`, word: w, type: 'to_comparative', base: w.english, formValue: w.comparative })
          }
          if (enabledDirections.value.reverse) {
            seq.push({ id: `${w.id}_from_comp`, word: w, type: 'to_base_from_comp', base: w.english, formValue: w.comparative })
          }
        }
        if (enabledForms.value.superlative && w.superlative) {
          if (enabledDirections.value.forward) {
            seq.push({ id: `${w.id}_to_super`, word: w, type: 'to_superlative', base: w.english, formValue: w.superlative })
          }
          if (enabledDirections.value.reverse) {
            seq.push({ id: `${w.id}_from_super`, word: w, type: 'to_base_from_super', base: w.english, formValue: w.superlative })
          }
        }
      }
      queue.value = shuffle(seq)
      totalUnique.value = queue.value.length
      doneCount.value = 0
      firstCorrect.value = 0
      seenCorrectIds.value = new Set()
      attemptedIds.value = new Set()
    }

    const expectedAnswer = (q) => {
      if (!q) return ''
      if (q.type === 'to_comparative' || q.type === 'to_superlative') return q.formValue
      return q.base
    }

    const startQuiz = () => {
      if (!canStartQuiz.value) return
      buildQueue()
      phase.value = 'quiz'
      resetQuestion()
      nextTick(() => { if (answerInput.value) answerInput.value.focus() })
    }

    const resetQuestion = () => {
      answer.value = ''
      answered.value = false
      feedback.value = null
    }

    const submit = async () => {
      if (answered.value || !answer.value.trim()) return
      answered.value = true
      const q = question.value

      let result
      try {
        result = await api.submitWordForm(q.word.id, q.type, answer.value.trim())
      } catch {
        const correctAnswer = expectedAnswer(q)
        result = { correct: false, correct_answer: correctAnswer, accepted_answers: [correctAnswer] }
      }

      if (result.correct) {
        if (!attemptedIds.value.has(q.id) && !seenCorrectIds.value.has(q.id)) {
          firstCorrect.value++
        }
        seenCorrectIds.value.add(q.id)
        try { await api.submitRecord(q.word.id, 'wordform', 1) } catch {}
      } else {
        attemptedIds.value.add(q.id)
        try { await api.submitRecord(q.word.id, 'wordform', 0) } catch {}
      }

      feedback.value = {
        correct: result.correct,
        correctAnswer: result.correct_answer || expectedAnswer(q),
        acceptedAnswers: result.accepted_answers || []
      }
    }

    const next = () => {
      const q = question.value
      if (!q) return

      if (feedback.value && feedback.value.correct) {
        queue.value.shift()
        doneCount.value++
      } else {
        queue.value.push(queue.value.shift())
      }

      if (queue.value.length === 0) {
        phase.value = 'result'
        return
      }
      resetQuestion()
      nextTick(() => { if (answerInput.value) answerInput.value.focus() })
    }

    const restart = () => {
      phase.value = 'study'
    }

    const loadFromQuery = async () => {
      const wordId = parseInt(route.query.wordId)
      if (wordId) {
        try {
          const word = await api.getWord(wordId)
          selectedSection.value = { id: `word-${wordId}`, name: word.english }
          sectionPath.value = `${word.english} / 单词词形`
          words.value = word.comparative || word.superlative ? [word] : []
          return
        } catch {}
      }

      const sectionId = parseInt(route.query.sectionId)
      if (!sectionId) return
      try {
        const treeData = await api.getVocabTree()
        for (const g of treeData) {
          for (const l of g.lessons) {
            for (const s of l.sections) {
              if (s.id === sectionId) {
                selectedSection.value = s
                sectionPath.value = `${g.name} / ${l.name} / ${s.name}`
                const all = await api.getSectionWords(sectionId)
                words.value = all.filter(w => w.comparative || w.superlative)
                return
              }
            }
          }
        }
      } catch {}
    }

    onMounted(async () => {
      await loadTree()
      await loadFromQuery()
      loading.value = false
    })

    return {
      tree, expandedGrades, expandedLessons, selectedSection, sectionPath,
      words, loading, phase, queue, answer, answered, feedback,
      doneCount, firstCorrect, totalUnique, answerInput,
      enabledForms, enabledDirections, filterHint, canStartQuiz,
      questionType, displayWord, prompt, questionTypeLabel,
      toggleGrade, toggleLesson, selectSection, backToTree,
      startQuiz, submit, next, restart
    }
  }
}
</script>

<style scoped>
.wf-page { max-width: 640px; margin: 0 auto; }
.loading { text-align: center; padding: 60px; color: #999; }
.empty { text-align: center; padding: 40px; }
.empty p { margin-bottom: 16px; color: #999; }

/* Study table */
.study-card { display: flex; flex-direction: column; align-items: center; padding: 24px; }
.study-card h2 { margin-bottom: 4px; color: #14b8a6; }
.section-path { font-size: 13px; color: #999; margin-bottom: 16px; }
.study-table-wrap { width: 100%; overflow-x: auto; margin-bottom: 16px; }
.study-table { width: 100%; border-collapse: collapse; font-size: 15px; }
.study-table th {
  background: #f0fdf4; color: #14b8a6; font-weight: 600;
  padding: 10px 12px; text-align: left; border-bottom: 2px solid #d1fae5;
}
.study-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; }
.study-table tr:last-child td { border-bottom: none; }
.study-table tr:hover td { background: #fafafa; }
.td-en { font-weight: 600; color: #333; }
.td-form { color: #14b8a6; font-family: monospace; }
.td-zh { color: #888; }
.filter-panel {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 8px;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  border: 1px solid #d1fae5;
  border-radius: 8px;
  background: #f8fffc;
}
.filter-title {
  color: #0f766e;
  font-size: 13px;
  font-weight: 700;
  margin-right: 2px;
}
.check-option {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #475569;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}
.check-option input { width: 15px; height: 15px; accent-color: #14b8a6; }
.filter-hint { color: #ef4444; font-size: 13px; margin-bottom: 4px; }
.start-btn { margin-top: 8px; }
.start-btn:disabled { cursor: not-allowed; opacity: 0.45; }

/* Quiz */
.question-card { display: flex; flex-direction: column; gap: 20px; align-items: center; padding: 28px; }
.q-header { display: flex; justify-content: space-between; width: 100%; font-size: 14px; color: #999; }
.q-type { color: #14b8a6; font-weight: bold; }
.q-prompt { text-align: center; }
.q-prompt-text { font-size: 16px; color: #666; margin-bottom: 8px; }
.q-base-word { font-size: 36px; font-weight: bold; color: #333; letter-spacing: 2px; }
.q-input-area { display: flex; gap: 8px; width: 100%; max-width: 400px; }
.q-input { flex: 1; font-size: 20px; text-align: center; padding: 12px; }
.q-feedback { font-size: 18px; padding: 12px 24px; border-radius: 12px; width: 100%; text-align: center; }
.accepted-answers { margin-top: 6px; font-size: 13px; opacity: 0.75; }
.fb-correct { background: #f0fdf4; color: #22c55e; }
.fb-wrong { background: #fef2f2; color: #ef4444; }

/* Result */
.result-card { text-align: center; padding: 40px; }
.result-card h2 { margin-bottom: 20px; color: #14b8a6; }
.result-stats { display: flex; flex-direction: column; gap: 8px; font-size: 16px; margin-bottom: 24px; }
.result-stats .correct { color: #22c55e; }
.result-stats .retry { color: #f59e0b; }
.final-pct { color: #14b8a6; font-size: 20px; }
.result-actions { display: flex; gap: 12px; justify-content: center; }

/* Tree browser */
.tree-browser { margin-top: 12px; }
.tree-item { margin: 2px 0; }
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.tree-node:hover { background: #f0f4ff; }
.toggle { font-size: 10px; color: #999; width: 14px; }
.node-icon { font-size: 16px; }
.node-name { flex: 1; }
.word-count { font-size: 12px; color: #999; }
.tree-children { padding-left: 24px; }
.section-node { margin: 2px 0; }
.empty-hint { padding: 20px; text-align: center; color: #999; }
.empty-hint a { color: #4f46e5; }

@media (max-width: 640px) {
  .filter-panel { grid-template-columns: 1fr; }
}
</style>
