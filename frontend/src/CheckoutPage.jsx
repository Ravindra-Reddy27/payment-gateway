import React, { useState } from 'react';
import axios from 'axios';
import { useSearchParams } from 'react-router-dom';

export default function CheckoutPage() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get('order_id');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // 'success' | 'failed'

  const handlePayment = async () => {
    setLoading(true);
    try {
      // 1. Create Payment Transaction
      // Note: In a real app, you would collect card details here.
      // For this project, we just trigger the API.
      const response = await axios.post('http://localhost:8000/api/v1/payments', {
        amount: 5000, // Hardcoded for demo
        currency: 'INR',
        order_id: orderId,
        method: 'upi'
      }, {
        headers: {
          'X-Api-Key': 'key_test_abc123',
          'X-Api-Secret': 'secret_test_xyz789'
        }
      });

      // 2. Notify Parent Window (The SDK) [cite: 526-531]
      window.parent.postMessage({
        type: 'payment_success',
        data: response.data
      }, '*');
      
      setStatus('success');

    } catch (error) {
      console.error(error);
      window.parent.postMessage({
        type: 'payment_failed',
        data: { message: 'Payment failed' }
      }, '*');
      setStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  if (status === 'success') {
    return (
      <div style={{ textAlign: 'center', padding: '40px', fontFamily: 'sans-serif' }}>
        <h2 style={{ color: 'green' }}>Payment Successful!</h2>
        <p>Redirecting...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '400px', margin: '0 auto' }}>
      <h2 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px' }}>Secure Checkout</h2>
      
      <div style={{ background: '#f9f9f9', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
        <p style={{ margin: '5px 0', color: '#666' }}>Order ID:</p>
        <strong>{orderId || 'Missing Order ID'}</strong>
        <p style={{ margin: '15px 0 5px', color: '#666' }}>Amount:</p>
        <strong style={{ fontSize: '24px' }}>₹5,000.00</strong>
      </div>

      <button 
        onClick={handlePayment}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px',
          background: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px',
          cursor: loading ? 'not-allowed' : 'pointer',
          opacity: loading ? 0.7 : 1
        }}
      >
        {loading ? 'Processing...' : 'Pay Now'}
      </button>
    </div>
  );
}