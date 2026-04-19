import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate } from 'k6/metrics'

const errorRate = new Rate('errors')
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3001'

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    errors: ['rate<0.05'],
  },
}

export default function () {
  const healthRes = http.get(`${BASE_URL}/api/health`)
  check(healthRes, { 'health 200': (r) => r.status === 200 })
  errorRate.add(healthRes.status !== 200)

  const simulateRes = http.post(
    `${BASE_URL}/api/harmonic/simulate`,
    JSON.stringify({ fundamentalFreq: 1000, channels: [2, 3, 4, 5] }),
    { headers: { 'Content-Type': 'application/json' } }
  )
  check(simulateRes, { 'simulate 200': (r) => r.status === 200 })
  errorRate.add(simulateRes.status !== 200)

  sleep(1)
}
