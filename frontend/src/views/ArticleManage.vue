<template>
  <div class="article-manage">
    <div class="card form-card">
      <div class="form-header">
        <h2>{{ editing ? '编辑文章' : '新增文章' }}</h2>
        <span v-if="draftSaved" class="draft-badge">📝 已暂存</span>
      </div>
      <div v-if="showRestore" class="restore-bar">
        检测到未保存的草稿（{{ draftTime }}）
        <button class="btn-ghost" @click="restoreDraft">恢复</button>
        <button class="btn-ghost" @click="discardDraft">丢弃</button>
      </div>
      <div class="form-row">
        <input v-model="form.title" placeholder="文章标题" class="input-title" @input="saveDraft" />
        <select v-model="form.language" class="input-lang" @change="saveDraft">
          <option value="en">English</option>
          <option value="zh">中文</option>
        </select>
      </div>
      <textarea v-model="form.content" placeholder="请输入文章内容（段落之间用空行分隔）" rows="8" class="input-content" @input="saveDraft"></textarea>
      <div class="form-actions">
        <button class="btn-primary" @click="save">{{ editing ? '保存' : '添加' }}</button>
        <button v-if="editing" class="btn-ghost" @click="cancelEdit">取消</button>
      </div>
    </div>

    <div class="article-list">
      <div v-for="a in articles" :key="a.id" class="card article-card">
        <div class="article-header">
          <h3>{{ a.title }}</h3>
          <span class="lang-badge" :class="a.language">{{ a.language === 'en' ? 'EN' : '中文' }}</span>
        </div>
        <div class="article-meta">
          <span>{{ a.paragraph_count || 0 }} 段</span>
          <span>{{ a.content.length }} 字</span>
        </div>
        <div class="article-actions">
          <button class="btn-primary" @click="startRecite(a)">背诵</button>
          <button class="btn-success" @click="startVoiceRecite(a)">🎤 语音背诵</button>
          <button class="btn-ghost" @click="editArticle(a)">编辑</button>
          <button class="btn-danger" @click="deleteArticle(a)">删除</button>
        </div>
      </div>
      <div v-if="articles.length === 0" class="empty">
        <p>还没有文章，快来添加一篇吧</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/index.js'

const DRAFT_KEY = 'article_draft'

export default {
  name: 'ArticleManage',
  setup() {
    const router = useRouter()
    const articles = ref([])
    const editing = ref(false)
    const editId = ref(null)
    const form = ref({ title: '', content: '', language: 'en' })
    const draftSaved = ref(false)
    const showRestore = ref(false)
    const draftTime = ref('')
    let draftTimer = null

    const load = async () => {
      try {
        articles.value = await api.getArticles()
      } catch {}
    }

    const resetForm = () => {
      form.value = { title: '', content: '', language: 'en' }
      editing.value = false
      editId.value = null
      draftSaved.value = false
    }

    const saveDraft = () => {
      if (editing.value) return
      if (!form.value.title.trim() && !form.value.content.trim()) return
      clearTimeout(draftTimer)
      draftTimer = setTimeout(() => {
        const data = { ...form.value, _savedAt: Date.now() }
        localStorage.setItem(DRAFT_KEY, JSON.stringify(data))
        draftSaved.value = true
      }, 500)
    }

    const restoreDraft = () => {
      const raw = localStorage.getItem(DRAFT_KEY)
      if (!raw) return
      try {
        const data = JSON.parse(raw)
        form.value.title = data.title || ''
        form.value.content = data.content || ''
        form.value.language = data.language || 'en'
        showRestore.value = false
        draftSaved.value = true
      } catch {}
    }

    const discardDraft = () => {
      localStorage.removeItem(DRAFT_KEY)
      showRestore.value = false
      draftSaved.value = false
    }

    const checkDraft = () => {
      const raw = localStorage.getItem(DRAFT_KEY)
      if (!raw) return
      try {
        const data = JSON.parse(raw)
        if (data._savedAt) {
          const d = new Date(data._savedAt)
          draftTime.value = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
        }
        if (data.title || data.content) {
          showRestore.value = true
        }
      } catch {}
    }

    const save = async () => {
      const d = form.value
      if (!d.title.trim() || !d.content.trim()) return
      try {
        if (editing.value) {
          await api.updateArticle(editId.value, d)
        } else {
          await api.createArticle(d)
        }
        discardDraft()
        resetForm()
        await load()
      } catch {}
    }

    const editArticle = (a) => {
      discardDraft()
      form.value = { title: a.title, content: a.content, language: a.language }
      editing.value = true
      editId.value = a.id
    }

    const cancelEdit = () => resetForm()

    const deleteArticle = async (a) => {
      if (!confirm(`确定删除「${a.title}」？`)) return
      try {
        await api.deleteArticle(a.id)
        await load()
      } catch {}
    }

    const startRecite = (a) => {
      router.push({ name: 'Recite', query: { articleId: a.id } })
    }

    const startVoiceRecite = (a) => {
      router.push({ name: 'VoiceRecite', query: { articleId: a.id } })
    }

    onMounted(() => {
      load()
      checkDraft()
    })

    return {
      articles, editing, form, save, editArticle, cancelEdit,
      deleteArticle, startRecite, startVoiceRecite, saveDraft, draftSaved,
      showRestore, draftTime, restoreDraft, discardDraft
    }
  }
}
</script>

<style scoped>
.article-manage { display: flex; flex-direction: column; gap: 20px; }
.form-card h2 { margin-bottom: 12px; font-size: 18px; color: #333; }
.form-row { display: flex; gap: 12px; margin-bottom: 12px; }
.input-title { flex: 1; }
.input-lang { width: 120px; }
.input-content { width: 100%; padding: 12px; border: 2px solid #e0e7ff; border-radius: 8px; font-size: 15px; outline: none; resize: vertical; font-family: inherit; }
.input-content:focus { border-color: #4f46e5; }
.form-actions { display: flex; gap: 8px; margin-top: 12px; }
.article-list { display: flex; flex-direction: column; gap: 12px; }
.article-card { display: flex; flex-direction: column; gap: 8px; }
.article-header { display: flex; align-items: center; gap: 12px; }
.article-header h3 { font-size: 18px; color: #333; }
.lang-badge { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
.lang-badge.en { background: #dbeafe; color: #2563eb; }
.lang-badge.zh { background: #fef3c7; color: #d97706; }
.article-meta { display: flex; gap: 16px; font-size: 13px; color: #999; }
.article-actions { display: flex; gap: 8px; }
.empty { text-align: center; padding: 40px; color: #ccc; font-size: 16px; }
.form-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.form-header h2 { margin-bottom: 0; }
.draft-badge { font-size: 12px; color: #d97706; background: #fef3c7; padding: 2px 8px; border-radius: 4px; }
.restore-bar { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fef3c7; border-radius: 8px; font-size: 13px; color: #92400e; margin-bottom: 12px; }
.restore-bar button { font-size: 12px; padding: 4px 10px; }
</style>
