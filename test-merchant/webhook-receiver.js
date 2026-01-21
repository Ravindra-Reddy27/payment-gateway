// test-merchant/webhook-receiver.js
const express = require('express');
const crypto = require('crypto');
const app = express();

app.use(express.json());

app.post('/webhook', (req, res) => {
    // 1. Get the signature from headers [cite: 658]
    const signature = req.headers['x-webhook-signature'];
    
    // 2. Get the raw payload string [cite: 659]
    // Note: In a real production app, you'd use raw-body middleware. 
    // For this test, JSON.stringify works IF the sender uses no whitespace.
    const payload = JSON.stringify(req.body);

    // 3. Verify signature using the Test Secret [cite: 661-664]
    const expectedSignature = crypto
        .createHmac('sha256', 'whsec_test_abc123')
        .update(payload)
        .digest('hex');

    if (signature !== expectedSignature) {
        console.log('❌ Invalid signature');
        console.log('Expected:', expectedSignature);
        console.log('Received:', signature);
        return res.status(401).send('Invalid signature');
    }

    // 4. Log Success [cite: 669-670]
    console.log('✅ Webhook verified:', req.body.event);
    if (req.body.data && req.body.data.payment) {
        console.log('   Payment ID:', req.body.data.payment.id);
    }

    res.status(200).send('OK');
});

app.listen(4000, '0.0.0.0', () => {
  console.log('Test merchant webhook running on port 4000');
});