import React, { useState } from 'react';
import { AlertTriangle, Search, CheckCircle, XCircle } from 'lucide-react';

export default function FlakyTestsTab({ flakyTests }) {
  const [search, setSearch] = useState('');

  const filteredTests = flakyTests.filter(t => 
    t.test_name.toLowerCase().includes(search.toLowerCase()) ||
    (t.test_suite && t.test_suite.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Flaky Test Intelligence
          </h2>
          <p className="text-xs text-gray-400">Tests ranked by state-flipping score: 2 &times; min(P, F) / (P + F)</p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search test or suite..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-gray-900/80 border border-gray-800 rounded-xl"
          />
        </div>
      </div>

      <div className="glass-card overflow-hidden border border-gray-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-900/80 text-gray-400 font-semibold border-b border-gray-800 uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Test Name</th>
                <th className="py-3.5 px-4">Test Suite</th>
                <th className="py-3.5 px-4 text-center">Total Runs</th>
                <th className="py-3.5 px-4 text-center">Passed / Failed</th>
                <th className="py-3.5 px-4 text-center">Failure Rate</th>
                <th className="py-3.5 px-6 text-right">Flakiness Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filteredTests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500">
                    No flaky test records found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredTests.map((test, idx) => {
                  const score = test.flakiness_score;
                  const isHighFlaky = score >= 0.5;
                  const isMediumFlaky = score >= 0.2 && score < 0.5;

                  return (
                    <tr key={idx} className="hover:bg-gray-800/40 transition-colors">
                      <td className="py-4 px-6 font-medium text-white">
                        <span className="font-mono">{test.test_name}</span>
                      </td>
                      <td className="py-4 px-4 text-gray-400">
                        {test.test_suite || 'default'}
                      </td>
                      <td className="py-4 px-4 text-center font-semibold">
                        {test.total_runs}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className="inline-flex items-center gap-2">
                          <span className="text-emerald-400 font-medium flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" /> {test.passed_count}
                          </span>
                          <span className="text-gray-600">/</span>
                          <span className="text-rose-400 font-medium flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> {test.failed_count}
                          </span>
                        </span>
                      </td>
                      <td className="py-4 px-4 text-center font-mono text-gray-300">
                        {(test.failure_rate * 100).toFixed(1)}%
                      </td>
                      <td className="py-4 px-6 text-right">
                        <span className={
                          isHighFlaky
                            ? 'badge badge-rose'
                            : isMediumFlaky
                            ? 'badge badge-amber'
                            : 'badge badge-emerald'
                        }>
                          {(score * 100).toFixed(0)}% Flaky
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
