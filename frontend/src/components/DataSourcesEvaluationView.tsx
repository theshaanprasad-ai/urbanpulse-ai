import React from 'react';
import {
  Database,
  CheckCircle2,
  ShieldCheck,
  Award,
  FileText,
  Clock,
  ExternalLink,
  Info,
  Server
} from 'lucide-react';
import { DataSourceStatus, EvaluationReport } from '../types';

interface DataSourcesEvaluationViewProps {
  dataSources: DataSourceStatus[];
  evaluationReport: EvaluationReport | null;
}

export const DataSourcesEvaluationView: React.FC<DataSourcesEvaluationViewProps> = ({
  dataSources,
  evaluationReport,
}) => {
  return (
    <div className="space-y-6">
      {/* 1. Machine Learning Validation Report & Evaluation Metrics (Module 15) */}
      {evaluationReport && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">
                  Model Evaluation & Ground Truth Benchmarks
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated against Greater Chennai Corporation historical inundation records (2015-2023).
              </p>
            </div>

            <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium">
              5-Fold Spatial-Block CV
            </span>
          </div>

          {/* KPI Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 uppercase block">F1-Score</span>
              <span className="text-lg font-bold text-emerald-400">
                {evaluationReport.metrics.f1_score.toFixed(3)}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 uppercase block">Precision</span>
              <span className="text-lg font-bold text-white">
                {(evaluationReport.metrics.precision * 100).toFixed(1)}%
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 uppercase block">Recall</span>
              <span className="text-lg font-bold text-white">
                {(evaluationReport.metrics.recall * 100).toFixed(1)}%
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 uppercase block">ROC-AUC</span>
              <span className="text-lg font-bold text-cyan-400">
                {evaluationReport.metrics.roc_auc.toFixed(3)}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 uppercase block">Detection Delay</span>
              <span className="text-lg font-bold text-amber-400">
                {evaluationReport.detection_delay_minutes} min
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 uppercase block">Sample Size</span>
              <span className="text-lg font-bold text-slate-200">
                {evaluationReport.sample_size} Events
              </span>
            </div>
          </div>

          {/* Confusion Matrix and Holdout Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 text-xs">
            {/* Confusion Matrix */}
            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <span className="font-bold text-slate-200 block text-xs">
                Contingency Confusion Matrix (Test Holdout: Cyclone Michaung 2023)
              </span>
              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/30">
                  <span className="text-[10px] text-slate-400 block">True Positive (Flooded)</span>
                  <span className="font-bold text-emerald-400 text-sm">
                    {evaluationReport.confusion_matrix.true_positive}
                  </span>
                </div>
                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/30">
                  <span className="text-[10px] text-slate-400 block">False Positive (False Alarm)</span>
                  <span className="font-bold text-rose-400 text-sm">
                    {evaluationReport.confusion_matrix.false_positive}
                  </span>
                </div>
                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/30">
                  <span className="text-[10px] text-slate-400 block">False Negative (Missed Flood)</span>
                  <span className="font-bold text-rose-400 text-sm">
                    {evaluationReport.confusion_matrix.false_negative}
                  </span>
                </div>
                <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/30">
                  <span className="text-[10px] text-slate-400 block">True Negative (Safe Area)</span>
                  <span className="font-bold text-emerald-400 text-sm">
                    {evaluationReport.confusion_matrix.true_negative}
                  </span>
                </div>
              </div>
            </div>

            {/* Holdout Methodology */}
            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <span className="font-bold text-slate-200 block text-xs">Spatial & Temporal Generalization</span>
              <div className="space-y-1.5 text-[11px] text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-400">Spatial-Block Holdout Score:</span>
                  <span className="font-bold text-emerald-400">
                    {(evaluationReport.spatial_holdout_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Temporal Out-of-Sample Holdout:</span>
                  <span className="font-bold text-cyan-400">
                    {(evaluationReport.temporal_holdout_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Brier Calibration Loss:</span>
                  <span className="font-bold text-slate-200">{evaluationReport.metrics.brier_score}</span>
                </div>
              </div>
              <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-800/80 leading-relaxed">
                Methodology: Spatial blocks partition northern (Kosasthalaiyar), central (Cooum), and southern (Adyar) basins into independent holdouts to prevent spatial leakage.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
            <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{evaluationReport.provenance_disclaimer}</span>
          </div>
        </div>
      )}

      {/* 2. Ingestion Provider Health Status & Licensing Register (Module L) */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-emerald-400" />
              Unified Data Ingestion Register & Provider Health
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Tracks upstream telemetry health, data freshness, spatial coverage, and licensing compliance.
            </p>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
            {dataSources.length} Active Ingestion Providers
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-2 font-medium">Provider & Endpoint</th>
                <th className="pb-2 font-medium">Category</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Synced Records</th>
                <th className="pb-2 font-medium">Coverage Details</th>
                <th className="pb-2 font-medium">License & Terms</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {dataSources.map((src) => (
                <tr key={src.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 font-medium text-white flex items-center gap-2">
                    <Server className="w-3.5 h-3.5 text-slate-400" />
                    <span>{src.source_name}</span>
                  </td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-mono">
                      {src.category}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold text-[10px] flex items-center gap-1 w-max">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      {src.status}
                    </span>
                  </td>
                  <td className="py-3 font-semibold text-slate-200">{src.records_count}</td>
                  <td className="py-3 text-slate-300 max-w-xs">{src.coverage_details ?? '-'}</td>
                  <td className="py-3 text-slate-400 text-[11px]">{src.license_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
