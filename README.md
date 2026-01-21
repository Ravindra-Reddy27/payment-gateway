#  Payment Gateway System

A production-ready Payment Gateway that handles payments asynchronously using background workers. It includes a Merchant Dashboard, a Developer API, and an embeddable Checkout SDK.

## 🚀 Features

- **Async Processing**: Payments are processed in the background using Redis queues, ensuring high performance
- **Webhooks**: Notifies merchants instantly when a payment succeeds or fails (with secure HMAC signatures)
- **Idempotency**: Prevents duplicate charges if the same request is sent twice
- **Smart Retries**: Automatically retries failed webhooks with exponential backoff (wait times increase after each failure)
- **Refunds**: Supports partial refunds and validation logic

## 🛠️ Quick Start (Setup)

You only need Docker installed to run this entire system.

### 1. Start the Application

Open your terminal in the project folder and run:

```bash
docker-compose up -d --build
```

This single command starts 7 services:

- Backend API (Port 8000)
- Worker Service (Background Job Processor)
- Dashboard (Port 3000)
- Checkout SDK (Port 3001)
- Database (PostgreSQL)
- Queue (Redis)
- Test Merchant (Port 4000)

### 2. Access the Services

- **Merchant Dashboard**: http://localhost:3000
- **API Health Check**: http://localhost:8000/api/v1/test/jobs/status
- **Checkout JS SDK**: http://localhost:3001/checkout.js

## 🔑 Environment Variables

The application comes pre-configured for local development. You do not need to change these unless you are deploying to production.

| Service | Variable | Default Value | Description |
|---------|----------|---------------|-------------|
| API | `DATABASE_URL` | `postgresql://...` | Connection string for the database |
| API | `REDIS_URL` | `redis://redis:6379` | Connection string for the job queue |
| API | `WEBHOOK_RETRY_INTERVALS_TEST` | `true` | Speeds up retries for testing purposes |

## 📡 API Documentation

### 1. Create a Payment

Initiates a payment request. The status will initially be `pending`.

**Endpoint**: `POST /api/v1/payments`

**Headers**:
- `X-Api-Key`: `key_test_abc123`
- `X-Api-Secret`: `secret_test_xyz789`
- `Idempotency-Key`: (Optional) Unique string to prevent duplicates

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-Api-Key: key_test_abc123" \
  -H "X-Api-Secret: secret_test_xyz789" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "currency": "INR",
    "order_id": "order_12345",
    "method": "upi"
  }'
```

### 2. Get Payment Status

Check the current status of a payment.

**Endpoint**: `GET /api/v1/payments/{payment_id}`

### 3. Issue a Refund

Refund a successful payment (supports partial amounts).

**Endpoint**: `POST /api/v1/payments/{payment_id}/refunds`

**Body**:

```json
{
  "amount": 1000,
  "reason": "Customer requested return"
}
```

## 🎣 Webhook Integration Guide

Webhooks notify your server when a payment status changes (e.g., `payment.success`).

### 1. Configure Webhook URL

1. Go to the Dashboard at http://localhost:3000
2. Navigate to the **Webhooks** tab
3. Enter your server URL
   - For the included Test Merchant: Use `http://test-merchant:4000/webhook`

### 2. Verify Signatures (Security)

Every webhook includes an `X-Webhook-Signature` header. You must verify this to ensure the request is genuine.

**Verification Logic (Node.js Example)**:

```javascript
const crypto = require('crypto');

const secret = 'whsec_test_abc123'; // Found in Dashboard
const signature = req.headers['x-webhook-signature'];
const payload = JSON.stringify(req.body);

const expectedSignature = crypto
  .createHmac('sha256', secret)
  .update(payload)
  .digest('hex');

if (signature === expectedSignature) {
  console.log("✅ Verified Webhook");
}
```

## 📦 SDK Integration Guide

To add the checkout popup to your website, include the script and initialize it.

### 1. Add the Script

```html
<script src="http://localhost:3001/checkout.js"></script>
```

### 2. Initialize Payment

```javascript
const checkout = new PaymentGateway({
  key: 'key_test_abc123', // Your Public API Key
  orderId: 'order_12345', // The Order ID from your system
  onSuccess: (response) => {
    console.log('Payment Successful!', response);
    alert('Payment ID: ' + response.paymentId);
  },
  onFailure: (error) => {
    console.error('Payment Failed', error);
  }
});

// Open the modal
checkout.open();
```

## 🧪 Testing Instructions

### Automated Testing

Since the system includes a Test Merchant, you can verify the entire flow easily:

1. **Configure Webhook**: Set URL to `http://test-merchant:4000/webhook` in the Dashboard
2. **Make a Payment**: Use the curl command in the API section above
3. **Check Logs**:
   - Go to the Dashboard Webhooks table
   - You should see a `payment.success` event
   - The status should turn Green (Success) automatically

### Verify Retry Logic

1. Temporarily set the Webhook URL to a fake address (e.g., `http://nowhere`)
2. Trigger a payment
3. Watch the Dashboard log show "Pending" and "Attempts: 1"
4. Fix the URL back to correct one
5. Click Retry and watch it succeed

## 🔧 Troubleshooting

- **Worker stops after refresh?** Increase Docker memory limit in Docker Desktop settings (Settings → Resources)
- **Webhook failed with "Connection Refused"?** Ensure you are using `http://test-merchant:4000/webhook` and NOT `localhost`
