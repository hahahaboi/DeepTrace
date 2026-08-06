import React from 'react';
import { Activity, Layers, AlertTriangle, PieChart, Send, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, backendHealthy, onRefresh, loading }) {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: PieChart },
    { id: 'clusters', label: 'Failure Clusters', icon: Layers },
    { id: 'flaky', label: 'Flaky Tests', icon: AlertTriangle },
    { id: 'patterns', label: 'Failure Patterns', icon: Activity },
    { id: 'simulator', label: 'Webhook Simulator', icon: Send },
  ];

  return (
    <header className="glass-card mb-8 px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4 border-b border-gray-800">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            DeepTrace
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-semibold">
              v1.0
            </span>
          </h1>
          <p className="text-xs text-gray-400">CI/CD Failure Intelligence Platform</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-gray-900/60 p-1.5 rounded-xl border border-gray-800/80">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-cyan-400 border border-cyan-500/30 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Status & Actions */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-900/80 border border-gray-800 text-xs">
          {backendHealthy ? (
            <>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span className="text-gray-300 font-medium">Backend Live</span>
            </>
          ) : (
            <>
              <XCircle className="w-4 h-4 text-rose-400" />
              <span className="text-gray-400">Backend Disconnected</span>
            </>
          )}
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2.5 rounded-lg bg-gray-800/80 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700/50 transition-all disabled:opacity-50"
          title="Refresh Data"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </header>
  );
}
