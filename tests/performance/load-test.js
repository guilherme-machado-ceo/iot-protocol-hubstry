import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');

// Test configuration
export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],     // 95% of requests under 500ms
    'http_req_failed': ['rate<0.01'],       // Error rate under 1%
    'errors': ['rate<0.01'],                // Custom error rate under 1%
  },
};

const BASE_URL = 'http://localhost:3000';

// Test scenarios
export default function () {
  // Test 1: Homepage load
  let homeResponse = http.get(`${BASE_URL}/`);
  check(homeResponse, {
    'homepage status is 200': (r) => r.status === 200,
    'homepage loads in <200ms': (r) => r.timings.duration < 200,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: API health check
  let healthResponse = http.get(`${BASE_URL}/api/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time <100ms': (r) => r.timings.duration < 100,
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: Harmonic protocol simulation
  let simulationPayload = JSON.stringify({
    fundamentalFrequency: 1000,
    harmonicChannels: [2, 3, 5, 7],
    deviceCount: 10,
    simulationDuration: 5000
  });

  let simulationResponse = http.post(`${BASE_URL}/api/harmonic/simulate`, simulationPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(simulationResponse, {
    'simulation status is 200': (r) => r.status === 200,
    'simulation completes in <2s': (r) => r.timings.duration < 2000,
    'simulation returns valid data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.results && Array.isArray(data.results);
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(2);

  // Test 4: FFT calculation endpoint
  let fftPayload = JSON.stringify({
    signal: Array.from({ length: 1024 }, (_, i) => Math.sin(2 * Math.PI * i / 1024)),
    sampleRate: 44100
  });

  let fftResponse = http.post(`${BASE_URL}/api/harmonic/fft`, fftPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(fftResponse, {
    'FFT calculation status is 200': (r) => r.status === 200,
    'FFT calculation time <100ms': (r) => r.timings.duration < 100,
    'FFT returns frequency data': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.frequencies && data.magnitudes;
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(1);

  // Test 5: Device registration
  let devicePayload = JSON.stringify({
    deviceId: `device_${Math.random().toString(36).substr(2, 9)}`,
    deviceType: 'sensor',
    harmonicChannel: Math.floor(Math.random() * 10) + 2,
    capabilities: ['temperature', 'humidity']
  });

  let deviceResponse = http.post(`${BASE_URL}/api/devices/register`, devicePayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(deviceResponse, {
    'device registration status is 201': (r) => r.status === 201,
    'device registration time <300ms': (r) => r.timings.duration < 300,
  }) || errorRate.add(1);

  sleep(1);
}

// Setup function - runs once before the test
export function setup() {
  console.log('Starting load test for Harmonic IoT Protocol');

  // Verify the application is running
  let response = http.get(`${BASE_URL}/api/health`);
  if (response.status !== 200) {
    throw new Error('Application is not running or not healthy');
  }

  return { startTime: new Date() };
}

// Teardown function - runs once after the test
export function teardown(data) {
  console.log(`Load test completed. Started at: ${data.startTime}`);
  console.log('Test duration:', new Date() - data.startTime, 'ms');
}
