import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import KPICards from './components/KPICards';
import OverviewTab from './components/OverviewTab';
import ClustersTab from './components/ClustersTab';
import FlakyTestsTab from './components/FlakyTestsTab';
import PatternsTab from './components/PatternsTab';
import WebhookSimulator from './components/WebhookSimulator';

import {
  fetchHealth,
  fetchClusters,
  fetchPatterns,
  fetchFlakyTests
} from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(false);

  const [clusters, setClusters] = useState([]);
  const [flakyTests, setFlakyTests] = useState([]);
  const [patterns, setPatterns] = useState([]);

  const loadData = async () => {
    setLoading(true);

    const isHealthy = await fetchHealth();
    setBackendHealthy(isHealthy);

    if (isHealthy) {
      const [clustersData, flakyData, patternsData] = await Promise.all([
        fetchClusters(),
        fetchFlakyTests(2, 0.2),
        fetchPatterns(10)
      ]);

      setClusters(clustersData);
      setFlakyTests(flakyData);
      setPatterns(patternsData);
    }

    setLoading(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Auto-refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const totalFailures = clusters.reduce((acc, c) => acc + (c.failure_count || 0), 0);

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 p-4 md:p-8 font-sans antialiased">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Top Header & Navigation */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          backendHealthy={backendHealthy}
          onRefresh={loadData}
          loading={loading}
        />

        {/* Metrics Overview Cards */}
        <KPICards
          clusterCount={clusters.length}
          flakyCount={flakyTests.filter(t => t.is_flaky).length}
          patternCount={patterns.length}
          totalFailures={totalFailures}
        />

        {/* Active Tab Panel */}
        <main className="transition-all duration-300">
          {activeTab === 'overview' && (
            <OverviewTab
              clusters={clusters}
              flakyTests={flakyTests}
              patterns={patterns}
            />
          )}

          {activeTab === 'clusters' && (
            <ClustersTab clusters={clusters} />
          )}

          {activeTab === 'flaky' && (
            <FlakyTestsTab flakyTests={flakyTests} />
          )}

          {activeTab === 'patterns' && (
            <PatternsTab patterns={patterns} />
          )}

          {activeTab === 'simulator' && (
            <WebhookSimulator onWebhookProcessed={loadData} />
          )}
        </main>

        {/* Footer */}
        <footer className="pt-8 pb-4 text-center border-t border-gray-900 text-xs text-gray-500">
          <p>DeepTrace CI/CD Failure Intelligence Platform &bull; Built with FastAPI, PostgreSQL pgvector, HDBSCAN & React</p>
        </footer>

      </div>
    </div>
  );
}
