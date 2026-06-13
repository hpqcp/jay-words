const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const api = {
  // Grades
  getGrades: () => request('/grades'),
  createGrade: (name) => request('/grades', { method: 'POST', body: JSON.stringify({ name }) }),
  renameGrade: (id, name) => request(`/grades/${id}`, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteGrade: (id) => request(`/grades/${id}`, { method: 'DELETE' }),

  // Lessons
  getLessons: (gradeId) => request(`/grades/${gradeId}/lessons`),
  createLesson: (gradeId, name) => request(`/grades/${gradeId}/lessons`, { method: 'POST', body: JSON.stringify({ name }) }),
  renameLesson: (id, name) => request(`/lessons/${id}`, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteLesson: (id) => request(`/lessons/${id}`, { method: 'DELETE' }),

  // Sections
  getSections: (lessonId) => request(`/lessons/${lessonId}/sections`),
  createSection: (lessonId, name) => request(`/lessons/${lessonId}/sections`, { method: 'POST', body: JSON.stringify({ name }) }),
  renameSection: (id, name) => request(`/sections/${id}`, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteSection: (id) => request(`/sections/${id}`, { method: 'DELETE' }),

  // Words
  getWords: (sectionId) => request(`/sections/${sectionId}/words`),
  createWord: (sectionId, data) => request(`/sections/${sectionId}/words`, { method: 'POST', body: JSON.stringify(data) }),
  editWord: (id, data) => request(`/words/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteWord: (id) => request(`/words/${id}`, { method: 'DELETE' }),

  // Vocab tree & learning
  getVocabTree: () => request('/vocab/tree'),
  getSectionWords: (sectionId) => request(`/sections/${sectionId}/words`),
  getWord: (wordId) => request(`/words/${wordId}`),

  // Word lookup
  lookupWord: (word) => request(`/lookup?word=${encodeURIComponent(word)}`),

  // Quiz
  submitAnswer: (wordId, answer) => request('/quiz/submit', { method: 'POST', body: JSON.stringify({ word_id: wordId, answer }) }),

  // Wrong words
  getWrongWords: () => request('/wrong/'),
  removeWrongWord: (id) => request(`/wrong/${id}`, { method: 'DELETE' }),
  clearWrongWords: () => request('/wrong/', { method: 'DELETE' }),

  // Version
  getVersion: () => request('/version'),

  // Learning records
  submitRecord: (wordId, mode, result) => request('/records/', { method: 'POST', body: JSON.stringify({ word_id: wordId, mode, result }) }),
  getStats: () => request('/records/stats'),

  // Word Forms
  submitWordForm: (wordId, questionType, answer) => request('/quiz/word-form', { method: 'POST', body: JSON.stringify({ word_id: wordId, question_type: questionType, answer }) }),

  // Articles
  getArticles: () => request('/articles'),
  getArticle: (id) => request(`/articles/${id}`),
  createArticle: (data) => request('/articles', { method: 'POST', body: JSON.stringify(data) }),
  updateArticle: (id, data) => request(`/articles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteArticle: (id) => request(`/articles/${id}`, { method: 'DELETE' }),
  getReciteData: (id, level) => request(`/articles/${id}/recite?level=${level}`),
  submitPractice: (id, data) => request(`/articles/${id}/practice`, { method: 'POST', body: JSON.stringify(data) }),
  getArticleProgress: (id) => request(`/articles/${id}/progress`),
  submitVoicePractice: (id, data) => request(`/articles/${id}/voice-practice`, { method: 'POST', body: JSON.stringify(data) }),
  getVoiceProgress: (id) => request(`/articles/${id}/voice-progress`),

  // Import / Export
  importFile: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/import`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Import failed')
    return res.json()
  },
  exportVocab: (gradeId) => request(`/export${gradeId ? '?grade_id=' + gradeId : ''}`),
}
