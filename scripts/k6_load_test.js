import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  vus: 5,
  duration: '15s',
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    errors: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.AE_BASE_URL || 'http://localhost:8000';

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  const healthOk = check(healthRes, {
    'health status 200': (r) => r.status === 200,
    'health response time < 1s': (r) => r.timings.duration < 1000,
  });
  errorRate.add(!healthOk);

  // Status check
  const statusRes = http.get(`${BASE_URL}/status/1`);
  check(statusRes, {
    'status endpoint responds': (r) => r.status === 200 || r.status === 404,
  });

  sleep(1);
}
