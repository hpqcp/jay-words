<template>
  <div class="home">
    <div class="hero">
      <h1>📚 小杰背单词</h1>
      <p>选择词库和学习模式开始背单词吧！</p>
    </div>

    <div class="card mb">
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
                     :class="{ active: selectedSection === section.id }"
                     @click="selectSection(section)">
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

    <div v-if="selectedSection" class="card">
      <h2>选择模式</h2>
      <p class="selected-hint">当前：{{ selectedSection.path }}</p>
      <div class="mode-buttons">
        <button class="btn-primary mode-btn" @click="startFlashcard">
          🃏 翻卡片学习
        </button>
        <button class="mode-btn btn-choice" @click="startChoice">
          🔘 选择正确
        </button>
        <button class="mode-btn btn-completion" @click="startCompletion">
          🔤 补全单词
        </button>
        <button class="btn-success mode-btn" @click="startQuiz">
          ✍️ 拼写测验
        </button>
        <button class="mode-btn btn-match" @click="startMatch">
          🔗 连连线
        </button>
        <button class="mode-btn btn-racing" @click="startRacing">
          🏎️ 单词赛车
        </button>
      </div>
    </div>

    <div class="card mt">
      <h2>快速导入</h2>
      <p class="hint">支持 JSON 或 CSV 格式的词库文件</p>
      <input type="file" accept=".json,.csv" @change="onImport" class="file-input" />
      <p v-if="importResult" class="import-result">{{ importResult }}</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/index.js'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const tree = ref([])
    const expandedGrades = ref(new Set())
    const expandedLessons = ref(new Set())
    const selectedSection = ref(null)
    const importResult = ref('')

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

    const selectSection = (section) => {
      selectedSection.value = section
    }

    const startFlashcard = () => {
      router.push({ name: 'Flashcard', query: { sectionId: selectedSection.value.id } })
    }

    const startQuiz = () => {
      router.push({ name: 'Quiz', query: { sectionId: selectedSection.value.id } })
    }

    const startCompletion = () => {
      router.push({ name: 'Completion', query: { sectionId: selectedSection.value.id } })
    }

    const startChoice = () => {
      router.push({ name: 'Choice', query: { sectionId: selectedSection.value.id } })
    }

    const startMatch = () => {
      router.push({ name: 'Match', query: { sectionId: selectedSection.value.id } })
    }

    const startRacing = () => {
      router.push({ name: 'Racing', query: { sectionId: selectedSection.value.id } })
    }

    const onImport = async (e) => {
      const file = e.target.files[0]
      if (!file) return
      try {
        const result = await api.importFile(file)
        importResult.value = `导入成功：${result.grades} 个年级，${result.lessons} 课，${result.sections} 节，${result.words} 个单词`
        await loadTree()
      } catch (err) {
        importResult.value = '导入失败：' + err.message
      }
    }

    onMounted(loadTree)

    return { tree, expandedGrades, expandedLessons, selectedSection, toggleGrade, toggleLesson, selectSection, startFlashcard, startQuiz, startCompletion, startChoice, startMatch, startRacing, onImport, importResult }
  }
}
</script>

<style scoped>
.home { max-width: 700px; margin: 0 auto; }
.hero { text-align: center; margin-bottom: 24px; }
.hero h1 { font-size: 32px; color: #4f46e5; margin-bottom: 8px; }
.hero p { color: #888; font-size: 16px; }
.mb { margin-bottom: 16px; }
.mt { margin-top: 16px; }
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
.tree-node.active { background: #e0e7ff; color: #4f46e5; font-weight: 600; }
.toggle { font-size: 10px; color: #999; width: 14px; }
.node-icon { font-size: 16px; }
.node-name { flex: 1; }
.word-count { font-size: 12px; color: #999; }
.tree-children { padding-left: 24px; }
.section-node { margin: 2px 0; }
.empty-hint { padding: 20px; text-align: center; color: #999; }
.empty-hint a { color: #4f46e5; }
.selected-hint { color: #666; margin: 8px 0; font-size: 14px; }
.mode-buttons { display: flex; gap: 16px; margin-top: 16px; }
.mode-btn { flex: 1; padding: 16px; font-size: 18px; }
.btn-completion { background: #f59e0b; color: #fff; }
.btn-completion:hover { opacity: 0.85; }
.btn-choice { background: #ec4899; color: #fff; }
.btn-choice:hover { opacity: 0.85; }
.btn-match { background: #8b5cf6; color: #fff; }
.btn-match:hover { opacity: 0.85; }
.btn-racing { background: #ef4444; color: #fff; }
.btn-racing:hover { opacity: 0.85; }
.hint { color: #888; font-size: 13px; margin: 4px 0 12px; }
.file-input { display: block; margin: 8px 0; }
.import-result { color: #22c55e; font-size: 14px; margin-top: 8px; }
</style>
