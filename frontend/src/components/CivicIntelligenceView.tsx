import React, { useState } from 'react';
import {
  MessageSquare,
  Send,
  Link2,
  CheckCircle,
  XCircle,
  Filter,
  AlertCircle,
  Check,
  Languages,
  ShieldCheck,
  MapPin,
  Upload,
  FileText,
  AlertTriangle,
  FileSpreadsheet,
  Layers,
  Database
} from 'lucide-react';
import { CivicComplaint, DuplicateCandidatePair, CSVImportJob } from '../types';
import { api } from '../api/client';

interface CivicIntelligenceViewProps {
  complaints: CivicComplaint[];
  duplicatePairs: DuplicateCandidatePair[];
  onSubmitComplaint: (text: string, landmark?: string) => Promise<CivicComplaint>;
  onResolveDuplicate: (c1Id: number, c2Id: number, action: 'MERGE' | 'REJECT') => Promise<void>;
  onRefreshData?: () => void;
}

export const CivicIntelligenceView: React.FC<CivicIntelligenceViewProps> = ({
  complaints,
  duplicatePairs,
  onSubmitComplaint,
  onResolveDuplicate,
  onRefreshData,
}) => {
  const [subTab, setSubTab] = useState<'nlp' | 'csv' | 'duplicates'>('nlp');
  const [complaintText, setComplaintText] = useState('');
  const [selectedLandmark, setSelectedLandmark] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedResult, setSubmittedResult] = useState<CivicComplaint | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  // CSV Importer State
  const [csvContent, setCsvContent] = useState('');
  const [csvFilename, setCsvFilename] = useState('gcc_1913_export.csv');
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<CSVImportJob | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintText.trim()) return;

    setIsSubmitting(true);
    try {
      const res = await onSubmitComplaint(complaintText, selectedLandmark);
      setSubmittedResult(res);
      setComplaintText('');
      if (onRefreshData) onRefreshData();
    } catch (err) {
      console.error('Failed to submit complaint:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleImportCsv = async () => {
    if (!csvContent.trim()) return;
    setIsImporting(true);
    setImportError(null);
    try {
      const res = await api.uploadComplaintsCsv({
        csv_content: csvContent,
        filename: csvFilename,
        city_id: 'chennai',
        provenance: 'MUNICIPAL_CSV_EXPORT'
      });
      setImportResult(res);
      if (onRefreshData) onRefreshData();
    } catch (err: any) {
      setImportError(err.message || 'Failed to import CSV dataset');
    } finally {
      setIsImporting(false);
    }
  };

  const filteredComplaints = complaints.filter((c) => {
    if (selectedCategory === 'ALL') return true;
    return c.issue_category === selectedCategory;
  });

  return (
    <div className="space-y-6">
      {/* Sub-navigation bar */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setSubTab('nlp')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            subTab === 'nlp'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Languages className="w-4 h-4" />
          <span>Multilingual NLP Ingestion</span>
        </button>

        <button
          onClick={() => setSubTab('csv')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            subTab === 'csv'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Municipal CSV Batch Importer</span>
        </button>

        <button
          onClick={() => setSubTab('duplicates')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            subTab === 'duplicates'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Link2 className="w-4 h-4" />
          <span>Duplicate Incident Linking ({duplicatePairs.length})</span>
        </button>
      </div>

      {/* 1. Multilingual NLP Grievance Ingestion */}
      {subTab === 'nlp' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Languages className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Submit a typed citizen report</h3>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium">
              English • Tamil • Hindi • Hinglish
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Processes raw citizen reports, detects language, extracts incident category &amp; severity,
            identifies Queue B life-safety hazards (live wires, open manholes), and grounds coordinates strictly against verified landmarks.
          </p>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <textarea
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              rows={3}
              placeholder="Type or paste citizen complaint in any language (e.g. 'Vyasarpadi subway ke neeche paani bhar gaya', 'Live wire snapped near market')..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <input
                  type="text"
                  value={selectedLandmark}
                  onChange={(e) => setSelectedLandmark(e.target.value)}
                  placeholder="Optional landmark (e.g. Vyasarpadi Subway)"
                  className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-slate-700 w-60"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !complaintText.trim()}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isSubmitting ? 'Parsing Multilingual Text...' : 'Submit & Classify'}</span>
              </button>
            </div>
          </form>

          {/* Real-time classified result card */}
          {submittedResult && (
            <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/40 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-emerald-400" /> Grievance Ingested: {submittedResult.tracking_number}
                </span>
                <div className="flex items-center gap-2">
                  {submittedResult.is_severe_hazard && (
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                      🚨 Queue B: Immediate Safety Hazard
                    </span>
                  )}
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                    {submittedResult.language_detected}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
                <div>
                  <span className="text-slate-400 block">Classified Category:</span>
                  <span className="font-bold text-amber-400">{submittedResult.issue_category}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Severity Score:</span>
                  <span className="font-bold text-rose-400">{submittedResult.severity_score} / 5</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Resolved Landmark:</span>
                  <span className="font-bold text-slate-200">{submittedResult.landmark ?? 'City Center'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Coordinates:</span>
                  <span className="font-mono text-emerald-400">
                    {submittedResult.lat ? `${submittedResult.lat.toFixed(4)}, ${submittedResult.lon?.toFixed(4)}` : 'No coordinates (kept without inventing)'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 2. Municipal CSV Batch Importer */}
      {subTab === 'csv' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Municipal Complaint Dataset Importer</h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Upload or paste municipal complaint records (CSV). Automatic column mapping, spatial bounding-box audit, and rejection log.
              </p>
            </div>

          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Paste CSV Content (with headers):</span>
              <span className="font-mono text-[11px] text-slate-500">
                Supports Complaint ID, Description, Category, Created Date, Latitude, Longitude, Ward
              </span>
            </div>
            <textarea
              value={csvContent}
              onChange={(e) => setCsvContent(e.target.value)}
              rows={8}
              placeholder="Paste raw CSV text here..."
              className="w-full bg-slate-950 font-mono text-xs border border-slate-800 rounded-lg p-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">
              Target City: <strong className="text-white">Chennai (Greater Chennai Corporation)</strong>
            </span>

            <button
              onClick={handleImportCsv}
              disabled={isImporting || !csvContent.trim()}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-5 py-2 rounded-lg transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              <span>{isImporting ? 'Parsing & Auditing Batch...' : 'Parse & Ingest CSV Batch'}</span>
            </button>
          </div>

          {importError && (
            <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{importError}</span>
            </div>
          )}

          {/* Import Audit Results Card */}
          {importResult && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <span className="font-bold text-white text-sm">Batch Ingestion Audit: {importResult.id}</span>
                </div>
                <span className="text-xs text-slate-400 font-mono">{importResult.filename}</span>
              </div>

              {/* Counts Grid */}
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Total Rows</span>
                  <span className="text-lg font-bold text-white font-mono">{importResult.total_rows}</span>
                </div>
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Valid &amp; Ingested</span>
                  <span className="text-lg font-bold text-emerald-400 font-mono">{importResult.imported_rows}</span>
                </div>
                <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Rejected / Flagged</span>
                  <span className="text-lg font-bold text-rose-400 font-mono">{importResult.rejected_rows}</span>
                </div>
              </div>

              {/* Column Mapping Table */}
              {importResult.column_mapping && (
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-slate-300">Auto-Mapped Columns:</span>
                  <div className="flex flex-wrap gap-2 text-[11px] font-mono">
                    {Object.entries(importResult.column_mapping).map(([k, v]) => (
                      <span key={k} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                        {v} &rarr; <strong className="text-emerald-400">{k}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Rejection Log Table */}
              {importResult.rejection_log && importResult.rejection_log.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-slate-800">
                  <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" /> Rejection Audit Log ({importResult.rejection_log.length} Rows):
                  </span>
                  <div className="bg-slate-900/60 rounded-lg border border-slate-800 max-h-48 overflow-y-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                          <th className="p-2">Line #</th>
                          <th className="p-2">Rejection Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-[11px]">
                        {importResult.rejection_log.map((rej, i) => (
                          <tr key={i} className="hover:bg-slate-800/30">
                            <td className="p-2 font-mono text-amber-400">Line {rej.line}</td>
                            <td className="p-2 text-rose-300 font-mono">{rej.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 3. Duplicate Detection & Incident Linking Center */}
      {subTab === 'duplicates' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Link2 className="w-5 h-5 text-cyan-400" />
              <h3 className="text-base font-bold text-white">Duplicate Detection &amp; Incident Linking</h3>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-medium">
              {duplicatePairs.length} Candidate Matches
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Surfaces recurring citizen reports for the same physical breakdown using combined spatiotemporal proximity and token-level semantic similarity. Human review prevents accidental over-merges.
          </p>

          {duplicatePairs.length === 0 ? (
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 text-center">
              No active duplicate pairs detected above confidence threshold.
            </div>
          ) : (
            <div className="space-y-3">
              {duplicatePairs.map((pair, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-cyan-400">Match Confidence: {Math.round(pair.composite_match_score * 100)}%</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {pair.distance_meters}m apart • {pair.time_diff_minutes}m time delta
                      </span>
                    </div>
                    <span className="text-[11px] font-semibold text-amber-400">
                      Suggested Action: {pair.suggested_action}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                      <div className="flex justify-between text-[11px] text-slate-400 font-medium">
                        <span>Report #{pair.complaint_a.tracking_number}</span>
                        <span>{pair.complaint_a.language_detected}</span>
                      </div>
                      <p className="text-slate-200">{pair.complaint_a.raw_text}</p>
                      <span className="text-[10px] text-emerald-400 block">{pair.complaint_a.landmark}</span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                      <div className="flex justify-between text-[11px] text-slate-400 font-medium">
                        <span>Report #{pair.complaint_b.tracking_number}</span>
                        <span>{pair.complaint_b.language_detected}</span>
                      </div>
                      <p className="text-slate-200">{pair.complaint_b.raw_text}</p>
                      <span className="text-[10px] text-emerald-400 block">{pair.complaint_b.landmark}</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 italic">
                    Algorithm Breakdown: {pair.explanation}
                  </p>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                    <button
                      onClick={() => onResolveDuplicate(pair.complaint_a.id, pair.complaint_b.id, 'REJECT')}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition cursor-pointer flex items-center gap-1.5"
                    >
                      <XCircle className="w-3.5 h-3.5 text-rose-400" />
                      <span>Reject / Mark Distinct</span>
                    </button>
                    <button
                      onClick={() => onResolveDuplicate(pair.complaint_a.id, pair.complaint_b.id, 'MERGE')}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition cursor-pointer flex items-center gap-1.5"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Confirm Merge into Single Linked Incident</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Verified Complaints Stream Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            Verified Municipal Grievance Ledger ({complaints.length} Records)
          </h3>

          {/* Category Filter */}
          <div className="flex items-center gap-2 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-2.5 py-1 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Categories</option>
              <option value="WASTE_MANAGEMENT">Waste Management</option>
              <option value="WATER_SUPPLY">Water Supply</option>
              <option value="ROADS_INFRASTRUCTURE">Roads &amp; Infrastructure</option>
              <option value="DRAINAGE_SANITATION">Drainage &amp; Sanitation</option>
              <option value="STREETLIGHTS_ELECTRICITY">Streetlights</option>
              <option value="POWER_SUPPLY">Power Supply</option>
              <option value="PUBLIC_ASSETS">Public Assets</option>
              <option value="ILLEGAL_DUMPING">Illegal Dumping</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-2 font-medium">Tracking ID</th>
                <th className="pb-2 font-medium">Citizen Text</th>
                <th className="pb-2 font-medium">Language</th>
                <th className="pb-2 font-medium">Category</th>
                <th className="pb-2 font-medium">Severity</th>
                <th className="pb-2 font-medium">Landmark / Zone</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredComplaints.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 font-mono text-emerald-400 font-semibold">{c.tracking_number}</td>
                  <td className="py-2.5 text-slate-200 max-w-sm truncate">
                    {c.is_severe_hazard && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 mr-1.5">
                        HAZARD
                      </span>
                    )}
                    {c.raw_text}
                  </td>
                  <td className="py-2.5 text-slate-400">{c.language_detected}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium text-[10px]">
                      {c.issue_category}
                    </span>
                  </td>
                  <td className="py-2.5 font-semibold text-rose-400">{c.severity_score}/5</td>
                  <td className="py-2.5 text-slate-300">{c.landmark || c.zone_id || '-'}</td>
                  <td className="py-2.5 text-slate-400 font-medium uppercase text-[10px]">{c.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
