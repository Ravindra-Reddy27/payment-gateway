import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';
const HEADERS = {
  'X-Api-Key': 'key_test_abc123',
  'X-Api-Secret': 'secret_test_xyz789'
};

export default function WebhookConfig() {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await axios.get(`${API_URL}/webhooks?limit=10`, { headers: HEADERS });
      setLogs(res.data.data || []);
    } catch (err) {
      console.error("Failed to fetch logs", err);
    }
  };

  const handleRetry = async (webhookId) => {
    try {
      await axios.post(`${API_URL}/webhooks/${webhookId}/retry`, {}, { headers: HEADERS });
      alert("Retry scheduled!");
      fetchLogs();
    } catch (err) {
      alert("Failed to retry");
    }
  };

  const handleSave = (e) => {
      e.preventDefault();
      alert("Configuration saved (Simulation)");
  };

  // Styles for high contrast
  const inputStyle = {
    width: '100%',
    padding: '10px',
    marginTop: '5px',
    marginBottom: '15px',
    borderRadius: '4px',
    border: '1px solid #ccc',
    backgroundColor: '#fff', // Force White Background
    color: '#333',           // Force Black Text
    fontSize: '16px'
  };

  const buttonStyle = {
    padding: '8px 16px',
    cursor: 'pointer',
    marginRight: '10px',
    marginBottom: '10px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px'
  };

  return (
    <div data-test-id="webhook-config" style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2>Webhook Configuration</h2>
      
      <form data-test-id="webhook-config-form" onSubmit={handleSave} style={{ marginBottom: '40px', background: '#2a2a2a', padding: '20px', borderRadius: '8px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', color: '#fff' }}>Webhook URL</label>
          <input 
            data-test-id="webhook-url-input"
            type="url"
            placeholder="https://yoursite.com/webhook"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            style={inputStyle}
          />
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ color: '#fff', marginRight: '10px' }}>Webhook Secret:</label>
          <span data-test-id="webhook-secret" style={{ fontFamily: 'monospace', background: '#444', padding: '4px 8px', borderRadius: '4px', color: '#ff79c6' }}>
            whsec_test_abc123
          </span>
          <button type="button" data-test-id="regenerate-secret-button" style={{ ...buttonStyle, marginLeft: '15px', backgroundColor: '#6c757d', fontSize: '12px' }}>
            Regenerate
          </button>
        </div>
        
        <button data-test-id="save-webhook-button" type="submit" style={buttonStyle}>
          Save Configuration
        </button>
        
        <button data-test-id="test-webhook-button" type="button" onClick={() => alert("Test sent!")} style={{ ...buttonStyle, backgroundColor: '#28a745' }}>
          Send Test Webhook
        </button>
      </form>
      
      <h3>Webhook Logs</h3>
      <table data-test-id="webhook-logs-table" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #555', textAlign: 'left' }}>
            <th style={{ padding: '10px' }}>Event</th>
            <th style={{ padding: '10px' }}>Status</th>
            <th style={{ padding: '10px' }}>Attempts</th>
            <th style={{ padding: '10px' }}>Last Attempt</th>
            <th style={{ padding: '10px' }}>Response Code</th>
            <th style={{ padding: '10px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id} data-test-id="webhook-log-item" data-webhook-id={log.id} style={{ borderBottom: '1px solid #444' }}>
              <td data-test-id="webhook-event" style={{ padding: '10px' }}>{log.event}</td>
              <td data-test-id="webhook-status" style={{ padding: '10px', color: log.status === 'success' ? '#50fa7b' : '#ff5555' }}>
                {log.status}
              </td>
              <td data-test-id="webhook-attempts" style={{ padding: '10px' }}>{log.attempts}</td>
              <td data-test-id="webhook-last-attempt" style={{ padding: '10px', fontSize: '0.9em', color: '#ccc' }}>
                 {log.last_attempt_at ? new Date(log.last_attempt_at).toLocaleString() : '-'}
              </td>
              <td data-test-id="webhook-response-code" style={{ padding: '10px' }}>{log.response_code || '-'}</td>
              <td style={{ padding: '10px' }}>
                <button 
                  data-test-id="retry-webhook-button"
                  data-webhook-id={log.id}
                  onClick={() => handleRetry(log.id)}
                  style={{ ...buttonStyle, backgroundColor: '#ffb86c', color: '#000', padding: '4px 8px', fontSize: '12px', margin: 0 }}
                >
                  Retry
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}