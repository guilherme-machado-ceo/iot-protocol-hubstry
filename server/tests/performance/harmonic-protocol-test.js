import http from 'k6/http'
import { check, sleep } from 'k6'
import { Trend } from 'k6/metrics'

const harmonicLatency = new Trend('harmonic_processing_ms')
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3001'

export const options = {
  vus: 20,
  duration: '2m',
  thresholds: {
    harmonic_processing_ms: ['p(95)<100'],
    http_req_failed: ['rate<0.01'],
  },
}

export default function () {
  const payload = JSON.stringify({
    fundamentalFreq: 1000,
    channels: [2, 3, 4, 5, 7, 8],
    message: `IoT test message VU=${__VU} iter=${__ITER}`,
  })

  const start = Date.now()
  const res = http.post(`${BASE_URL}/api/harmonic/simulate`, payload, {
    headers: { 'Content-Type': 'application/json' },
  })
  harmonicLatency.add(Date.now() - start)

  check(res, {
    'simulate 200': (r) => r.status === 200,
    'has harmonics': (r) => {
      const body = JSON.parse(r.body)
      return Array.isArray(body.harmonics) && body.harmonics.length === 6
    },
  })

  sleep(0.2)
}
