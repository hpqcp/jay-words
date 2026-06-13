<template>
  <div class="manage-page">
    <h1>词库管理</h1>

    <div class="toolbar">
      <button class="btn-primary" @click="showAddGrade = true">+ 新增年级</button>
      <button class="btn-success" @click="triggerImport">📥 导入文件</button>
      <button class="btn-ghost" @click="exportAll">📤 导出全部</button>
      <input ref="fileInput" type="file" accept=".json,.csv" style="display:none" @change="onImport" />
    </div>

    <div v-if="showAddGrade" class="card inline-form">
      <input v-model="newGradeName" placeholder="年级名称（如 三年级上册）" @keyup.enter="addGrade" />
      <button class="btn-primary" @click="addGrade">确定</button>
      <button class="btn-ghost" @click="showAddGrade = false; newGradeName = ''">取消</button>
    </div>

    <p v-if="importMsg" class="import-msg">{{ importMsg }}</p>

    <div class="manage-layout">
      <div class="tree-panel card">
        <h3>目录</h3>
        <div v-for="grade in tree" :key="grade.id" class="tree-item">
          <div class="tree-node grade-node" :class="{ active: activeGrade === grade.id }">
            <div class="node-label" @click="selectGrade(grade)">
              <span class="toggle" @click.stop="toggleGrade(grade.id)">{{ expandedGrades.has(grade.id) ? '▼' : '▶' }}</span>
              <span>📁 {{ grade.name }}</span>
            </div>
            <div class="node-actions">
              <button class="tiny-btn" @click.stop="editGrade(grade)">✏️</button>
              <button class="tiny-btn danger" @click.stop="delGrade(grade)">🗑️</button>
            </div>
          </div>
          <div v-if="expandedGrades.has(grade.id)" class="tree-children">
            <div v-for="lesson in grade.lessons" :key="lesson.id" class="tree-item">
              <div class="tree-node" :class="{ active: activeLesson === lesson.id }">
                <div class="node-label" @click="selectLesson(grade, lesson)">
                  <span class="toggle" @click.stop="toggleLesson(lesson.id)">{{ expandedLessons.has(lesson.id) ? '▼' : '▶' }}</span>
                  <span>📂 {{ lesson.name }}</span>
                </div>
                <div class="node-actions">
                  <button class="tiny-btn" @click.stop="editLesson(lesson)">✏️</button>
                  <button class="tiny-btn danger" @click.stop="delLesson(lesson)">🗑️</button>
                </div>
              </div>
              <div v-if="expandedLessons.has(lesson.id)" class="tree-children">
                <div v-for="section in lesson.sections" :key="section.id" class="tree-item">
                  <div class="tree-node section-node" :class="{ active: activeSection === section.id }">
                    <div class="node-label" @click="selectSection(grade, lesson, section)">
                      <span>📄 {{ section.name }} ({{ section.word_count }})</span>
                    </div>
                    <div class="node-actions">
                      <button class="tiny-btn" @click.stop="editSection(section)">✏️</button>
                      <button class="tiny-btn danger" @click.stop="delSection(section)">🗑️</button>
                    </div>
                  </div>
                </div>
                <div class="tree-item">
                  <div class="tree-node add-node" @click="addSection(lesson.id)">
                    <span>+ 新增节</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="tree-item">
              <div class="tree-node add-node" @click="addLesson(grade.id)">
                <span>+ 新增课</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="word-panel card">
        <h3 v-if="activeSectionName">{{ activeSectionName }}</h3>
        <h3 v-else class="hint">请从左侧选择一个节</h3>

        <div v-if="activeSection" class="word-toolbar">
          <button class="btn-primary" @click="showAddWord = true">+ 新增单词</button>
        </div>

        <div v-if="showAddWord" class="inline-form">
          <input v-model="newWord.english" placeholder="英文" />
          <button class="btn-ghost lookup-btn" @click="onLookup" :disabled="!newWord.english.trim() || lookupLoading">
            🔍
          </button>
          <input v-model="newWord.chinese" placeholder="中文" />
          <input v-model="newWord.phonetic" placeholder="音标" />
          <div class="form-forms-row">
            <input v-model="newWord.comparative" placeholder="比较级" class="form-input-sm" />
            <input v-model="newWord.superlative" placeholder="最高级" class="form-input-sm" />
          </div>
          <button class="btn-primary" @click="addWord">确定</button>
          <button class="btn-ghost" @click="showAddWord = false; resetNewWord()">取消</button>
          <p v-if="lookupMsg" class="lookup-msg">{{ lookupLoading ? '⏳ 查询中...' : lookupMsg }}</p>
        </div>

        <div v-if="editingWord" class="inline-form">
          <input v-model="editWordForm.english" placeholder="英文" />
          <input v-model="editWordForm.chinese" placeholder="中文" />
          <input v-model="editWordForm.phonetic" placeholder="音标" />
          <div class="form-forms-row">
            <input v-model="editWordForm.comparative" placeholder="比较级" class="form-input-sm" />
            <input v-model="editWordForm.superlative" placeholder="最高级" class="form-input-sm" />
          </div>
          <button class="btn-primary" @click="saveWordEdit">保存</button>
          <button class="btn-ghost" @click="editingWord = null">取消</button>
        </div>

        <div class="word-list">
          <div v-for="(w, i) in words" :key="w.id" class="word-item">
            <span class="word-index">{{ i + 1 }}</span>
            <div class="word-content">
              <strong>{{ w.english }}</strong>
              <span class="word-chinese">{{ w.chinese }}</span>
              <span v-if="w.phonetic" class="word-phonetic">{{ w.phonetic }}</span>
              <div v-if="w.comparative || w.superlative" class="word-forms">
                <span v-if="w.comparative" class="form-badge comp">比较级: {{ w.comparative }}</span>
                <span v-if="w.superlative" class="form-badge super">最高级: {{ w.superlative }}</span>
              </div>
            </div>
            <div class="word-actions">
              <button class="tiny-btn" title="翻卡片" @click="learnWord(w.id, 'flashcard')">🃏</button>
              <button class="tiny-btn" title="拼写" @click="learnWord(w.id, 'quiz')">✍️</button>
              <button class="tiny-btn" title="补全" @click="learnWord(w.id, 'completion')">🔤</button>
              <button class="tiny-btn" title="选择" @click="learnWord(w.id, 'choice')">🔘</button>
              <button v-if="w.comparative || w.superlative" class="tiny-btn" title="词形" @click="practiceWordForm(w.id)">🔁</button>
              <button class="tiny-btn" @click="startEditWord(w)">✏️</button>
              <button class="tiny-btn danger" @click="delWord(w)">🗑️</button>
            </div>
          </div>
          <div v-if="words.length === 0 && activeSection" class="hint">该节暂无单词</div>
        </div>
      </div>
    </div>

    <!-- Edit dialogs -->
    <div v-if="editDialog" class="modal-overlay" @click.self="editDialog = null">
      <div class="modal card">
        <h3>{{ editDialog.title }}</h3>
        <input v-model="editDialog.value" :placeholder="editDialog.placeholder" @keyup.enter="confirmEdit" />
        <div class="modal-actions">
          <button class="btn-primary" @click="confirmEdit">确定</button>
          <button class="btn-ghost" @click="editDialog = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/index.js'

export default {
  name: 'Manage',
  setup() {
    const router = useRouter()
    const tree = ref([])
    const activeGrade = ref(null)
    const activeLesson = ref(null)
    const activeSection = ref(null)
    const activeSectionName = ref('')
    const words = ref([])
    const expandedGrades = ref(new Set())
    const expandedLessons = ref(new Set())
    const showAddGrade = ref(false)
    const newGradeName = ref('')
    const importMsg = ref('')
    const fileInput = ref(null)
    const showAddWord = ref(false)
    const newWord = ref({ english: '', chinese: '', phonetic: '', comparative: '', superlative: '' })

    const editingWord = ref(null)
    const editWordForm = ref({ english: '', chinese: '', phonetic: '', comparative: '', superlative: '' })
    const editDialog = ref(null)
    const lookupLoading = ref(false)
    const lookupMsg = ref('')

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

    const selectGrade = async (grade) => {
      activeGrade.value = grade.id
      activeLesson.value = null
      activeSection.value = null
      activeSectionName.value = ''
      words.value = []
      if (!expandedGrades.value.has(grade.id)) expandedGrades.value.add(grade.id)
      // Ensure lessons are loaded
      grade.lessons = grade.lessons || []
    }

    const selectLesson = async (grade, lesson) => {
      activeGrade.value = grade.id
      activeLesson.value = lesson.id
      activeSection.value = null
      activeSectionName.value = ''
      words.value = []
      if (!expandedGrades.value.has(grade.id)) expandedGrades.value.add(grade.id)
      if (!expandedLessons.value.has(lesson.id)) expandedLessons.value.add(lesson.id)
    }

    const selectSection = async (grade, lesson, section) => {
      activeGrade.value = grade.id
      activeLesson.value = lesson.id
      activeSection.value = section.id
      activeSectionName.value = `${grade.name} / ${lesson.name} / ${section.name}`
      words.value = await api.getWords(section.id)
      if (!expandedGrades.value.has(grade.id)) expandedGrades.value.add(grade.id)
      if (!expandedLessons.value.has(lesson.id)) expandedLessons.value.add(lesson.id)
    }

    // Grade CRUD
    const addGrade = async () => {
      if (!newGradeName.value.trim()) return
      await api.createGrade(newGradeName.value.trim())
      newGradeName.value = ''
      showAddGrade.value = false
      await loadTree()
    }

    const editGrade = (grade) => {
      editDialog.value = { type: 'grade', id: grade.id, value: grade.name, title: '编辑年级', placeholder: '年级名称' }
    }

    const delGrade = async (grade) => {
      if (!confirm(`确定删除"${grade.name}"吗？将删除该年级下所有内容。`)) return
      await api.deleteGrade(grade.id)
      await loadTree()
      if (activeGrade.value === grade.id) { activeGrade.value = null; words.value = [] }
    }

    // Lesson CRUD
    const addLesson = async (gradeId) => {
      const name = prompt('请输入课名称：')
      if (!name) return
      await api.createLesson(gradeId, name)
      await loadTree()
      if (!expandedGrades.value.has(gradeId)) expandedGrades.value.add(gradeId)
    }

    const editLesson = (lesson) => {
      editDialog.value = { type: 'lesson', id: lesson.id, value: lesson.name, title: '编辑课', placeholder: '课名称' }
    }

    const delLesson = async (lesson) => {
      if (!confirm(`确定删除"${lesson.name}"吗？`)) return
      await api.deleteLesson(lesson.id)
      await loadTree()
      if (activeLesson.value === lesson.id) { activeLesson.value = null; words.value = [] }
    }

    // Section CRUD
    const addSection = async (lessonId) => {
      const name = prompt('请输入节名称：')
      if (!name) return
      await api.createSection(lessonId, name)
      await loadTree()
      if (!expandedLessons.value.has(lessonId)) expandedLessons.value.add(lessonId)
    }

    const editSection = (section) => {
      editDialog.value = { type: 'section', id: section.id, value: section.name, title: '编辑节', placeholder: '节名称' }
    }

    const delSection = async (section) => {
      if (!confirm(`确定删除"${section.name}"吗？`)) return
      await api.deleteSection(section.id)
      await loadTree()
      if (activeSection.value === section.id) { activeSection.value = null; words.value = [] }
    }

    // Word lookup
    const onLookup = async () => {
      const eng = newWord.value.english.trim()
      if (!eng) return
      lookupLoading.value = true
      lookupMsg.value = '查询中...'
      try {
        const data = await api.lookupWord(eng)
        if (data.chinese) newWord.value.chinese = data.chinese
        if (data.phonetic) newWord.value.phonetic = data.phonetic
        if (!newWord.value.comparative && data.comparative) newWord.value.comparative = data.comparative
        if (!newWord.value.superlative && data.superlative) newWord.value.superlative = data.superlative
        const hasForms = data.comparative || data.superlative
        if (data.chinese && hasForms) lookupMsg.value = '✅ 已自动获取释义、音标和词形'
        else if (data.chinese) lookupMsg.value = '✅ 已自动获取释义和音标'
        else if (hasForms) lookupMsg.value = '✅ 已自动生成词形，请补充中文'
        else lookupMsg.value = '⚠️ 未找到翻译，请手动输入'
      } catch {
        lookupMsg.value = '⚠️ 网络异常，请手动输入'
      } finally {
        lookupLoading.value = false
      }
    }

    const resetNewWord = () => { newWord.value = { english: '', chinese: '', phonetic: '', comparative: '', superlative: '' }; lookupMsg.value = '' }

    // Word CRUD
    const addWord = async () => {
      if (!newWord.value.english.trim() || !newWord.value.chinese.trim()) return
      await api.createWord(activeSection.value, {
        english: newWord.value.english.trim(),
        chinese: newWord.value.chinese.trim(),
        phonetic: newWord.value.phonetic.trim(),
        comparative: newWord.value.comparative.trim(),
        superlative: newWord.value.superlative.trim()
      })
      resetNewWord()
      showAddWord.value = false
      words.value = await api.getWords(activeSection.value)
      await loadTree()
    }

    const startEditWord = (w) => {
      editingWord.value = w.id
      editWordForm.value = { english: w.english, chinese: w.chinese, phonetic: w.phonetic || '', comparative: w.comparative || '', superlative: w.superlative || '' }
    }

    const saveWordEdit = async () => {
      await api.editWord(editingWord.value, editWordForm.value)
      editingWord.value = null
      words.value = await api.getWords(activeSection.value)
    }

    const delWord = async (w) => {
      if (!confirm(`确定删除"${w.english}"吗？`)) return
      await api.deleteWord(w.id)
      words.value = await api.getWords(activeSection.value)
      await loadTree()
    }

    const learnWord = (wordId, mode) => {
      const name = mode.charAt(0).toUpperCase() + mode.slice(1)
      router.push({ name, query: { wordId } })
    }

    const practiceWordForm = (wordId) => {
      router.push({ name: 'WordFormPractice', query: { wordId } })
    }

    // Import / Export
    const triggerImport = () => { fileInput.value.click() }

    const onImport = async (e) => {
      const file = e.target.files[0]
      if (!file) return
      try {
        const result = await api.importFile(file)
        importMsg.value = `✅ 导入成功：${result.grades} 年级, ${result.lessons} 课, ${result.sections} 节, ${result.words} 词`
        await loadTree()
      } catch (err) {
        importMsg.value = '❌ 导入失败：' + err.message
      }
      e.target.value = ''
    }

    const exportAll = async () => {
      const data = await api.exportVocab()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'vocab_export.json'
      a.click()
      URL.revokeObjectURL(url)
    }

    const confirmEdit = async () => {
      const d = editDialog.value
      if (!d || !d.value.trim()) return
      if (d.type === 'grade') await api.renameGrade(d.id, d.value.trim())
      else if (d.type === 'lesson') await api.renameLesson(d.id, d.value.trim())
      else if (d.type === 'section') await api.renameSection(d.id, d.value.trim())
      editDialog.value = null
      await loadTree()
    }

    onMounted(loadTree)

    return {
      tree, activeGrade, activeLesson, activeSection, activeSectionName, words,
      expandedGrades, expandedLessons,
      showAddGrade, newGradeName, importMsg, fileInput,
      showAddWord, newWord, editingWord, editWordForm, editDialog, lookupLoading, lookupMsg,
      toggleGrade, toggleLesson,
      selectGrade, selectLesson, selectSection,
      addGrade, editGrade, delGrade,
      addLesson, editLesson, delLesson,
      addSection, editSection, delSection,
      addWord, resetNewWord, startEditWord, saveWordEdit, delWord, learnWord, practiceWordForm, onLookup,
      triggerImport, onImport, exportAll, confirmEdit
    }
  }
}
</script>

<style scoped>
.manage-page { max-width: 100%; }
.manage-page h1 { margin-bottom: 16px; color: #333; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.import-msg { color: #22c55e; font-size: 14px; margin-bottom: 12px; }
.manage-layout { display: flex; gap: 20px; align-items: flex-start; }
.tree-panel { width: 320px; min-width: 260px; flex-shrink: 0; max-height: 70vh; overflow-y: auto; }
.tree-panel h3 { margin-bottom: 12px; color: #666; font-size: 14px; }
.word-panel { flex: 1; min-height: 300px; }
.word-panel h3 { margin-bottom: 16px; }
.word-panel h3.hint { color: #999; font-weight: normal; }
.tree-item { margin: 2px 0; }
.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
}
.tree-node:hover { background: #f0f4ff; }
.tree-node.active { background: #e0e7ff; color: #4f46e5; font-weight: 600; }
.grade-node { font-weight: 600; }
.section-node { font-size: 13px; }
.add-node { color: #22c55e; font-size: 13px; }
.node-label { display: flex; align-items: center; gap: 4px; flex: 1; }
.toggle { font-size: 10px; color: #999; width: 14px; }
.node-actions { display: flex; gap: 2px; }
.tree-children { padding-left: 20px; }
.tiny-btn {
  background: none; border: none; cursor: pointer; padding: 2px 4px; font-size: 12px; opacity: 0.5;
}
.tiny-btn:hover { opacity: 1; }
.tiny-btn.danger:hover { color: #ef4444; }
.inline-form { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.inline-form input { flex: 1; min-width: 100px; }
.word-toolbar { margin-bottom: 12px; }
.word-list { margin-top: 8px; }
.word-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
}
.word-item:last-child { border-bottom: none; }
.word-index { color: #ccc; font-size: 13px; width: 24px; }
.word-content { flex: 1; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.word-chinese { color: #666; }
.word-phonetic { color: #bbb; font-size: 13px; }
.word-actions { display: flex; gap: 4px; }
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.modal { min-width: 300px; }
.modal h3 { margin-bottom: 16px; }
.modal input { width: 100%; margin-bottom: 16px; }
.modal-actions { display: flex; gap: 12px; justify-content: flex-end; }
.lookup-btn { font-size: 18px; padding: 8px 12px; }
.lookup-msg { font-size: 12px; color: #888; width: 100%; margin: 4px 0 0; }
.form-forms-row { display: flex; gap: 8px; width: 100%; }
.form-input-sm { flex: 1; min-width: 80px; font-size: 13px; }
.word-forms { display: flex; gap: 6px; width: 100%; margin-top: 2px; }
.form-badge { font-size: 11px; padding: 1px 6px; border-radius: 4px; }
.form-badge.comp { background: #dbeafe; color: #2563eb; }
.form-badge.super { background: #fef3c7; color: #d97706; }
</style>
