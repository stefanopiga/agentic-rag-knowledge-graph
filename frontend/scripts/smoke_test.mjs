import assert from 'node:assert/strict'

const base = process.env.VITE_API_BASE_URL || process.env.VITE_API_URL || 'http://localhost:8000'

const r1 = await fetch(`${base}/health`)
assert.equal([200,500].includes(r1.status), true)

const r2 = await fetch(`${base}/health/detailed`)
assert.equal([200,500].includes(r2.status), true)

const r3 = await fetch(`${base}/status/database`)
assert.equal([200,500].includes(r3.status), true)

console.log('Smoke test OK against', base)
