import React, { useState, useEffect } from 'react';
import {
  Brain,
  Link2,
  AlertTriangle,
  Info,
  ShieldAlert,
  ArrowRight,
  Droplets,
  Trash2,
  Construction,
  Waves,
  Lightbulb,
  Zap,
  CheckCircle,
  ExternalLink,
  Users
} from 'lucide-react';
import { CrossCategoryPattern } from '../types';
import { api } from '../api/client';

interface CrossCategoryPatternsViewProps {
  selectedCity: string;
}

export const CrossCategoryPatternsView: React.FC<CrossCategoryPatternsViewProps> = ({
  selectedCity
}) => {
  const [patterns, setPatterns] = useState<CrossCategoryPattern[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatterns();
  }, [selectedCity]);

  const loadPatterns = async () => {
    try {
      setLoading(true);
      const res = await api.getCrossCategoryPatterns(selectedCity);
      setPatterns(res);
    } catch (err) {
      console.error('Failed to load cross category patterns:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'WASTE_MANAGEMENT':
        return <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center gap-1.5"><Trash2 className="w-3.5 h-3.5" /> Waste Management</span>;
      case 'DRAINAGE_SANITATION':
        return <span className="px-2.5 py-1 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-semibold flex items-center gap-1.5"><Waves className="w-3.5 h-3.5" /> Drainage &amp; Sanitation</span>;
      case 'WATER_SUPPLY':
        return <span className="px-2.5 py-1 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center gap-1.5"><Droplets className="w-3.5 h-3.5" /> Water Supply</span>;
      case 'ROADS_INFRASTRUCTURE':
        return <span className="px-2.5 py-1 rounded bg-orange-500/20 text-orange-300 border border-orange-500/30 text-xs font-semibold flex items-center gap-1.5"><Construction className="w-3.5 h-3.5" /> Roads &amp; Potholes</span>;
      case 'POWER_SUPPLY':
        return <span className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" /> Power Supply</span>;
      default:
        return <span className="px-2.5 py-1 rounded bg-slate-500/20 text-slate-300 border border-slate-500/30 text-xs font-semibold">{cat}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">Cross-Category Pattern Discovery</h2>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Multi-Department Cascades
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
              Detects co-occurring breakdown spikes across distinct municipal categories within localized
              spatiotemporal windows. Uncovers systemic vulnerabilities that single-silo department portals miss.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-800/80 p-2.5 rounded-lg border border-slate-700/80 text-xs">
            <Link2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-slate-300 text-[11px] font-mono">
              Co-occurrence Radius: 450m • Window: 48h
            </span>
          </div>
        </div>

        {/* Mandatory Hackathon Problem Statement Guardrail Notice */}
        <div className="mt-4 p-3.5 bg-amber-950/30 border border-amber-500/40 rounded-lg text-xs text-amber-200/90 flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <strong className="text-amber-300 font-semibold uppercase text-[11px] tracking-wide block">
              Methodological Guardrail: Correlation vs Causation
            </strong>
            <p className="text-[11px] leading-relaxed">
              Co-occurrence patterns represent candidate hypotheses formulated from statistically correlated complaint surges.
              They indicate elevated compound stress requiring coordinated cross-department inspection, not verified mechanical causation.
            </p>
          </div>
        </div>
      </div>

      {/* Discovered Pattern Cards */}
      <div className="grid grid-cols-1 gap-4">
        {patterns.map((item) => (
          <div
            key={item.id}
            className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition space-y-4 shadow-sm"
          >
            {/* Top Bar: Interacting Categories and Correlation Score */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2 flex-wrap">
                {getCategoryBadge(item.category_a)}
                <ArrowRight className="w-4 h-4 text-slate-500" />
                {getCategoryBadge(item.category_b)}
                <span className="text-xs text-slate-400 font-mono ml-2">
                  Ward: <strong className="text-slate-200">{item.zone_id || 'Citywide Cluster'}</strong>
                </span>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block uppercase font-mono">Correlation</span>
                  <span className="text-sm font-bold text-emerald-400 font-mono">
                    r = {item.correlation_coefficient.toFixed(2)}
                  </span>
                </div>
                <div className="text-right pl-3 border-l border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase font-mono">Co-Occurrences</span>
                  <span className="text-sm font-bold text-cyan-400 font-mono">{item.co_occurrence_count} incidents</span>
                </div>
              </div>
            </div>

            {/* Candidate Hypothesis Explanation */}
            <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-lg space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                <Brain className="w-3.5 h-3.5" />
                <span>Candidate Cascading Hypothesis:</span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed font-sans">
                {item.hypothesis_text}
              </p>
            </div>

            {/* Coordinated Action Recommendation */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-slate-900/50 p-3 rounded-lg border border-slate-800/80">
              <div className="flex items-center gap-2 text-slate-300">
                <Users className="w-4 h-4 text-cyan-400" />
                <span>
                  <strong>Recommended Operational Protocol:</strong> Coordinated inter-departmental dispatch between both relevant civic wings.
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  Prox: {item.geographic_proximity_meters}m
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  Time: {item.temporal_window_hours}h
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {patterns.length === 0 && (
        <div className="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-xl text-slate-400 text-xs">
          No cross-category co-occurrence patterns currently detected.
        </div>
      )}
    </div>
  );
};
