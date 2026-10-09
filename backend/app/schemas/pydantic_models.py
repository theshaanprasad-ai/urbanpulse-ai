"""
Pydantic data validation and serialization models for MonsoonWatch India API.
Guarantees schema compliance across all operational endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------- City & Geography ----------------
class ZoneSchema(BaseModel):
    id: str
    city_id: str
    zone_number: int
    name: str
    center_lat: float
    center_lon: float
    mean_elevation_m: float
    impervious_fraction: float
    drainage_density_km_per_sqkm: float
    historical_flood_vulnerability: float
    population: int
    boundary_geojson: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AssetSchema(BaseModel):
    id: str
    city_id: str
    zone_id: Optional[str] = None
    name: str
    asset_type: str
    lat: float
    lon: float
    elevation_m: float
    critical_threshold_mm: float
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CitySchema(BaseModel):
    id: str
    name: str
    state: str
    center_lat: float
    center_lon: float
    zoom_level: int
    drainage_network_type: str
    population: int
    zones: List[ZoneSchema] = []
    assets: List[AssetSchema] = []

    class Config:
        from_attributes = True


# ---------------- Rainfall Intelligence ----------------
class RainfallObservationSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    station_id: str
    station_name: str
    timestamp: datetime
    rainfall_1h_mm: float
    rainfall_3h_mm: float
    rainfall_24h_mm: float
    source: str
    provenance: str

    class Config:
        from_attributes = True


class RainfallForecastSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    valid_from: datetime
    valid_to: datetime
    forecast_6h_mm: float
    forecast_24h_mm: float
    forecast_72h_mm: float
    model_name: str
    source: str
    provenance: str

    class Config:
        from_attributes = True


class OfficialWarningSchema(BaseModel):
    id: int
    city_id: str
    warning_level: str
    issuing_authority: str
    issued_at: datetime
    valid_until: datetime
    headline: str
    description: str
    recommended_actions: Optional[str] = None
    source_url: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- Historical Inundation ----------------
class HistoricalWaterloggingSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    location_name: str
    lat: float
    lon: float
    event_date: str
    rainfall_amount_mm: Optional[float] = None
    flood_depth_cm: float
    disruption_type: str
    source_citation: str

    class Config:
        from_attributes = True


# ---------------- Civic Intelligence & Complaints ----------------
class CivicComplaintCreate(BaseModel):
    city_id: str = "chennai"
    raw_text: str = Field(..., min_length=3, description="Citizen complaint text in English, Hindi, Tamil, or Hinglish")
    lat: Optional[float] = Field(None, ge=6.4, le=35.7, description="Latitude within India")
    lon: Optional[float] = Field(None, ge=68.0, le=97.5, description="Longitude within India")
    landmark: Optional[str] = None
    zone_id: Optional[str] = None
    reporter_email: Optional[str] = None



class AIAssistantRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    city_id: str = "chennai"
    language: Optional[str] = None


class AIAssistantResponse(BaseModel):
    answer: str
    language: str
    source: str
    evidence: List[str] = []
    suggested_actions: List[str] = []


class CivicComplaintSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    tracking_number: str
    raw_text: str
    parsed_summary: Optional[str] = None
    language_detected: str
    issue_category: str
    subcategory: Optional[str] = None
    severity_score: int
    is_severe_hazard: bool = False
    lat: Optional[float] = None
    lon: Optional[float] = None
    landmark: Optional[str] = None
    reported_at: datetime
    status: str
    source: str
    provenance: str
    linked_incident_id: Optional[int] = None
    reporter_email: Optional[str] = None
    photo_analysis: Optional[str] = None
    scan_source: Optional[str] = None

    class Config:
        from_attributes = True


class PhotoReportRequest(BaseModel):
    city_id: str = "chennai"
    image_base64: str = Field(..., min_length=20, description="JPEG/PNG/WebP as raw or data-URL base64")
    mime_type: Optional[str] = "image/jpeg"
    note: Optional[str] = ""
    hint_category: Optional[str] = None
    landmark: Optional[str] = None
    lat: Optional[float] = Field(None, ge=6.4, le=35.7)
    lon: Optional[float] = Field(None, ge=68.0, le=97.5)
    zone_id: Optional[str] = None
    reporter_email: Optional[str] = None


class PhotoScanResult(BaseModel):
    problem_confirmed: bool
    issue_category: str
    subcategory: str
    severity_score: int
    is_severe_hazard: bool
    confidence: float
    what_is_going_on: str
    officer_notes: str
    visible_cues: List[str] = []
    scan_source: str
    scan_fallback_reason: Optional[str] = None


class PhotoReportResponse(BaseModel):
    complaint: CivicComplaintSchema
    scan: PhotoScanResult
    tracking_number: str
    citizen_report: str


class DuplicateCandidatePair(BaseModel):
    complaint_a: CivicComplaintSchema
    complaint_b: CivicComplaintSchema
    distance_meters: float
    time_diff_minutes: float
    text_similarity_score: float
    composite_match_score: float  # 0.0 to 1.0
    suggested_action: str
    explanation: str


class DuplicateResolutionRequest(BaseModel):
    complaint_id_1: int
    complaint_id_2: int
    action: str = Field(..., description="'MERGE' to link into single incident, or 'REJECT' to mark distinct")
    incident_title: Optional[str] = None


# ---------------- Category Configuration ----------------
class ComplaintCategoryConfigSchema(BaseModel):
    id: str
    code: str
    name: str
    description: str
    target_department: str
    default_sla_hours: int
    baseline_rate_per_day: float
    severity_weight: float
    icon_name: str
    is_active: bool

    class Config:
        from_attributes = True


# ---------------- Temporal Anomaly Detection ----------------
class TemporalAnomalyRecordSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    category_code: str
    time_window: str
    observed_count: int
    expected_baseline: float
    mad_z_score: float
    poisson_p_value: Optional[float] = None
    magnitude_ratio: float
    anomaly_type: str
    statistical_significance: str
    detection_method: str
    data_coverage_pct: float
    explanation_text: str
    detected_at: datetime

    class Config:
        from_attributes = True


# ---------------- Cross-Category Patterns ----------------
class CrossCategoryPatternSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    category_a: str
    category_b: str
    co_occurrence_count: int
    temporal_window_hours: int
    geographic_proximity_meters: float
    correlation_coefficient: float
    hypothesis_text: str
    supporting_complaint_ids: Optional[List[int]] = None
    detected_at: datetime

    class Config:
        from_attributes = True


# ---------------- CSV Ingestion ----------------
class CSVImportJobSchema(BaseModel):
    id: str
    filename: str
    total_rows: int
    imported_rows: int
    rejected_rows: int
    rejection_log: Optional[List[Dict[str, Any]]] = None
    column_mapping: Optional[Dict[str, str]] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class CSVUploadRequest(BaseModel):
    csv_content: str
    filename: str = "uploaded_complaints.csv"
    city_id: str = "chennai"
    provenance: str = "MUNICIPAL_CSV_EXPORT"


# ---------------- Hotspots & Anomalies ----------------
class HotspotClusterSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    cluster_name: str
    center_lat: float
    center_lon: float
    radius_meters: float
    complaint_count: int
    baseline_normal_count: float
    anomaly_ratio: float
    status: str
    detection_timestamp: datetime
    rainfall_evidence: str

    class Config:
        from_attributes = True


# ---------------- Impact Risk Engine ----------------
class ContributingFactor(BaseModel):
    factor_name: str
    score: float
    max_score: float
    weight_pct: float
    description: str
    supporting_metric: str


class RiskAssessmentSchema(BaseModel):
    id: int
    city_id: str
    zone_id: str
    zone_name: Optional[str] = None
    assessment_timestamp: datetime
    mode: str
    overall_risk_score: float
    risk_category: str
    confidence_score: float
    data_completeness_pct: float
    supporting_evidence: Optional[Dict[str, Any]] = None
    contributing_factors: Optional[List[Dict[str, Any]]] = None
    limitations_text: Optional[str] = None
    recommended_action: Optional[str] = None
    version: str

    class Config:
        from_attributes = True


class WhatIfScenarioRequest(BaseModel):
    city_id: str = "chennai"
    additional_rainfall_mm: float = Field(..., ge=0.0, le=250.0, description="Hypothetical additional rainfall in mm")
    rainfall_duration_hours: float = Field(default=3.0, ge=1.0, le=24.0)
    drainage_blockage_pct: float = Field(default=25.0, ge=0.0, le=100.0)


class WhatIfScenarioResponse(BaseModel):
    scenario_description: str
    baseline_critical_wards: int
    projected_critical_wards: int
    average_risk_increase_pct: float
    ward_projected_risks: List[Dict[str, Any]]


# ---------------- System Alerts ----------------
class SystemAlertSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    alert_class: str
    severity: str
    title: str
    location_name: str
    valid_from: datetime
    valid_to: datetime
    evidence_text: str
    contributing_factors: Optional[Dict[str, Any]] = None
    data_gaps: Optional[str] = None
    recommended_action: str
    source_reference: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------- Decision Actions & Audit ----------------
class DecisionActionSchema(BaseModel):
    id: int
    city_id: str
    zone_id: Optional[str] = None
    asset_id: Optional[str] = None
    queue_type: str = "EMERGING_PATTERN_QUEUE"
    category_code: str = "WASTE_MANAGEMENT"
    target_department: str = "Solid Waste Management Dept"
    action_type: str
    priority_score: float
    priority_rank: int
    location_name: str
    description: str
    evidence_basis: str
    status: str
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class DualQueueResponse(BaseModel):
    queue_a_emerging_patterns: List[DecisionActionSchema]
    queue_b_severe_hazards: List[DecisionActionSchema]
    total_pending_queue_a: int
    total_pending_queue_b: int


class DecisionActionUpdate(BaseModel):
    status: str = Field(..., description="PENDING_REVIEW, ACKNOWLEDGED, ASSIGNED, IN_PROGRESS, RESOLVED, DEFERRED")
    assigned_to: Optional[str] = None
    operator_name: str = "Control Room Supervisor"
    reason: Optional[str] = "Routine prioritization confirmation"


# ---------------- Data Sources ----------------
class DataSourceStatusSchema(BaseModel):
    id: str
    source_name: str
    category: str
    status: str
    last_successful_sync: datetime
    records_count: int
    coverage_details: Optional[str] = None
    license_type: str
    citation: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------- Climate Scenarios ----------------
class ClimateScenarioSchema(BaseModel):
    id: str
    city_id: str
    scenario_name: str
    time_horizon: str
    projected_annual_rainfall_change_pct: float
    extreme_rainfall_frequency_multiplier: float
    vulnerable_ward_count: int
    projected_runoff_increase_pct: float
    data_source_citation: str

    class Config:
        from_attributes = True


# ---------------- Model Evaluation & Benchmarks ----------------
class EvaluationReportSchema(BaseModel):
    evaluation_date: str
    dataset_name: str
    pilot_city: str
    sample_size: int
    validation_methodology: str
    metrics: Dict[str, float]
    confusion_matrix: Dict[str, int]
    per_class_f1: Dict[str, float]
    spatial_holdout_score: float
    temporal_holdout_score: float
    detection_delay_minutes: float
    provenance_disclaimer: str
