import http from 'k6/http';
import { check, fail } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const USERNAME = __ENV.USERNAME || 'admin';
const PASSWORD = __ENV.PASSWORD || 'AdminPassword123';
const BATCH_SIZE = Number(__ENV.BATCH_SIZE || 50);

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFrom(values) {
  return values[randomInt(0, values.length - 1)];
}

function createGroup(drf) {
  const departmentIds = [101, 102, 103, 104];
  const counterpartyIds = [10001, 10002, 10003, 10004, 10005];
  const vatRate = randomFrom(['0.1', '0.2']);
  const date = '2026-04-13';
  const departmentId = randomFrom(departmentIds);
  const counterpartyId = randomFrom(counterpartyIds);
  const lines = randomInt(1, 4);

  const tx = [];
  let vatTotal = 0;
  for (let i = 1; i <= lines; i += 1) {
    const quantity = randomInt(1, 10);
    const unitPrice = randomInt(100, 5000);
    const amount = quantity * unitPrice;
    const vat = amount * Number(vatRate);
    vatTotal += vat;
    tx.push({
      transactionId: `${drf}-INC-${String(i).padStart(3, '0')}`,
      drf,
      type: 'INCOME',
      counterpartyId,
      departmentId,
      date,
      productName: `Product ${i}`,
      unitMeasure: 'pcs',
      quantity: String(quantity),
      unitPrice: String(unitPrice),
      vatRate,
    });
  }

  tx.push({
    transactionId: `${drf}-VAT-001`,
    drf,
    type: 'VAT',
    counterpartyId,
    departmentId,
    date,
    vatRate,
    vatAmount: vatTotal.toFixed(4),
  });

  return tx;
}

export function setupAuth() {
  const loginUrl = `${BASE_URL}/api/auth/login/`;
  const response = http.post(
    loginUrl,
    JSON.stringify({ username: USERNAME, password: PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  const isOk = check(response, { 'login status 200': (r) => r.status === 200 });
  if (!isOk) {
    fail(
      `setupAuth failed: POST ${loginUrl} returned status=${response.status}; body="${String(
        response.body || ''
      ).slice(0, 300)}"`
    );
  }

  const contentType = String(response.headers['Content-Type'] || response.headers['content-type'] || '');
  if (!contentType.includes('application/json')) {
    fail(
      `setupAuth failed: expected JSON from ${loginUrl}, got content-type="${contentType}", body="${String(
        response.body || ''
      ).slice(0, 300)}"`
    );
  }

  let body;
  try {
    body = response.json();
  } catch (error) {
    fail(
      `setupAuth failed: cannot parse JSON from ${loginUrl}; error="${error}", body="${String(
        response.body || ''
      ).slice(0, 300)}"`
    );
  }

  if (!body?.access) {
    fail(`setupAuth failed: access token missing in login response from ${loginUrl}`);
  }

  return { token: body.access };
}

export function sendBatch(token) {
  if (!token) {
    fail('sendBatch failed: missing bearer token from setupAuth');
  }

  const payload = [];
  while (payload.length < BATCH_SIZE) {
    const drf = `K6-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    payload.push(...createGroup(drf));
  }

  const response = http.post(
    `${BASE_URL}/api/v1/ingest/transactions`,
    JSON.stringify(payload.slice(0, BATCH_SIZE)),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    }
  );

  check(response, {
    'ingest accepted': (r) => r.status === 202,
  });
}
