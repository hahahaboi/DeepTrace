import React from 'react';
import { Activity, Hash, AlertOctagon } from 'lucide-react';

export default function PatternsTab({ patterns }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-rose-400" />
          Recurring Failure Patterns
        </h2>
        <p className="text-xs text-gray-400">Aggregated breakdown of common errors by CI/CD job and step</p>
      </div>

      {patterns.length === 0 ? (
        <div className="glass-card p-12 text-center text-gray-400">
          <Activity className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="font-semibold text-gray-300">No Recurring Failure Patterns Ingested</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {patterns.map((pattern, idx) => (
            <div key={idx} className="glass-card p-6 border border-gray-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-3 mb-3">
                  <span className="badge badge-cyan font-mono">
                    Job: {pattern.job_name}
                  </span>
                  <span className="badge badge-rose flex items-center gap-1">
                    <Hash className="w-3 h-3" /> {pattern.occurrence_count} {pattern.occurrence_count === 1 ? 'occurrence' : 'occurrences'}
                  </span>
                </div>

                {pattern.step_name && (
                  <p className="text-xs text-gray-400 mb-2">
                    Step: <span className="text-gray-200 font-medium">{pattern.step_name}</span>
                  </p>
                )}

                <div className="bg-black/50 p-3 rounded-lg border border-gray-800/80 mt-3">
                  <div className="flex items-center gap-1.5 text-xs text-rose-400 font-semibold mb-1">
                    <AlertOctagon className="w-3.5 h-3.5" />
                    Failure Reason
                  </div>
                  <p className="text-xs text-gray-300 font-mono line-clamp-3">
                    {pattern.failure_reason || 'Unspecified failure exception'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
