import { sleep } from 'k6';
import { sendBatch, setupAuth } from './lib/common.js';

export const options = {
  vus: 2,
  duration: '30s',
};

export function setup() {
  return setupAuth();
}

export default function (data) {
  sendBatch(data.token);
  sleep(1);
}
