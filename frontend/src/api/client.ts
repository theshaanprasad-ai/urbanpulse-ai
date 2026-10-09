import {
  City,
  Zone,
  VulnerableAsset,
  RainfallObservation,
  RainfallAnalytics,
  OfficialWarning,
  HistoricalWaterlogging,
  CivicComplaint,
  DuplicateCandidatePair,
  HotspotCluster,
  RiskAssessment,
  WhatIfResponse,
  SystemAlert,
  DecisionAction,
  DataSourceStatus,
  ClimateScenario,
  EvaluationReport,
  ComplaintCategoryConfig,
  TemporalAnomalyRecord,
  CrossCategoryPattern,
  CSVImportJob,
  DualQueueResponse,
  PhotoReportResponse,
} from '../types';

export interface AIAssistantResponse {
  answer: string;
  language: string;
  source: string;
  evidence: string[];
  suggested_actions: string[];
}

// Dev uses the Vite proxy; a hosted build needs the deployed backend's origin.
const BASE_URL = `${import.meta.env.VITE_API_BASE_URL ?? ''}/api`;

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error [${res.status}] ${endpoint}: ${errorText}`);
  }
  return res.json();
}

export const api = {
  getHealth: () => fetchJson<{ status: string; data_mode: string; version: string; default_city: string }>('/health'),

  getCities: () => fetchJson<City[]>('/cities'),
  getCity: (cityId: string) => fetchJson<City>(`/cities/${cityId}`),
  getZones: (cityId: string = 'chennai') => fetchJson<Zone[]>(`/zones?city_id=${cityId}`),
  getAssets: (cityId: string = 'chennai') => fetchJson<VulnerableAsset[]>(`/assets?city_id=${cityId}`),

  getRainfallObservations: (cityId: string = 'chennai') =>
    fetchJson<RainfallObservation[]>(`/rainfall/observations?city_id=${cityId}`),
  getRainfallAnalytics: (cityId: string = 'chennai') =>
    fetchJson<RainfallAnalytics>(`/rainfall/analytics?city_id=${cityId}`),
  getOfficialWarnings: (cityId: string = 'chennai') =>
    fetchJson<OfficialWarning[]>(`/rainfall/warnings?city_id=${cityId}`),

  getHistoricalWaterlogging: (cityId: string = 'chennai') =>
    fetchJson<HistoricalWaterlogging[]>(`/waterlogging/historical?city_id=${cityId}`),

  getComplaints: (cityId: string = 'chennai', category?: string) =>
    fetchJson<CivicComplaint[]>(`/civic/complaints?city_id=${cityId}${category ? `&category=${category}` : ''}`),
  submitComplaint: (payload: { raw_text: string; city_id?: string; landmark?: string; reporter_email?: string }) =>
    fetchJson<CivicComplaint>('/civic/complaints', {
      method: 'POST',
      body: JSON.stringify({ city_id: 'chennai', ...payload }),
    }),
  submitPhotoReport: (payload: {
    city_id?: string;
    image_base64: string;
    mime_type?: string;
    note?: string;
    hint_category?: string;
    landmark?: string;
    lat?: number;
    lon?: number;
    reporter_email?: string;
  }) =>
    fetchJson<PhotoReportResponse>('/civic/photo-report', {
      method: 'POST',
      body: JSON.stringify({ city_id: 'chennai', ...payload }),
    }),
  getDuplicateCandidates: (cityId: string = 'chennai') =>
    fetchJson<DuplicateCandidatePair[]>(`/civic/duplicates?city_id=${cityId}`),
  resolveDuplicate: (payload: { complaint_id_1: number; complaint_id_2: number; action: 'MERGE' | 'REJECT'; incident_title?: string }) =>
    fetchJson<{ status: string; action: string; message: string }>('/civic/duplicates/resolve', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getHotspots: (cityId: string = 'chennai') => fetchJson<HotspotCluster[]>(`/hotspots?city_id=${cityId}`),

  getRiskAssessments: (cityId: string = 'chennai', mode: 'MODE_1_BASELINE' | 'MODE_2_ML' = 'MODE_1_BASELINE') =>
    fetchJson<RiskAssessment[]>(`/risk/assessments?city_id=${cityId}&mode=${mode}`),
  simulateWhatIf: (payload: { city_id?: string; additional_rainfall_mm: number; drainage_blockage_pct?: number }) =>
    fetchJson<WhatIfResponse>('/risk/what-if', {
      method: 'POST',
      body: JSON.stringify({ city_id: 'chennai', drainage_blockage_pct: 25.0, ...payload }),
    }),

  getAlerts: (cityId: string = 'chennai') => fetchJson<SystemAlert[]>(`/alerts?city_id=${cityId}`),

  getActions: (cityId: string = 'chennai') => fetchJson<DecisionAction[]>(`/actions?city_id=${cityId}`),
  updateAction: (actionId: number, payload: { status: string; assigned_to?: string; reason?: string }) =>
    fetchJson<DecisionAction>(`/actions/${actionId}/update`, {
      method: 'POST',
      body: JSON.stringify({ operator_name: 'Control Room Supervisor', ...payload }),
    }),

  // UrbanPulse AI multi-category anomaly & queue intelligence
  getCategories: () => fetchJson<ComplaintCategoryConfig[]>('/categories'),
  getTemporalAnomalies: (cityId: string = 'chennai', category?: string, significance?: string) =>
    fetchJson<TemporalAnomalyRecord[]>(
      `/anomalies/temporal?city_id=${cityId}${category ? `&category_code=${category}` : ''}${significance ? `&significance=${significance}` : ''}`
    ),
  getCrossCategoryPatterns: (cityId: string = 'chennai') =>
    fetchJson<CrossCategoryPattern[]>(`/patterns/cross-category?city_id=${cityId}`),
  getDualQueues: (cityId: string = 'chennai') =>
    fetchJson<DualQueueResponse>(`/actions/queues?city_id=${cityId}`),
  uploadComplaintsCsv: (payload: { csv_content: string; filename?: string; city_id?: string; provenance?: string }) =>
    fetchJson<CSVImportJob>('/complaints/upload-csv', {
      method: 'POST',
      body: JSON.stringify({ city_id: 'chennai', ...payload }),
    }),
  getCityAnalytics: (cityId: string = 'chennai') =>
    fetchJson<any>(`/analytics/city?city_id=${cityId}`),
  getDataQuality: (cityId: string = 'chennai') =>
    fetchJson<any>(`/analytics/quality?city_id=${cityId}`),
  askAIAssistant: (payload: { message: string; city_id?: string; language?: string }) =>
    fetchJson<AIAssistantResponse>('/ai/assistant', {
      method: 'POST',
      body: JSON.stringify({ city_id: 'chennai', ...payload }),
    }),

  getClimateScenarios: (cityId: string = 'chennai') =>
    fetchJson<ClimateScenario[]>(`/climate/scenarios?city_id=${cityId}`),
  compareClimateScenarios: (cityId: string = 'chennai') =>
    fetchJson<any>(`/climate/compare?city_id=${cityId}`),

  getDataSources: () => fetchJson<DataSourceStatus[]>('/datasources/status'),
  getEvaluationReport: (cityId: string = 'chennai') =>
    fetchJson<EvaluationReport>(`/evaluation/report?city_id=${cityId}`),

};
