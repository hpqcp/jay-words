export const LEVEL_CONFIG = {
  1: { label: '跟读', description: '全文可见', ratio: 0, firstPerSentence: false, hideAll: false },
  2: { label: '简单', description: '每句隐藏 1 词', ratio: 0, firstPerSentence: true, hideAll: false },
  3: { label: '普通', description: '每句隐藏 30%', ratio: 0.3, firstPerSentence: false, hideAll: false },
  4: { label: '困难', description: '每句隐藏 70%', ratio: 0.7, firstPerSentence: false, hideAll: false },
  5: { label: '默写', description: '全文隐藏', ratio: 1, firstPerSentence: false, hideAll: true },
}

export function isWordToken(token, language) {
  const text = String(token || '').trim()
  if (!text) return false
  if (language === 'zh') return /[\u4e00-\u9fffA-Za-z0-9]/.test(text)
  return /^\w+(?:'\w+)?$/.test(text)
}

function isSentenceEnd(token) {
  return /[。！？.!?\n]$/.test(String(token || ''))
}

function normalizeToken(token) {
  return String(token || '')
    .trim()
    .replace(/^[^\w\u4e00-\u9fff']+|[^\w\u4e00-\u9fff']+$/g, '')
    .toLowerCase()
}

const CHINESE_CONFUSION_GROUPS = [
  '的地得',
  '他她它',
  '在再',
  '做作坐',
  '那哪',
  '了啦',
  '吗嘛',
  '已以',
  '又有',
  '只知',
  '是事',
  '和合',
  '跟根',
  '个各',
  '声生',
  '进近',
  '向像',
  '因音',
  '读度',
  '词辞',
  '练炼',
  '段断',
]

const CHINESE_CONFUSIONS = CHINESE_CONFUSION_GROUPS.reduce((map, group) => {
  const chars = Array.from(group)
  chars.forEach(char => {
    map[char] = new Set(chars.filter(item => item !== char))
  })
  return map
}, {})

function editDistance(a, b) {
  const left = String(a || '')
  const right = String(b || '')
  const m = left.length
  const n = right.length
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = 0; i <= m; i++) dp[i][0] = i
  for (let j = 0; j <= n; j++) dp[0][j] = j
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    }
  }
  return dp[m][n]
}

function correctionCost(original, recognized, language) {
  if (original === recognized) return 0
  if (!original || !recognized) return 1
  if (language === 'zh') {
    if (original.length === 1 && recognized.length === 1 && CHINESE_CONFUSIONS[original]?.has(recognized)) return 0.25
    return 1
  }
  const dist = editDistance(original, recognized)
  if (original.length >= 7 && dist <= 2) return 0.4
  if (original.length >= 4 && dist <= 1) return 0.3
  return 1
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

export function selectHiddenByLevel(tokens, language, level) {
  const config = LEVEL_CONFIG[level] || LEVEL_CONFIG[1]
  const wordIndices = tokens.map((token, i) => isWordToken(token, language) ? i : -1).filter(i => i >= 0)
  if (!wordIndices.length) return []
  if (config.hideAll) return wordIndices
  if (config.ratio <= 0 && !config.firstPerSentence) return []

  const groups = []
  let current = []
  tokens.forEach((token, i) => {
    if (isWordToken(token, language)) current.push(i)
    if (isSentenceEnd(token) && current.length) {
      groups.push(current)
      current = []
    }
  })
  if (current.length) groups.push(current)

  const hidden = new Set()
  groups.forEach(group => {
    if (config.firstPerSentence) {
      hidden.add(group[0])
    } else {
      selectHidden(group.length, config.ratio).forEach(i => hidden.add(group[i]))
    }
  })
  return [...hidden].sort((a, b) => a - b)
}

export function splitTokenSentences(tokens, language, text) {
  const result = []
  let current = []
  tokens.forEach(token => {
    current.push(token)
    if (isSentenceEnd(token) && current.some(t => isWordToken(t, language))) {
      result.push({ text: current.join(''), tokens: current })
      current = []
    }
  })
  if (current.some(t => isWordToken(t, language))) result.push({ text: current.join(''), tokens: current })
  if (result.length) return result

  const parts = language === 'zh'
    ? String(text || '').split(/(?<=[。！？\n])/)
    : String(text || '').split(/(?<=[.!?\n])/)
  return parts.map(s => s.trim()).filter(Boolean).map(s => ({ text: s, tokens: [s] }))
}

function expandOriginalTokens(tokens, language) {
  const units = []
  tokens.forEach((token, displayIndex) => {
    if (!isWordToken(token, language)) return
    const normalized = normalizeToken(token)
    if (!normalized) return
    if (language === 'zh') {
      Array.from(normalized).forEach(char => {
        if (/[\u4e00-\u9fffA-Za-z0-9]/.test(char)) units.push({ value: char, displayIndex })
      })
    } else {
      units.push({ value: normalized, displayIndex })
    }
  })
  return units
}

export function tokenizeRecognized(text, language) {
  const source = String(text || '').trim().toLowerCase()
  if (!source) return []
  if (language === 'zh') {
    return Array.from(source).map(normalizeToken).filter(token => /[\u4e00-\u9fffA-Za-z0-9]/.test(token))
  }
  return (source.match(/\b\w+(?:'\w+)?\b/g) || []).map(normalizeToken).filter(Boolean)
}

function alignValues(orig, recog, language = 'en', allowCorrection = false) {
  const m = orig.length
  const n = recog.length
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = 0; i <= m; i++) dp[i][0] = i
  for (let j = 0; j <= n; j++) dp[0][j] = j
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = allowCorrection ? correctionCost(orig[i - 1].value, recog[j - 1], language) : (orig[i - 1].value === recog[j - 1] ? 0 : 1)
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    }
  }

  const alignment = []
  let i = m
  let j = n
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0) {
      const subCost = allowCorrection ? correctionCost(orig[i - 1].value, recog[j - 1], language) : (orig[i - 1].value === recog[j - 1] ? 0 : 1)
      if (dp[i][j] === dp[i - 1][j - 1] + subCost) {
        const status = subCost === 0 ? 'correct' : (subCost < 1 ? 'corrected' : 'wrong')
        alignment.unshift({ ...orig[i - 1], status, got: recog[j - 1] })
        i--; j--
        continue
      }
    }
    if (j > 0 && dp[i][j] === dp[i][j - 1] + 1) {
      alignment.unshift({ value: recog[j - 1], displayIndex: null, status: 'extra', got: recog[j - 1] })
      j--
    } else if (i > 0) {
      alignment.unshift({ ...orig[i - 1], status: 'missing', got: '' })
      i--
    } else {
      alignment.unshift({ value: recog[j - 1], displayIndex: null, status: 'extra', got: recog[j - 1] })
      j--
    }
  }
  return alignment
}

function summarizeAlignment(alignment, total, language) {
  const displayStatus = {}
  let correct = 0

  alignment.forEach(item => {
    if (item.status === 'correct' || item.status === 'corrected') correct++
    if (item.displayIndex === null) return
    if (!displayStatus[item.displayIndex]) displayStatus[item.displayIndex] = []
    displayStatus[item.displayIndex].push(item.status)
  })

  const tokenStatuses = {}
  Object.entries(displayStatus).forEach(([idx, statuses]) => {
    if (statuses.every(s => s === 'correct')) tokenStatuses[idx] = 'correct'
    else if (statuses.every(s => s === 'correct' || s === 'corrected')) tokenStatuses[idx] = 'corrected'
    else if (statuses.includes('wrong')) tokenStatuses[idx] = 'wrong'
    else tokenStatuses[idx] = 'missing'
  })

  const correctedParts = alignment.map(item => {
    if (item.status === 'correct' || item.status === 'corrected') return item.value
    if (item.status === 'wrong' || item.status === 'extra') return item.got || ''
    if (item.status === 'missing') return language === 'zh' ? '□' : '___'
    return ''
  }).filter(Boolean)

  return {
    alignment,
    tokenStatuses,
    correct,
    total,
    accuracy: total > 0 ? correct / total : 0,
    correctedText: language === 'zh' ? correctedParts.join('') : correctedParts.join(' '),
  }
}

export function compareDisplayTokens(tokens, recognizedText, language) {
  const originalUnits = expandOriginalTokens(tokens, language)
  const recognizedTokens = tokenizeRecognized(recognizedText, language)
  const alignment = alignValues(originalUnits, recognizedTokens, language, false)
  return summarizeAlignment(alignment, originalUnits.length, language)
}

export function correctRecognizedText(tokens, recognizedText, language) {
  return compareWithCorrection(tokens, recognizedText, language).correctedText
}

export function compareWithCorrection(tokens, recognizedText, language) {
  const originalUnits = expandOriginalTokens(tokens, language)
  const recognizedTokens = tokenizeRecognized(recognizedText, language)
  const alignment = alignValues(originalUnits, recognizedTokens, language, true)
  return summarizeAlignment(alignment, originalUnits.length, language)
}

export function buildDisplayTokens(tokens, hiddenIndices, tokenStatuses, level, language) {
  return tokens.map((token, i) => {
    const hidden = hiddenIndices.includes(i)
    const status = tokenStatuses[i]
    let display = token
    let className = ''

    if (level === 5) {
      if (status === 'correct') { className = 'correct-word' }
      else if (status === 'corrected') { className = 'corrected-word' }
      else if (status === 'wrong') { className = 'wrong-word' }
      else if (status === 'missing') { display = `${token}?`; className = 'missing-word' }
      else if (isWordToken(token, language)) display = '____'
    } else if (!hidden || level === 1) {
      if (status === 'correct') className = 'correct-word'
      else if (status === 'corrected') className = 'corrected-word'
      else if (status === 'wrong') className = 'wrong-word'
      else if (status === 'missing') { display = `${token}?`; className = 'missing-word' }
    } else {
      if (status === 'correct') { className = 'correct-word' }
      else if (status === 'corrected') { className = 'corrected-word' }
      else if (status === 'wrong') { className = 'wrong-word' }
      else if (status === 'missing') { display = `${token}?`; className = 'missing-word' }
      else display = '____'
    }

    return { display, original: token, status: className }
  })
}
