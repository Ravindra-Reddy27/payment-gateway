import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import WebhookConfig from './WebhookConfig';
import Docs from './Docs';
import CheckoutPage from './CheckoutPage';

function App() {
  return (
    <Router>
      <div>
        <nav style={{ padding: '20px', borderBottom: '1px solid #ddd', marginBottom: '20px' }}>
          <Link to="/dashboard/webhooks" style={{ marginRight: '20px' }}>Webhooks</Link>
          <Link to="/dashboard/docs">Documentation</Link>
        </nav>

        <Routes>
          <Route path="/dashboard/webhooks" element={<WebhookConfig />} />
          <Route path="/dashboard/docs" element={<Docs />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/" element={
            <div style={{ padding: '20px' }}>
              <h1>Merchant Dashboard</h1>
              <p>Select a tab above to manage your integration.</p>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;