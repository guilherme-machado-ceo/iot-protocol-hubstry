import http from 'k6/http'
import { check, sleep } from 'k6'

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3001'

export const options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(99)<2000'],
    http_req_failed: ['rate<0.10'],
  },
}

export default function () {
  const res = http.post(
    `${BASE_URL}/api/devices/register`,
    JSON.stringify({
      deviceId: `stress_device_${__VU}_${__ITER}`,
      deviceType: 'stress_test',
      fundamentalFreq: 1000,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  )
  check(res, { 'register 201': (r) => r.status === 201 })
  sleep(0.5)
}
