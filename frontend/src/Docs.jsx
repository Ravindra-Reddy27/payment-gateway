import React from 'react';

export default function Docs() {
  // Common style for code blocks to ensure visibility
  const codeBlockStyle = {
    background: '#f4f4f4',
    padding: '15px',
    color: '#333',          // <--- FORCES BLACK TEXT
    borderRadius: '5px',
    overflowX: 'auto',
    border: '1px solid #ccc'
  };

  return (
    <div data-test-id="api-docs" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Integration Guide</h2>

      {/* Section 1: Create Order */}
      <section data-test-id="section-create-order" style={{ marginBottom: '30px' }}>
        <h3>1. Create Order</h3>
        <pre data-test-id="code-snippet-create-order" style={codeBlockStyle}>
<code>{`curl -X POST http://localhost:8000/api/v1/payments \\
  -H "X-Api-Key: key_test_abc123" \\
  -H "X-Api-Secret: secret_test_xyz789" \\
  -H "Content-Type: application/json" \\
  -d '{
    "amount": 50000,
    "currency": "INR",
    "order_id": "order_xyz",
    "method": "upi"
  }'`}</code>
        </pre>
      </section>

      {/* Section 2: SDK Integration */}
      <section data-test-id="section-sdk-integration" style={{ marginBottom: '30px' }}>
        <h3>2. SDK Integration</h3>
        <pre data-test-id="code-snippet-sdk" style={codeBlockStyle}>
<code>{`<script src="http://localhost:5173/checkout.js"></script>
<script>
const checkout = new PaymentGateway({
  key: 'key_test_abc123',
  orderId: 'order_xyz',
  onSuccess: (response) => {
    console.log('Payment ID:', response.paymentId);
  }
});
checkout.open();
</script>`}</code>
        </pre>
      </section>

      {/* Section 3: Webhook Verification */}
      <section data-test-id="section-webhook-verification">
        <h3>3. Verify Webhook Signature</h3>
        <pre data-test-id="code-snippet-webhook" style={codeBlockStyle}>
<code>{`const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(payload))
    .digest('hex');
    
  return signature === expectedSignature;
}`}</code>
        </pre>
      </section>
    </div>
  );
}