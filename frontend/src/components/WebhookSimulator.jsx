import React, { useState } from 'react';
import { Send, CheckCircle, AlertTriangle, Code, Terminal, Key } from 'lucide-react';
import { sendMockWebhook } from '../api';

const PRESETS = {
  python: {
    action: "completed",
    workflow_run: {
      id: Math.floor(Math.random() * 100000) + 10000,
      run_number: Math.floor(Math.random() * 50) + 1,
      event: "push",
      status: "completed",
      conclusion: "failure",
      html_url: "https://github.com/deeptrace-demo/backend/actions/runs/123",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    repository: {
      id: 9901,
      name: "backend-service",
      owner: { login: "deeptrace-org" }
    },
    failed_job_name: "test-python",
    failed_step_name: "pytest",
    failure_reason: "AssertionError: Expected 200 OK but got 500 Internal Server Error",
    raw_logs: `
[INFO] Running pytest backend/tests/...
Traceback (most recent call last):
  File "app/main.py", line 42, in run
    result = execute_task()
  File "app/tasks.py", line 12, in execute_task
    raise ValueError("Database connection failed")
ValueError: Database connection failed
`
  },
  node: {
    action: "completed",
    workflow_run: {
      id: Math.floor(Math.random() * 100000) + 10000,
      run_number: Math.floor(Math.random() * 50) + 1,
      event: "pull_request",
      status: "completed",
      conclusion: "failure",
      html_url: "https://github.com/deeptrace-demo/frontend/actions/runs/456",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    repository: {
      id: 9902,
      name: "frontend-app",
      owner: { login: "deeptrace-org" }
    },
    failed_job_name: "test-node",
    failed_step_name: "npm test",
    failure_reason: "Error: Cannot find module 'express'",
    raw_logs: `
> jest
Error: Cannot find module 'express'
    at Object.<anonymous> (tests/index.test.js:8:21)
    at runTest (node_modules/jest-circus/build/run.js:124:4)
`
  }
};

export default function WebhookSimulator({ onWebhookProcessed }) {
  const [selectedPreset, setSelectedPreset] = useState('python');
  const [payloadText, setPayloadText] = useState(JSON.stringify(PRESETS.python, null, 2));
  const [secret, setSecret] = useState('deeptrace_secret_123');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  const handleSelectPreset = (key) => {
    setSelectedPreset(key);
    const updated = {
      ...PRESETS[key],
      workflow_run: {
        ...PRESETS[key].workflow_run,
        id: Math.floor(Math.random() * 100000) + 10000,
        run_number: Math.floor(Math.random() * 50) + 1,
      }
    };
    setPayloadText(JSON.stringify(updated, null, 2));
    setResult(null);
  };

  const handleSend = async () => {
    setSending(true);
    setResult(null);

    try {
      const parsedPayload = JSON.parse(payloadText);
      const res = await sendMockWebhook(parsedPayload, secret);
      setResult(res);

      if (res.ok) {
        onWebhookProcessed();
      }
    } catch (e) {
      setResult({ ok: false, status: 400, data: { error: `Invalid JSON syntax: ${e.message}` } });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Send className="w-5 h-5 text-cyan-400" />
          Interactive Webhook Simulator
        </h2>
        <p className="text-xs text-gray-400">
          Send real-time signed GitHub Actions failure webhooks to test automatic log parsing, vector embedding, and HDBSCAN cluster creation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Form */}
        <div className="lg:col-span-2 glass-card p-6 border border-gray-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Code className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-bold text-white">Preset Failure Scenarios:</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleSelectPreset('python')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  selectedPreset === 'python'
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                    : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                Python Traceback Failure
              </button>
              <button
                onClick={() => handleSelectPreset('node')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  selectedPreset === 'node'
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                    : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                Node.js Module Failure
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
              JSON Webhook Payload
            </label>
            <textarea
              rows={14}
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              className="w-full font-mono text-xs bg-black/70 p-4 border border-gray-800 rounded-xl leading-relaxed text-gray-200"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Key className="w-4 h-4 text-gray-500" />
              <span className="text-xs text-gray-400">Webhook Secret:</span>
              <input
                type="text"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                className="text-xs font-mono py-1 px-3 bg-gray-900 border border-gray-800 rounded-lg text-cyan-300"
              />
            </div>

            <button
              onClick={handleSend}
              disabled={sending}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {sending ? 'Signing & Sending...' : 'Trigger Webhook Endpoint'}
            </button>
          </div>
        </div>

        {/* Right Result View */}
        <div className="glass-card p-6 border border-gray-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-3">
              <Terminal className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Live Execution Result</h3>
            </div>

            {result ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-xl border flex items-center gap-3 ${
                  result.ok
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}>
                  {result.ok ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                  <div>
                    <div className="font-bold text-sm">
                      {result.ok ? 'Webhook Ingested Successfully' : 'Webhook Ingestion Failed'}
                    </div>
                    <div className="text-xs opacity-80">HTTP Status Code: {result.status}</div>
                  </div>
                </div>

                <div className="bg-black/60 p-4 rounded-xl border border-gray-800">
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">API Response</span>
                  <pre className="text-xs font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-center text-sm">
                <Send className="w-10 h-10 text-gray-700 mb-3" />
                <p>Click "Trigger Webhook Endpoint" to send an HMAC-signed request.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
