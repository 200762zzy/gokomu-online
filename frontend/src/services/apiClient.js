const API_BASE = '/api'
const TIMEOUT = 60000

function getApiKey() {
  return localStorage.getItem('deepseek_api_key') || ''
}

export async function requestAnalysis(board, retries = 2) {
  const apiKey = getApiKey()
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT)
    try {
      const resp = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board, api_key: apiKey }),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      if (!resp.ok) return null
      return await resp.json()
    } catch {
      clearTimeout(timeoutId)
      if (attempt < retries) continue
      return null
    }
  }
}

export async function requestReview(moves, result, retries = 1) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT)
    try {
      const resp = await fetch(`${API_BASE}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ moves, result }),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      if (!resp.ok) return null
      return await resp.json()
    } catch {
      clearTimeout(timeoutId)
      if (attempt < retries) continue
      return null
    }
  }
}

export async function requestAiMove(board, player) {
  const apiKey = getApiKey()
  if (!apiKey) return null
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT)
  try {
    const resp = await fetch(`${API_BASE}/ai-move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ board, player, api_key: apiKey }),
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    if (!resp.ok) return null
    return await resp.json()
  } catch {
    clearTimeout(timeoutId)
    return null
  }
}
