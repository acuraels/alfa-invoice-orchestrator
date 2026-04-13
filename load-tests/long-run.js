import { sleep } from 'k6';
import { sendBatch, setupAuth } from './lib/common.js';

export const options = {
  stages: [
    { duration: '2m', target: 8 },
    { duration: '30m', target: 8 },
    { duration: '2m', target: 0 },
  ],
};

export function setup() {
  return setupAuth();
}

export default function (data) {
  sendBatch(data.token);
  sleep(1);
}
