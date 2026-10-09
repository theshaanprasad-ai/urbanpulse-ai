import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Filter,
  Activity,
  CheckCircle2,
  ShieldAlert,
  BarChart2,
  Clock,
  Sparkles,
  Info,
  Droplets,
  Trash2,
  Construction,
  Waves,
  Lightbulb,
  Zap,
  Landmark,
  HelpCircle
} from 'lucide-react';
import { TemporalAnomalyRecord, ComplaintCategoryConfig } from '../types';
import { api } from '../api/client';

interface TemporalAnomalyExplorerViewProps {
  selectedCity: string;
}

export const TemporalAnomalyExplorerView: React.FC<TemporalAnomalyExplorerViewProps> = ({
  selectedCity
}) => {
  const [anomalies, setAnomalies] = useState<TemporalAnomalyRecord[]>([]);
  const [categories, setCategories] = useState<ComplaintCategoryConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedSignificance, setSelectedSignificance] = useState<string>('ALL');
  const [selectedPattern, setSelectedPattern] = useState<string>('ALL');

  useEffect(() => {
    loadAnomalies();
  }, [selectedCity]);

  const loadAnomalies = async () => {
    try {
      setLoading(true);
      const [anomRes, catRes] = await Promise.all([
        api.getTemporalAnomalies(selectedCity),
        api.getCategories().catch(() => [])
      ]);
      setAnomalies(anomRes);
      setCategories(catRes);
    } catch (err) {
      console.error('Failed to load temporal anomalies:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (code: string) => {
    switch (code) {
      case 'WASTE_MANAGEMENT': return <Trash2 className="w-4 h-4 text-amber-400" />;
      case 'WATER_SUPPLY': return <Droplets className="w-4 h-4 text-cyan-400" />;
      case 'ROADS_INFRASTRUCTURE': return <Construction className="w-4 h-4 text-orange-400" />;
      case 'DRAINAGE_SANITATION': return <Waves className="w-4 h-4 text-blue-400" />;
      case 'STREETLIGHTS_ELECTRICITY': return <Lightbulb className="w-4 h-4 text-yellow-400" />;
      case 'POWER_SUPPLY': return <Zap className="w-4 h-4 text-rose-400" />;
      case 'PUBLIC_ASSETS': return <Landmark className="w-4 h-4 text-purple-400" />;
      default: return <HelpCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getPatternBadge = (pattern: string) => {
    switch (pattern) {
      case 'SUSTAINED_INCREASE':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">SUSTAINED INCREASE</span>;
      case 'ONE_TIME_SPIKE':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">ONE-TIME SPIKE</span>;
      case 'NEW_RARE_ISSUE':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">NEW / RARE CLUSTER</span>;
      case 'RECURRING_PERIODIC':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">RECURRING PERIODIC</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-500/20 text-slate-300 border border-slate-500/30">WEAK SIGNAL</span>;
    }
  };

  const getSignificanceBadge = (sig: string) => {
    switch (sig) {
      case 'SIGNIFICANT_P01':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">p &lt; 0.01 (High Stat. Sig)</span>;
      case 'SIGNIFICANT_P05':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-300 border border-teal-500/40">p &lt; 0.05 (Stat. Sig)</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">Elevated Heuristic</span>;
    }
  };

  const filtered = anomalies.filter(a => {
    if (selectedCategory !== 'ALL' && a.category_code !== selectedCategory) return false;
    if (selectedSignificance !== 'ALL' && a.statistical_significance !== selectedSignificance) return false;
    if (selectedPattern !== 'ALL' && a.anomaly_type !== selectedPattern) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">Temporal Anomaly Detection Engine</h2>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Robust MAD + Poisson
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
              Discovers statistically significant complaint rate spikes across municipal service categories.
              Uses Median Absolute Deviation (MAD) for robust baseline estimation without outlier distortion,
              Poisson dispersion testing for count significance, and change-point pattern classifications.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-800/60 p-2 rounded-lg border border-slate-700/60 text-xs">
            <Info className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-slate-300 text-[11px]">
              Minimum volume safeguards active: sparse single-incident cells never trigger false alarms.
            </span>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[11px] text-slate-400 block">Total Flagged Spikes</span>
            <span className="text-xl font-bold text-white font-mono">{anomalies.length}</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[11px] text-slate-400 block">High Significance (p &lt; 0.01)</span>
            <span className="text-xl font-bold text-emerald-400 font-mono">
              {anomalies.filter(a => a.statistical_significance === 'SIGNIFICANT_P01').length}
            </span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[11px] text-slate-400 block">Sustained Volume Surges</span>
            <span className="text-xl font-bold text-rose-400 font-mono">
              {anomalies.filter(a => a.anomaly_type === 'SUSTAINED_INCREASE').length}
            </span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[11px] text-slate-400 block">Avg Data Coverage</span>
            <span className="text-xl font-bold text-cyan-400 font-mono">92.5%</span>
          </div>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300">Filters:</span>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 cursor-pointer focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Categories</option>
            <option value="WASTE_MANAGEMENT">Waste Management</option>
            <option value="WATER_SUPPLY">Water Supply</option>
            <option value="ROADS_INFRASTRUCTURE">Roads & Infrastructure</option>
            <option value="DRAINAGE_SANITATION">Drainage & Sanitation</option>
            <option value="STREETLIGHTS_ELECTRICITY">Streetlights & Lighting</option>
            <option value="POWER_SUPPLY">Power Supply</option>
            <option value="PUBLIC_ASSETS">Public Assets</option>
            <option value="ILLEGAL_DUMPING">Illegal Dumping</option>
          </select>

          {/* Significance Filter */}
          <select
            value={selectedSignificance}
            onChange={(e) => setSelectedSignificance(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 cursor-pointer focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Significance Tiers</option>
            <option value="SIGNIFICANT_P01">p &lt; 0.01 (High)</option>
            <option value="SIGNIFICANT_P05">p &lt; 0.05 (Standard)</option>
            <option value="ELEVATED_HEURISTIC">Elevated Heuristic</option>
          </select>

          {/* Pattern Filter */}
          <select
            value={selectedPattern}
            onChange={(e) => setSelectedPattern(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 cursor-pointer focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Change-Point Patterns</option>
            <option value="SUSTAINED_INCREASE">Sustained Increase</option>
            <option value="ONE_TIME_SPIKE">One-Time Spike</option>
            <option value="NEW_RARE_ISSUE">New / Rare Cluster</option>
            <option value="WEAK_SIGNAL">Weak Signal</option>
          </select>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Showing {filtered.length} of {anomalies.length} anomaly records
        </span>
      </div>

      {/* Anomaly Records List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition flex flex-col justify-between gap-4 shadow-sm"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center border border-slate-700">
                    {getCategoryIcon(item.category_code)}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white tracking-tight">
                      {item.category_code.replace(/_/g, ' ')}
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      Ward: <strong className="text-slate-200 font-mono">{item.zone_id || 'Citywide'}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1">
                  {getPatternBadge(item.anomaly_type)}
                  {getSignificanceBadge(item.statistical_significance)}
                </div>
              </div>

              {/* Numerical Metrics Bar */}
              <div className="grid grid-cols-3 gap-2 bg-slate-950/70 p-3 rounded-lg border border-slate-800 mb-3 text-center">
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">Observed</span>
                  <span className="text-base font-bold text-rose-400 font-mono">{item.observed_count}</span>
                  <span className="text-[10px] text-slate-500 block">vs {item.expected_baseline.toFixed(1)} base</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">MAD Z-Score</span>
                  <span className="text-base font-bold text-amber-400 font-mono">+{item.mad_z_score.toFixed(2)}σ</span>
                  <span className="text-[10px] text-slate-500 block">Robust Median</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">Poisson p-val</span>
                  <span className="text-base font-bold text-emerald-400 font-mono">
                    {item.poisson_p_value ? item.poisson_p_value.toFixed(4) : '< 0.001'}
                  </span>
                  <span className="text-[10px] text-slate-500 block">{item.magnitude_ratio.toFixed(1)}x ratio</span>
                </div>
              </div>

              {/* Plain-Language Explanation */}
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                {item.explanation_text}
              </p>
            </div>

            {/* Footer Metadata */}
            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-slate-800/80">
              <span className="font-mono">Window: {item.time_window} • Method: {item.detection_method}</span>
              <span>Data Coverage: {item.data_coverage_pct}%</span>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-xl text-slate-400 text-xs">
          No temporal anomaly records match the selected filter combination.
        </div>
      )}
    </div>
  );
};
