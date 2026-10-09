import React from 'react';
import {
  AlertTriangle,
  CloudRain,
  ShieldAlert,
  Flame,
  CheckCircle2,
  Clock,
  ExternalLink,
  ArrowRight,
  TrendingUp,
  MapPin,
  Waves,
  Zap,
  Trash2,
  Droplets,
  Construction,
  Lightbulb,
  Landmark,
  Brain,
  Info
} from 'lucide-react';
import {
  RainfallAnalytics,
  OfficialWarning,
  RiskAssessment,
  HotspotCluster,
  DecisionAction,
  CivicComplaint
} from '../types';

interface CommandCenterViewProps {
  analytics: RainfallAnalytics | null;
  warnings: OfficialWarning[];
  riskAssessments: RiskAssessment[];
  hotspots: HotspotCluster[];
  actions: DecisionAction[];
  complaints: CivicComplaint[];
  onNavigateTab: (tab: string) => void;
  onSelectZone: (zoneId: string) => void;
  onAcknowledgeAction: (actionId: number) => void;
}

export const CommandCenterView: React.FC<CommandCenterViewProps> = ({
  analytics,
  warnings,
  riskAssessments,
  hotspots,
  actions,
  complaints,
  onNavigateTab,
  onSelectZone,
  onAcknowledgeAction,
}) => {
  const severeHazards = complaints.filter(c => c.is_severe_hazard);
  const queueAActions = actions.filter(
    (a) => a.queue_type === 'EMERGING_PATTERN_QUEUE' || (!a.queue_type && a.priority_score < 90)
  );
  const queueBActions = actions.filter(
    (a) => a.queue_type === 'HIGH_SEVERITY_HAZARD_QUEUE' || (!a.queue_type && a.priority_score >= 90)
  );

  // Category counts
  const categoryCounts: Record<string, number> = {};
  complaints.forEach(c => {
    const cat = c.issue_category || 'OTHER';
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });

  const categoriesConfig = [
    { code: 'WASTE_MANAGEMENT', label: 'Waste Management', icon: Trash2, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { code: 'WATER_SUPPLY', label: 'Water Supply', icon: Droplets, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { code: 'ROADS_INFRASTRUCTURE', label: 'Roads & Infrastructure', icon: Construction, color: 'text-orange-400', bg: 'bg-orange-500/10' },
    { code: 'DRAINAGE_SANITATION', label: 'Drainage & Sanitation', icon: Waves, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { code: 'STREETLIGHTS_ELECTRICITY', label: 'Streetlights', icon: Lightbulb, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
    { code: 'POWER_SUPPLY', label: 'Power Supply', icon: Zap, color: 'text-rose-400', bg: 'bg-rose-500/10' },
    { code: 'PUBLIC_ASSETS', label: 'Public Assets', icon: Landmark, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { code: 'ILLEGAL_DUMPING', label: 'Illegal Dumping', icon: Trash2, color: 'text-red-400', bg: 'bg-red-500/10' },
  ];

  return (
    <div className="space-y-5">
      {/* 1. Header Banner & Context Disclosure */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <h2 className="text-lg font-bold text-white tracking-tight">Urban Spatiotemporal Intelligence Hub</h2>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Live Anomaly Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
              Detects emerging municipal breakdown patterns, temporal rate-of-rise spikes, and spatial grievance clusters across 9 service wings.
              Provides dual-queue triage for human decision-makers.
            </p>
          </div>

          {/* Secondary Context Weather Badge */}
          {analytics && (
            <div className="flex items-center gap-3 bg-slate-950/80 p-3 rounded-lg border border-slate-800 text-xs shrink-0">
              <CloudRain className="w-5 h-5 text-blue-400 shrink-0" />
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Contextual Weather:</span>
                <span className="text-xs font-bold text-slate-200">
                  {analytics.imd_24h_category} ({analytics.max_24h_observed_mm}mm/24h)
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2. Key Operational Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Municipal Complaints */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Ingested Grievances</span>
            <span className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldAlert className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{complaints.length}</span>
              <span className="text-xs text-slate-400">Records</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Active across 15 GCC Administrative Zones
            </p>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Multi-Departmental</span>
            <button
              onClick={() => onNavigateTab('civic-intelligence')}
              className="text-emerald-400 hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Ledger</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Metric 2: Statistically Flagged Spikes */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Stat. Significant Anomalies</span>
            <span className="p-1.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-400 font-mono">5</span>
              <span className="text-xs text-slate-400">Active Spikes</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Robust MAD Z-score &gt; +3.0σ • Poisson p &lt; 0.01
            </p>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Minimum-volume guarded</span>
            <button
              onClick={() => onNavigateTab('temporal-anomalies')}
              className="text-amber-400 hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>Explore Engine</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Metric 3: Queue B Immediate Safety Hazards */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Queue B: Critical Hazards</span>
            <span className="p-1.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Zap className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-rose-400 font-mono">{queueBActions.length}</span>
              <span className="text-xs text-slate-400">Urgent Incidents</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Open manholes, live wires, trapped vehicles
            </p>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span className="text-rose-400 font-semibold">Immediate Triage</span>
            <button
              onClick={() => onNavigateTab('alerts-actions')}
              className="text-rose-400 hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>Dispatch Squad</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Metric 4: Queue A Emerging Pattern Review */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Queue A: Emerging Trends</span>
            <span className="p-1.5 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Brain className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-cyan-400 font-mono">{queueAActions.length}</span>
              <span className="text-xs text-slate-400">Pattern Tasks</span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Cross-category cascades &amp; spatial hot clusters
            </p>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Ranked by severity</span>
            <button
              onClick={() => onNavigateTab('cross-category')}
              className="text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Patterns</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. Category Volume Distribution Overview */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <span>Multi-Category Civic Complaint Volume &amp; Health</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            9 Canonical Municipal Wings
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {categoriesConfig.map((cat) => {
            const Icon = cat.icon;
            const count = categoryCounts[cat.code] || 0;
            return (
              <div
                key={cat.code}
                className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-1.5 rounded ${cat.bg} ${cat.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-lg font-bold text-white font-mono">{count}</span>
                </div>
                <span className="text-xs font-semibold text-slate-200 block truncate">{cat.label}</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  {count > 3 ? 'Surge Detected' : 'Normal Baseline'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Priority Operational Action Tasks Preview */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            High Priority Operational Interventions
          </h3>
          <button
            onClick={() => onNavigateTab('alerts-actions')}
            className="text-xs text-emerald-400 hover:underline flex items-center gap-1 cursor-pointer"
          >
            <span>Open Decision Queue ({actions.length})</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="space-y-3">
          {actions.slice(0, 3).map((act) => {
            const isQueueB = act.queue_type === 'HIGH_SEVERITY_HAZARD_QUEUE' || act.priority_score >= 90;
            return (
              <div
                key={act.id}
                className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between flex-wrap gap-3 text-xs"
              >
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        isQueueB
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {isQueueB ? 'QUEUE B: IMMEDIATE HAZARD' : 'QUEUE A: EMERGING PATTERN'}
                    </span>
                    <strong className="text-white text-xs">{act.location_name}</strong>
                  </div>
                  <p className="text-slate-300 text-xs">{act.description}</p>
                </div>

                <div className="flex items-center gap-3">
                  <span className="font-bold font-mono text-emerald-400 text-sm">
                    Priority: {act.priority_score}
                  </span>
                  <button
                    onClick={() => onNavigateTab('alerts-actions')}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3 py-1.5 rounded transition cursor-pointer"
                  >
                    Review Action
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
