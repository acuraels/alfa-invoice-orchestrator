import { sleep } from 'k6';
import { sendBatch, setupAuth } from './lib/common.js';

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '30s', target: 60 },
    { duration: '1m', target: 60 },
    { duration: '30s', target: 5 },
    { duration: '30s', target: 0 },
  ],
};

export function setup() {
  return setupAuth();
}

export default function (data) {
  sendBatch(data.token);
  sleep(0.2);
}
