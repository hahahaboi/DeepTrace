import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';
import { Layers, AlertTriangle, Activity } from 'lucide-react';

const COLORS = ['#06B6D4', '#F43F5E', '#F59E0B', '#10B981', '#6366F1', '#8B5CF6', '#EC4899'];

export default function OverviewTab({ clusters, flakyTests, patterns }) {
  // Data formatting for Pie Chart (Failure Clusters)
  const clusterPieData = clusters.map(c => ({
    name: c.title.replace('Failure Cluster: ', ''),
    value: c.failure_count || 1
  }));

  // Data formatting for Flaky Tests Bar Chart
  const flakyBarData = flakyTests.slice(0, 6).map(t => ({
    name: t.test_name.length > 15 ? t.test_name.slice(0, 12) + '...' : t.test_name,
    Passed: t.passed_count,
    Failed: t.failed_count,
    Score: t.flakiness_score
  }));

  // Data formatting for Failure Patterns
  const patternBarData = patterns.slice(0, 6).map(p => ({
    name: `${p.job_name}/${p.step_name || 'step'}`,
    Count: p.occurrence_count
  }));

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Cluster Breakdown Pie Chart */}
        <div className="glass-card p-6 border border-gray-800">
          <div className="flex items-center gap-2 mb-6">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-semibold text-white">Cluster Distribution</h3>
          </div>

          {clusterPieData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={clusterPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {clusterPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#fff' }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px', color: '#9CA3AF' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-sm">
              <p>No failure clusters ingested yet.</p>
              <p className="text-xs text-gray-600 mt-1">Use the Webhook Simulator to send mock failures.</p>
            </div>
          )}
        </div>

        {/* Flaky Tests Pass/Fail Distribution */}
        <div className="glass-card p-6 border border-gray-800">
          <div className="flex items-center gap-2 mb-6">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-semibold text-white">Flaky Tests Pass vs Fail Ratios</h3>
          </div>

          {flakyBarData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={flakyBarData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                  <XAxis dataKey="name" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#fff' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', color: '#9CA3AF' }} />
                  <Bar dataKey="Passed" fill="#10B981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Failed" fill="#F43F5E" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-sm">
              <p>No flaky test history recorded yet.</p>
            </div>
          )}
        </div>

      </div>

      {/* Top Failure Patterns Bar Chart */}
      <div className="glass-card p-6 border border-gray-800">
        <div className="flex items-center gap-2 mb-6">
          <Activity className="w-5 h-5 text-rose-400" />
          <h3 className="text-base font-semibold text-white">Top Recurring Failure Patterns</h3>
        </div>

        {patternBarData.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={patternBarData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis type="number" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', color: '#fff' }}
                />
                <Bar dataKey="Count" fill="#06B6D4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-sm">
            <p>No failure patterns identified yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
