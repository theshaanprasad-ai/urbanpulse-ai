export type DataMode = 'LIVE' | 'HISTORICAL_REPLAY';

export interface Zone {
  id: string;
  city_id: string;
  zone_number: number;
  name: string;
  center_lat: number;
  center_lon: number;
  mean_elevation_m: number;
  impervious_fraction: number;
  drainage_density_km_per_sqkm: number;
  historical_flood_vulnerability: number;
  population: number;
  boundary_geojson?: {
    type: string;
    coordinates: number[][][];
  };
}

export interface VulnerableAsset {
  id: string;
  city_id: string;
  zone_id?: string;
  name: string;
  asset_type: 'SUBWAY' | 'UNDERPASS' | 'PUMPING_STATION' | 'CANAL_OUTFALL' | 'HOSPITAL';
  lat: number;
  lon: number;
  elevation_m: number;
  critical_threshold_mm: number;
  description?: string;
}

export interface City {
  id: string;
  name: string;
  state: string;
  center_lat: number;
  center_lon: number;
  zoom_level: number;
  drainage_network_type: string;
  population: number;
  zones: Zone[];
  assets: VulnerableAsset[];
}

export interface RainfallObservation {
  id: number;
  city_id: string;
  zone_id?: string;
  station_id: string;
  station_name: string;
  timestamp: string;
  rainfall_1h_mm: number;
  rainfall_3h_mm: number;
  rainfall_24h_mm: number;
  source: string;
  provenance: string;
}

export interface RainfallAnalytics {
  city_id: string;
  max_24h_observed_mm: number;
  average_24h_observed_mm: number;
  max_3h_burst_mm: number;
  max_1h_burst_mm: number;
  imd_24h_category: string;
  imd_color_code: string;
  imd_alert_level: string;
  short_duration_intensity: {
    hourly_rate_mm_per_hr: number;
    three_hour_avg_rate_mm_per_hr: number;
    intensity_status: string;
    severity: string;
    operational_advice: string;
  };
  antecedent_precipitation_index: number;
  soil_saturation_status: string;
  last_synced_timestamp: string;
}

export interface OfficialWarning {
  id: number;
  city_id: string;
  warning_level: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
  issuing_authority: string;
  issued_at: string;
  valid_until: string;
  headline: string;
  description: string;
  recommended_actions?: string;
  source_url?: string;
}

export interface HistoricalWaterlogging {
  id: number;
  city_id: string;
  zone_id?: string;
  location_name: string;
  lat: number;
  lon: number;
  event_date: string;
  rainfall_amount_mm?: number;
  flood_depth_cm: number;
  disruption_type: string;
  source_citation: string;
}

export interface CivicComplaint {
  id: number;
  city_id: string;
  zone_id?: string;
  tracking_number: string;
  raw_text: string;
  parsed_summary?: string;
  language_detected: string;
  issue_category: string;
  subcategory?: string;
  severity_score: number;
  is_severe_hazard?: boolean;
  lat?: number | null;
  lon?: number | null;
  landmark?: string;
  reported_at: string;
  status: string;
  source: string;
  provenance: string;
  linked_incident_id?: number;
  reporter_email?: string | null;
  photo_analysis?: string | null;
  scan_source?: string | null;
}

export interface PhotoScanResult {
  problem_confirmed: boolean;
  issue_category: string;
  subcategory: string;
  severity_score: number;
  is_severe_hazard: boolean;
  confidence: number;
  what_is_going_on: string;
  officer_notes: string;
  visible_cues: string[];
  scan_source: string;
  scan_fallback_reason?: string | null;
}

export interface PhotoReportResponse {
  complaint: CivicComplaint;
  scan: PhotoScanResult;
  tracking_number: string;
  citizen_report: string;
}

export interface ComplaintCategoryConfig {
  id: string;
  code: string;
  name: string;
  description: string;
  target_department: string;
  default_sla_hours: number;
  baseline_rate_per_day: number;
  severity_weight: number;
  icon_name: string;
  is_active: boolean;
}

export interface TemporalAnomalyRecord {
  id: number;
  city_id: string;
  zone_id?: string;
  category_code: string;
  time_window: string;
  observed_count: number;
  expected_baseline: number;
  mad_z_score: number;
  poisson_p_value?: number;
  magnitude_ratio: number;
  anomaly_type: 'ONE_TIME_SPIKE' | 'SUSTAINED_INCREASE' | 'RECURRING_PERIODIC' | 'NEW_RARE_ISSUE' | 'WEAK_SIGNAL' | string;
  statistical_significance: 'SIGNIFICANT_P01' | 'SIGNIFICANT_P05' | 'ELEVATED_HEURISTIC' | 'NOT_SIGNIFICANT' | string;
  detection_method: string;
  data_coverage_pct: number;
  explanation_text: string;
  detected_at: string;
}

export interface CrossCategoryPattern {
  id: number;
  city_id: string;
  zone_id?: string;
  category_a: string;
  category_b: string;
  co_occurrence_count: number;
  temporal_window_hours: number;
  geographic_proximity_meters: number;
  correlation_coefficient: number;
  hypothesis_text: string;
  supporting_complaint_ids?: number[];
  detected_at: string;
}

export interface CSVImportJob {
  id: string;
  filename: string;
  total_rows: number;
  imported_rows: number;
  rejected_rows: number;
  rejection_log?: Array<{ line: number; reason: string }>;
  column_mapping?: Record<string, string>;
  uploaded_at: string;
}

export interface DualQueueResponse {
  queue_a_emerging_patterns: DecisionAction[];
  queue_b_severe_hazards: DecisionAction[];
  total_pending_queue_a: number;
  total_pending_queue_b: number;
}

export interface DuplicateCandidatePair {
  complaint_a: CivicComplaint;
  complaint_b: CivicComplaint;
  distance_meters: number;
  time_diff_minutes: number;
  text_similarity_score: number;
  composite_match_score: number;
  suggested_action: string;
  explanation: string;
}

export interface HotspotCluster {
  id: number;
  city_id: string;
  zone_id?: string;
  cluster_name: string;
  center_lat: number;
  center_lon: number;
  radius_meters: number;
  complaint_count: number;
  baseline_normal_count: number;
  anomaly_ratio: number;
  status: 'EMERGING' | 'PERSISTENT' | 'RESOLVING';
  detection_timestamp: string;
  rainfall_evidence: string;
}

export interface ContributingFactor {
  factor_name: string;
  score: number;
  max_score: number;
  weight_pct: number;
  description: string;
  supporting_metric: string;
}

export interface RiskAssessment {
  id: number;
  city_id: string;
  zone_id: string;
  zone_name?: string;
  assessment_timestamp: string;
  mode: 'MODE_1_BASELINE' | 'MODE_2_ML';
  overall_risk_score: number;
  risk_category: 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
  confidence_score: number;
  data_completeness_pct: number;
  supporting_evidence?: Record<string, any>;
  contributing_factors?: ContributingFactor[];
  limitations_text?: string;
  recommended_action?: string;
  version: string;
}

export interface WhatIfResponse {
  scenario_description: string;
  baseline_critical_wards: number;
  projected_critical_wards: number;
  average_risk_increase_pct: number;
  ward_projected_risks: Array<{
    zone_id: string;
    zone_name: string;
    baseline_score: number;
    projected_score: number;
    risk_delta: number;
    baseline_category: string;
    projected_category: string;
  }>;
}

export interface SystemAlert {
  id: number;
  city_id: string;
  zone_id?: string;
  alert_class: 'OFFICIAL_WEATHER_ALERT' | 'MODEL_IMPACT_RISK' | 'CIVIC_ANOMALY';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  location_name: string;
  valid_from: string;
  valid_to: string;
  evidence_text: string;
  contributing_factors?: Record<string, any>;
  data_gaps?: string;
  recommended_action: string;
  source_reference: string;
  created_at: string;
}

export interface DecisionAction {
  id: number;
  city_id: string;
  zone_id?: string;
  asset_id?: string;
  queue_type?: 'EMERGING_PATTERN_QUEUE' | 'HIGH_SEVERITY_HAZARD_QUEUE' | string;
  category_code?: string;
  target_department?: string;
  action_type: string;
  priority_score: number;
  priority_rank: number;
  location_name: string;
  description: string;
  evidence_basis: string;
  status: 'PENDING_REVIEW' | 'ACKNOWLEDGED' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED' | 'DEFERRED';
  assigned_to?: string;
  assigned_at?: string;
  updated_at: string;
}

export interface DataSourceStatus {
  id: string;
  source_name: string;
  category: 'WEATHER' | 'COMPLAINTS' | 'GEOSPATIAL' | 'CLIMATE';
  status: 'HEALTHY' | 'STALE' | 'DEGRADED' | 'OFFLINE';
  last_successful_sync: string;
  records_count: number;
  coverage_details?: string;
  license_type: string;
  citation?: string;
}

export interface ClimateScenario {
  id: string;
  city_id: string;
  scenario_name: string;
  time_horizon: string;
  projected_annual_rainfall_change_pct: number;
  extreme_rainfall_frequency_multiplier: number;
  vulnerable_ward_count: number;
  projected_runoff_increase_pct: number;
  data_source_citation: string;
}

export interface EvaluationReport {
  evaluation_date: string;
  dataset_name: string;
  pilot_city: string;
  sample_size: number;
  validation_methodology: string;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    roc_auc: number;
    brier_score: number;
  };
  confusion_matrix: {
    true_positive: number;
    false_positive: number;
    true_negative: number;
    false_negative: number;
  };
  per_class_f1: Record<string, number>;
  spatial_holdout_score: number;
  temporal_holdout_score: number;
  detection_delay_minutes: number;
  provenance_disclaimer: string;
}
