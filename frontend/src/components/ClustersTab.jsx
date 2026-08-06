import React, { useState } from 'react';
import { Layers, ChevronRight, X, Terminal, Calendar, Hash } from 'lucide-react';
import { fetchClusterDetail } from '../api';

export default function ClustersTab({ clusters }) {
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const handleSelectCluster = async (clusterId) => {
    setLoadingDetail(true);
    const detail = await fetchClusterDetail(clusterId);
    setSelectedCluster(detail);
    setLoadingDetail(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            HDBSCAN Failure Clusters
          </h2>
          <p className="text-xs text-gray-400">Vector-grouped similar pipeline failures based on log embeddings</p>
        </div>
        <span className="badge badge-cyan">{clusters.length} Active Clusters</span>
      </div>

      {clusters.length === 0 ? (
        <div className="glass-card p-12 text-center text-gray-400">
          <Layers className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="font-semibold text-gray-300">No Failure Clusters Generated</p>
          <p className="text-xs text-gray-500 mt-1">Send failure webhooks to trigger vector embedding and HDBSCAN clustering.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {clusters.map((cluster) => (
            <div
              key={cluster.id}
              onClick={() => handleSelectCluster(cluster.id)}
              className="glass-card glass-card-interactive p-6 cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <h3 className="text-base font-bold text-white leading-snug">
                    {cluster.title}
                  </h3>
                  <span className="badge badge-rose flex-shrink-0">
                    {cluster.failure_count} {cluster.failure_count === 1 ? 'Failure' : 'Failures'}
                  </span>
                </div>

                <p className="text-xs text-gray-300 mb-4 line-clamp-3 leading-relaxed">
                  {cluster.summary || 'No summary available.'}
                </p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-800 text-xs text-gray-400">
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-gray-500" />
                  {new Date(cluster.created_at).toLocaleDateString()}
                </span>

                <span className="text-cyan-400 font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  View Failures <ChevronRight className="w-4 h-4" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cluster Detail Modal */}
      {selectedCluster && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-card w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden border-cyan-500/30">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-800 flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge badge-cyan">Cluster #{selectedCluster.id}</span>
                  <span className="badge badge-rose">{selectedCluster.failure_count} Items</span>
                </div>
                <h3 className="text-xl font-bold text-white">{selectedCluster.title}</h3>
              </div>
              <button
                onClick={() => setSelectedCluster(null)}
                className="p-2 rounded-lg bg-gray-800 text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              <div className="bg-gray-900/60 p-4 rounded-xl border border-gray-800">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Cluster Summary</h4>
                <p className="text-sm text-gray-200">{selectedCluster.summary}</p>
              </div>

              <div>
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-cyan-400" />
                  Associated Failures ({selectedCluster.failures.length})
                </h4>

                <div className="space-y-4">
                  {selectedCluster.failures.map((f) => (
                    <div key={f.id} className="bg-gray-900/90 border border-gray-800 rounded-xl p-4 space-y-2">
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span className="font-semibold text-cyan-400">
                          {f.repository || 'Repository'} &bull; Job: {f.job_name} {f.step_name ? `(${f.step_name})` : ''}
                        </span>
                        <span>{new Date(f.created_at).toLocaleString()}</span>
                      </div>

                      {f.failure_reason && (
                        <p className="text-xs font-medium text-rose-400">
                          Reason: {f.failure_reason}
                        </p>
                      )}

                      {f.log_summary && (
                        <pre className="text-xs bg-black/60 p-3 rounded-lg text-gray-300 overflow-x-auto whitespace-pre-wrap font-mono border border-gray-800/80">
                          {f.log_summary}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
