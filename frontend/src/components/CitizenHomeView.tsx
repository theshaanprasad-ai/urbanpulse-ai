import React, { useMemo, useState } from 'react';
import {
  Camera,
  CheckCircle2,
  Construction,
  Droplets,
  Lightbulb,
  Loader2,
  MapPin,
  Trash2,
  Waves,
  AlertTriangle,
} from 'lucide-react';
import { CivicComplaint, OfficialWarning, PhotoReportResponse } from '../types';
import { api } from '../api/client';

const PROBLEM_TYPES = [
  { id: 'ROADS_INFRASTRUCTURE', label: 'Pothole / road', hint: 'Broken road, crater, collapsed patch', icon: Construction },
  { id: 'DRAINAGE_SANITATION', label: 'Water blockade', hint: 'Flooded street, blocked drain, sewage', icon: Waves },
  { id: 'WASTE_MANAGEMENT', label: 'Garbage', hint: 'Dump, overflow, uncleared waste', icon: Trash2 },
  { id: 'WATER_SUPPLY', label: 'Water supply', hint: 'No water, leak, dirty water', icon: Droplets },
  { id: 'STREETLIGHTS_ELECTRICITY', label: 'Streetlight', hint: 'Dark pole, sparking, dead light', icon: Lightbulb },
  { id: 'OTHER', label: 'Other', hint: 'Anything else you see', icon: AlertTriangle },
];

interface CitizenHomeViewProps {
  cityId: string;
  reporterEmail?: string;
  complaints: CivicComplaint[];
  warnings: OfficialWarning[];
  onReportCreated: (complaint: CivicComplaint) => void;
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('Could not read photo'));
    reader.readAsDataURL(file);
  });
}

export const CitizenHomeView: React.FC<CitizenHomeViewProps> = ({
  cityId,
  reporterEmail,
  complaints,
  warnings,
  onReportCreated,
}) => {
  const [problemType, setProblemType] = useState('ROADS_INFRASTRUCTURE');
  const [note, setNote] = useState('');
  const [landmark, setLandmark] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PhotoReportResponse | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);

  const myReports = useMemo(
    () => complaints.filter((item) => reporterEmail && item.reporter_email === reporterEmail).slice(0, 8),
    [complaints, reporterEmail],
  );

  const nearby = complaints.slice(0, 6);

  const onPickPhoto = (file: File | undefined) => {
    if (!file) return;
    if (file.size > 4_000_000) {
      setError('Please choose a photo smaller than 4 MB.');
      return;
    }
    setPhoto(file);
    setPreview(URL.createObjectURL(file));
    setError(null);
  };

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setError('Location is not available on this device.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => setError('Location permission was not given. You can still send the report with a landmark.'),
    );
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!photo) {
      setError('Please add a photo of the problem.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const image = await fileToBase64(photo);
      const payload = await api.submitPhotoReport({
        city_id: cityId,
        image_base64: image,
        mime_type: photo.type || 'image/jpeg',
        note,
        hint_category: problemType,
        landmark: landmark || undefined,
        lat: coords?.lat,
        lon: coords?.lon,
        reporter_email: reporterEmail,
      });
      setResult(payload);
      onReportCreated(payload.complaint);
      setNote('');
      setLandmark('');
      setPhoto(null);
      setPreview(null);
    } catch (err: any) {
      setError(err.message || 'Could not send the report.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-5">
      <section className="rounded-3xl bg-white text-slate-900 border border-emerald-100 p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">For residents</p>
        <h2 className="mt-1 text-2xl font-bold">See a problem? Snap it.</h2>
        <p className="mt-1 text-sm text-slate-600">
          Take a photo of a pothole, water blockade, garbage pile, or dark street. AI checks the photo and files a city report for you.
        </p>
      </section>

      {warnings[0] && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <strong>Weather note:</strong> {warnings[0].headline}
        </div>
      )}

      <form onSubmit={submit} className="rounded-3xl bg-white text-slate-900 border border-slate-200 p-5 space-y-4">
        <div>
          <p className="text-sm font-semibold mb-2">What did you see?</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {PROBLEM_TYPES.map((item) => {
              const Icon = item.icon;
              const active = problemType === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setProblemType(item.id)}
                  className={`text-left rounded-2xl border p-3 ${active ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 bg-slate-50'}`}
                >
                  <Icon className={`w-5 h-5 ${active ? 'text-emerald-600' : 'text-slate-500'}`} />
                  <p className="mt-2 text-sm font-semibold">{item.label}</p>
                  <p className="text-[11px] text-slate-500">{item.hint}</p>
                </button>
              );
            })}
          </div>
        </div>

        <label className="block">
          <span className="text-sm font-semibold">Photo</span>
          <div className="mt-2 rounded-2xl border-2 border-dashed border-emerald-200 bg-emerald-50/50 p-4 text-center">
            {preview ? (
              <img src={preview} alt="Selected civic problem" className="mx-auto max-h-52 rounded-xl object-cover" />
            ) : (
              <div className="py-6 text-slate-500">
                <Camera className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
                <p className="text-sm font-medium">Tap to take or upload a photo</p>
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="mt-3 w-full text-sm"
              onChange={(event) => onPickPhoto(event.target.files?.[0])}
            />
          </div>
        </label>

        <label className="block">
          <span className="text-sm font-semibold">Short note (optional)</span>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            placeholder="Example: Water blocked near the bus stop since morning"
            className="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm outline-none focus:border-emerald-500"
          />
        </label>

        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3">
            <MapPin className="w-4 h-4 text-slate-400" />
            <input
              value={landmark}
              onChange={(e) => setLandmark(e.target.value)}
              placeholder="Landmark, street, or area"
              className="w-full bg-transparent py-3 text-sm outline-none"
            />
          </div>
          <button type="button" onClick={useMyLocation} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700">
            {coords ? 'Location added' : 'Use my location'}
          </button>
        </div>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-2xl bg-emerald-600 py-3.5 text-base font-bold text-white hover:bg-emerald-500 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <Camera className="w-5 h-5" />}
          {busy ? 'Checking photo and filing report…' : 'Scan photo and send report'}
        </button>
      </form>

      {result && (
        <section className={`rounded-3xl border p-5 text-slate-900 space-y-2 ${
          result.scan.problem_confirmed
            ? 'border-emerald-200 bg-emerald-50'
            : 'border-amber-200 bg-amber-50'
        }`}>
          <p className={`flex items-center gap-2 font-bold ${
            result.scan.problem_confirmed ? 'text-emerald-800' : 'text-amber-800'
          }`}>
            {result.scan.problem_confirmed
              ? <CheckCircle2 className="w-5 h-5" />
              : <AlertTriangle className="w-5 h-5" />}
            Report {result.tracking_number}
          </p>
          <p className="text-sm leading-relaxed">{result.citizen_report}</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-xl bg-white p-3">
              <p className="text-slate-500">Detected</p>
              <p className="font-semibold">{result.scan.subcategory}</p>
            </div>
            <div className="rounded-xl bg-white p-3">
              <p className="text-slate-500">Confidence</p>
              <p className="font-semibold">{Math.round(result.scan.confidence * 100)}% · {result.scan.scan_source === 'GEMINI_VISION' ? 'AI photo scan' : 'Local check'}</p>
            </div>
          </div>
        </section>
      )}

      <section className="rounded-3xl bg-white text-slate-900 border border-slate-200 p-5">
        <h3 className="font-bold">Your reports</h3>
        {myReports.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">Nothing from this account yet. Send a photo to create the first one.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {myReports.map((item) => (
              <li key={item.id} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
                <p className="font-semibold">{item.tracking_number} · {item.subcategory || item.issue_category}</p>
                <p className="text-slate-500 text-xs">{item.parsed_summary || item.raw_text}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-3xl bg-white text-slate-900 border border-slate-200 p-5">
        <h3 className="font-bold">Nearby city reports</h3>
        <ul className="mt-3 space-y-2">
          {nearby.map((item) => (
            <li key={item.id} className="flex items-start justify-between gap-3 text-sm border-b border-slate-100 pb-2">
              <div>
                <p className="font-medium">{item.subcategory || item.issue_category.replaceAll('_', ' ')}</p>
                <p className="text-xs text-slate-500">{item.landmark || 'City area'} · {item.status}</p>
              </div>
              <span className="text-[11px] font-semibold text-emerald-700">Sev {item.severity_score}/5</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};
