import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.05'],
  },
};

const defaultTarget = 'https://test-api.k6.io/public/crocodiles/1/';

export default function () {
  const target = `${__ENV.K6_TARGET_URL || defaultTarget}`;
  const response = http.get(target);
  check(response, {
    'response status is 200': (res) => res.status === 200,
  });
  sleep(1);
}
