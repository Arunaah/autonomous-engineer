import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  // Test 1: Health check
  const health = http.get(`${BASE_URL}/health`);
  check(health, {
    "health status 200": (r) => r.status === 200,
    "health response ok": (r) => JSON.parse(r.body).status === "ok",
  });

  sleep(0.5);

  // Test 2: Build endpoint (fire and forget)
  const payload = JSON.stringify({
    request: "Create a simple health check endpoint",
  });
  const params = { headers: { "Content-Type": "application/json" } };
  const build = http.post(`${BASE_URL}/build`, payload, params);
  check(build, {
    "build status 200": (r) => r.status === 200,
    "build started": (r) => JSON.parse(r.body).status === "started",
  });

  sleep(1);
}
