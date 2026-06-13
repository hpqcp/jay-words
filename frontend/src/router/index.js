import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Flashcard from '../views/Flashcard.vue'
import Quiz from '../views/Quiz.vue'
import Completion from '../views/Completion.vue'
import Choice from '../views/Choice.vue'
import Manage from '../views/Manage.vue'
import WrongWords from '../views/WrongWords.vue'
import LearningRecords from '../views/LearningRecords.vue'
import Match from '../views/Match.vue'
import Racing from '../views/Racing.vue'
import ArticleManage from '../views/ArticleManage.vue'
import Recite from '../views/Recite.vue'
import VoiceRecite from '../views/VoiceRecite.vue'
import WordFormPractice from '../views/WordFormPractice.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/flashcard', name: 'Flashcard', component: Flashcard },
  { path: '/quiz', name: 'Quiz', component: Quiz },
  { path: '/completion', name: 'Completion', component: Completion },
  { path: '/choice', name: 'Choice', component: Choice },
  { path: '/manage', name: 'Manage', component: Manage },
  { path: '/wrong', name: 'WrongWords', component: WrongWords },
  { path: '/records', name: 'LearningRecords', component: LearningRecords },
  { path: '/match', name: 'Match', component: Match },
  { path: '/racing', name: 'Racing', component: Racing },
  { path: '/articles', name: 'ArticleManage', component: ArticleManage },
  { path: '/recite', name: 'Recite', component: Recite },
  { path: '/voice-recite', name: 'VoiceRecite', component: VoiceRecite },
  { path: '/word-forms', name: 'WordFormPractice', component: WordFormPractice },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
