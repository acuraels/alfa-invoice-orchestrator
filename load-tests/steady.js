import { sleep } from 'k6';
import { sendBatch, setupAuth } from './lib/common.js';

export const options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '5m', target: 10 },
    { duration: '1m', target: 0 },
  ],
};

export function setup() {
  return setupAuth();
}

export default function (data) {
  sendBatch(data.token);
  sleep(0.5);
}
