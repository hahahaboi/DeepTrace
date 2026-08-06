import React from 'react';
import { Layers, AlertTriangle, Activity, Database } from 'lucide-react';

export default function KPICards({ clusterCount, flakyCount, patternCount, totalFailures }) {
  const cards = [
    {
      title: 'Failure Clusters',
      value: clusterCount,
      description: 'HDBSCAN grouped vector patterns',
      icon: Layers,
      color: 'from-cyan-500/20 to-blue-500/20',
      border: 'border-cyan-500/30',
      text: 'text-cyan-400',
    },
    {
      title: 'Flaky Tests',
      value: flakyCount,
      description: 'High pass/fail state flipping',
      icon: AlertTriangle,
      color: 'from-amber-500/20 to-orange-500/20',
      border: 'border-amber-500/30',
      text: 'text-amber-400',
    },
    {
      title: 'Failure Patterns',
      value: patternCount,
      description: 'Unique job & step error types',
      icon: Activity,
      color: 'from-rose-500/20 to-pink-500/20',
      border: 'border-rose-500/30',
      text: 'text-rose-400',
    },
    {
      title: 'Total Ingested Failures',
      value: totalFailures,
      description: 'Processed GitHub Action runs',
      icon: Database,
      color: 'from-indigo-500/20 to-purple-500/20',
      border: 'border-indigo-500/30',
      text: 'text-indigo-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`glass-card p-6 border ${card.border} relative overflow-hidden group hover:scale-[1.02] transition-transform`}
          >
            <div className={`absolute -right-4 -bottom-4 w-24 h-24 bg-gradient-to-br ${card.color} rounded-full blur-2xl group-hover:blur-xl transition-all`} />
            
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                {card.title}
              </span>
              <div className={`p-2.5 rounded-xl bg-gradient-to-br ${card.color} ${card.text}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>

            <div className="text-3xl font-extrabold text-white mb-1 tracking-tight">
              {card.value}
            </div>
            <p className="text-xs text-gray-400">{card.description}</p>
          </div>
        );
      })}
    </div>
  );
}
