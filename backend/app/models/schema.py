"""
SQLAlchemy ORM schemas for UrbanPulse AI.
General-purpose municipal complaint intelligence, statistical temporal anomaly detection,
spatiotemporal clustering, cross-category patterns, and dual-queue operational response.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(String(50), primary_key=True)  # e.g., 'chennai', 'bengaluru'
    name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    zoom_level = Column(Integer, default=11)
    boundary_bbox = Column(JSON, nullable=True)  # [min_lat, min_lon, max_lat, max_lon]
    drainage_network_type = Column(String(100), default="Combined & Natural Canals")
    population = Column(Integer, default=7000000)

    zones = relationship("AdministrativeZone", back_populates="city", cascade="all, delete-orphan")
    assets = relationship("VulnerableAsset", back_populates="city", cascade="all, delete-orphan")


class AdministrativeZone(Base):
    __tablename__ = "administrative_zones"

    id = Column(String(50), primary_key=True)  # e.g., 'chennai-zone-09'
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)
    mean_elevation_m = Column(Float, default=8.0)
    impervious_fraction = Column(Float, default=0.75)
    drainage_density_km_per_sqkm = Column(Float, default=1.8)
    historical_flood_vulnerability = Column(Float, default=0.5)
    population = Column(Integer, default=450000)

    city = relationship("City", back_populates="zones")
    assets = relationship("VulnerableAsset", back_populates="zone")


class VulnerableAsset(Base):
    __tablename__ = "vulnerable_assets"

    id = Column(String(50), primary_key=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    name = Column(String(150), nullable=False)
    asset_type = Column(String(50), nullable=False)  # SUBWAY, UNDERPASS, PUMPING_STATION, CANAL_OUTFALL, HOSPITAL, POWER_SUBSTATION, WATER_TREATMENT
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    elevation_m = Column(Float, default=5.0)
    critical_threshold_mm = Column(Float, default=50.0)
    description = Column(Text, nullable=True)

    city = relationship("City", back_populates="assets")
    zone = relationship("AdministrativeZone", back_populates="assets")


class ComplaintCategoryConfig(Base):
    """Configurable municipal complaint category definition."""
    __tablename__ = "complaint_category_configs"

    id = Column(String(50), primary_key=True)  # e.g. 'waste-mgmt'
    code = Column(String(50), unique=True, nullable=False)  # e.g. 'WASTE_MANAGEMENT'
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    target_department = Column(String(100), default="Solid Waste Management Dept")
    default_sla_hours = Column(Integer, default=24)
    baseline_rate_per_day = Column(Float, default=3.5)  # Expected normal daily reports per zone
    severity_weight = Column(Float, default=1.0)
    icon_name = Column(String(50), default="Trash2")
    is_active = Column(Boolean, default=True)


class CivicComplaint(Base):
    """Enriched municipal complaint entity across all municipal service categories."""
    __tablename__ = "civic_complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    tracking_number = Column(String(50), unique=True, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_summary = Column(Text, nullable=True)
    language_detected = Column(String(50), default="English")
    issue_category = Column(String(50), default="WASTE_MANAGEMENT")
    subcategory = Column(String(100), nullable=True)
    severity_score = Column(Integer, default=3)  # 1 to 5
    is_severe_hazard = Column(Boolean, default=False)  # Flag for Queue B immediate triage
    # Nullable: records without a verifiable location are kept but never assigned invented coordinates.
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    landmark = Column(String(150), nullable=True)
    occurrence_timestamp = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, default=datetime.utcnow)
    resolution_timestamp = Column(DateTime, nullable=True)
    status = Column(String(50), default="OPEN")  # OPEN, IN_INVESTIGATION, RESOLVED, REJECTED
    verification_state = Column(String(50), default="UNVERIFIED")  # UNVERIFIED, CONFIRMED, DISMISSED
    source = Column(String(50), default="CITIZEN_APP")
    source_system = Column(String(100), default="CITIZEN_PORTAL_1913")
    provenance = Column(String(50), default="SYNTHETIC_DEMO")
    linked_incident_id = Column(Integer, ForeignKey("linked_incidents.id"), nullable=True)
    reporter_email = Column(String(200), nullable=True)
    photo_analysis = Column(Text, nullable=True)
    scan_source = Column(String(50), nullable=True)


class LinkedIncident(Base):
    __tablename__ = "linked_incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    title = Column(String(200), nullable=False)
    issue_category = Column(String(50), default="WASTE_MANAGEMENT")
    primary_lat = Column(Float, nullable=False)
    primary_lon = Column(Float, nullable=False)
    complaint_count = Column(Integer, default=1)
    first_reported_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    verification_status = Column(String(50), default="UNVERIFIED")  # UNVERIFIED, CONFIRMED, DISMISSED
    operational_severity = Column(Integer, default=3)


class TemporalAnomalyRecord(Base):
    """Statistically validated temporal anomaly record (MAD, Poisson, Change-Point)."""
    __tablename__ = "temporal_anomaly_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    category_code = Column(String(50), nullable=False)
    time_window = Column(String(20), default="DAILY")  # HOURLY, DAILY, WEEKLY
    observed_count = Column(Integer, nullable=False)
    expected_baseline = Column(Float, nullable=False)
    mad_z_score = Column(Float, nullable=False)  # Robust Median Absolute Deviation Z-Score
    poisson_p_value = Column(Float, nullable=True)  # Count-based significance p-value
    magnitude_ratio = Column(Float, nullable=False)  # Observed / Baseline
    anomaly_type = Column(String(50), default="ONE_TIME_SPIKE")  # ONE_TIME_SPIKE, SUSTAINED_INCREASE, RECURRING_PERIODIC, NEW_RARE_ISSUE, WEAK_SIGNAL
    statistical_significance = Column(String(50), default="ELEVATED_HEURISTIC")  # SIGNIFICANT_P01, SIGNIFICANT_P05, ELEVATED_HEURISTIC, NOT_SIGNIFICANT
    detection_method = Column(String(100), default="Robust MAD + Poisson Dispersion")
    data_coverage_pct = Column(Float, default=90.0)
    explanation_text = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)


class HotspotCluster(Base):
    """Spatiotemporal cluster discovered across geographic space and time."""
    __tablename__ = "hotspot_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    cluster_name = Column(String(150), nullable=False)
    category_code = Column(String(50), default="WASTE_MANAGEMENT")
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    radius_meters = Column(Float, default=400.0)
    complaint_count = Column(Integer, default=5)
    baseline_normal_count = Column(Float, default=1.0)
    anomaly_ratio = Column(Float, default=5.0)
    status = Column(String(50), default="EMERGING")  # EMERGING, PERSISTENT, EXPANDING, RESOLVING
    detection_timestamp = Column(DateTime, default=datetime.utcnow)
    rainfall_evidence = Column(String(255), default="Concentrated reports in active spatial radius")


class CrossCategoryPatternRecord(Base):
    """Candidate co-occurring civic breakdown relationship discovered across categories."""
    __tablename__ = "cross_category_pattern_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    category_a = Column(String(50), nullable=False)
    category_b = Column(String(50), nullable=False)
    co_occurrence_count = Column(Integer, default=5)
    temporal_window_hours = Column(Integer, default=24)
    geographic_proximity_meters = Column(Float, default=500.0)
    correlation_coefficient = Column(Float, default=0.75)
    hypothesis_text = Column(Text, nullable=False)
    supporting_complaint_ids = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)


class DuplicateReview(Base):
    """Human decision on a candidate duplicate pair. Records are never deleted on merge."""
    __tablename__ = "duplicate_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    complaint_id_1 = Column(Integer, ForeignKey("civic_complaints.id"), nullable=False)
    complaint_id_2 = Column(Integer, ForeignKey("civic_complaints.id"), nullable=False)
    decision = Column(String(20), nullable=False)  # MERGE, REJECT
    match_score = Column(Float, nullable=True)
    reviewer = Column(String(100), default="Control Room Supervisor")
    note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)


class CSVImportJob(Base):
    """Audit ledger for user-uploaded municipal complaint CSV datasets."""
    __tablename__ = "csv_import_jobs"

    id = Column(String(50), primary_key=True)
    filename = Column(String(200), nullable=False)
    total_rows = Column(Integer, default=0)
    imported_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    rejection_log = Column(JSON, nullable=True)
    column_mapping = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    source_format = Column(String(10), nullable=True)  # CSV, JSON
    flagged_rows = Column(Integer, nullable=True)
    warning_log = Column(JSON, nullable=True)
    provenance = Column(String(50), nullable=True)


class DecisionAction(Base):
    """Action in the dual operational response queue (Emerging Patterns vs Severe Hazards)."""
    __tablename__ = "decision_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    asset_id = Column(String(50), ForeignKey("vulnerable_assets.id"), nullable=True)
    queue_type = Column(String(50), default="EMERGING_PATTERN_QUEUE")  # EMERGING_PATTERN_QUEUE (Queue A), HIGH_SEVERITY_HAZARD_QUEUE (Queue B)
    category_code = Column(String(50), default="WASTE_MANAGEMENT")
    target_department = Column(String(100), default="Solid Waste Management Dept")
    action_type = Column(String(100), nullable=False)
    priority_score = Column(Float, default=80.0)
    priority_rank = Column(Integer, default=1)
    location_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    evidence_basis = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING_REVIEW")  # PENDING_REVIEW, ACKNOWLEDGED, ASSIGNED, IN_PROGRESS, RESOLVED, DEFERRED
    assigned_to = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    source_alert_key = Column(String(200), nullable=True, index=True)

    audit_logs = relationship("ActionAuditLog", back_populates="action", cascade="all, delete-orphan")


class ActionAuditLog(Base):
    __tablename__ = "action_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(Integer, ForeignKey("decision_actions.id"), nullable=False)
    operator_name = Column(String(100), default="Control Room Supervisor")
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    action = relationship("DecisionAction", back_populates="audit_logs")


class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    alert_class = Column(String(50), nullable=False)  # STATISTICAL_ANOMALY, HIGH_SEVERITY_HAZARD, CROSS_CATEGORY_PATTERN, WEATHER_CONTEXT
    category_code = Column(String(50), default="WASTE_MANAGEMENT")
    severity = Column(String(20), default="WARNING")  # INFO, WARNING, CRITICAL
    title = Column(String(200), nullable=False)
    location_name = Column(String(100), nullable=False)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=False)
    evidence_text = Column(Text, nullable=False)
    contributing_factors = Column(JSON, nullable=True)
    data_gaps = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=False)
    source_reference = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DataSourceStatus(Base):
    __tablename__ = "data_source_statuses"

    id = Column(String(50), primary_key=True)
    source_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # COMPLAINTS, GEOSPATIAL, WEATHER, CLIMATE
    status = Column(String(50), default="HEALTHY")
    last_successful_sync = Column(DateTime, default=datetime.utcnow)
    records_count = Column(Integer, default=0)
    coverage_details = Column(String(255), nullable=True)
    license_type = Column(String(100), default="Open Government Data (OGD) / CC-BY")
    citation = Column(String(255), nullable=True)


# --- Optional Contextual Entities (Preserved without dominating) ---
class RainfallObservation(Base):
    __tablename__ = "rainfall_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    station_id = Column(String(50), nullable=False)
    station_name = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    rainfall_1h_mm = Column(Float, default=0.0)
    rainfall_3h_mm = Column(Float, default=0.0)
    rainfall_24h_mm = Column(Float, default=0.0)
    source = Column(String(100), default="IMD Automatic Weather Station")
    provenance = Column(String(50), default="SYNTHETIC_DEMO")


class RainfallForecast(Base):
    __tablename__ = "rainfall_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    forecast_6h_mm = Column(Float, default=0.0)
    forecast_24h_mm = Column(Float, default=0.0)
    forecast_72h_mm = Column(Float, default=0.0)
    model_name = Column(String(100), default="NCMRWF-GFS")
    source = Column(String(100), default="IMD NWP Grid")
    provenance = Column(String(50), default="SYNTHETIC_DEMO")


class OfficialWarning(Base):
    __tablename__ = "official_warnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    warning_level = Column(String(20), nullable=False)
    issuing_authority = Column(String(100), default="India Meteorological Department")
    issued_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=False)
    headline = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommended_actions = Column(Text, nullable=True)
    source_url = Column(String(255), nullable=True)


class HistoricalWaterloggingRecord(Base):
    __tablename__ = "historical_waterlogging_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=True)
    location_name = Column(String(150), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    event_date = Column(String(50), nullable=False)
    rainfall_amount_mm = Column(Float, nullable=True)
    flood_depth_cm = Column(Float, default=30.0)
    disruption_type = Column(String(100), default="Inundation")
    source_citation = Column(String(255), default="Historical Municipal Inundation Atlas")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    zone_id = Column(String(50), ForeignKey("administrative_zones.id"), nullable=False)
    assessment_timestamp = Column(DateTime, default=datetime.utcnow)
    mode = Column(String(50), default="MODE_1_BASELINE")
    overall_risk_score = Column(Float, nullable=False)
    risk_category = Column(String(50), nullable=False)
    confidence_score = Column(Float, default=0.85)
    data_completeness_pct = Column(Float, default=90.0)
    supporting_evidence = Column(JSON, nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    limitations_text = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    version = Column(String(50), default="v2.0.0-urbanpulse")


class ClimateScenario(Base):
    __tablename__ = "climate_scenarios"

    id = Column(String(50), primary_key=True)
    city_id = Column(String(50), ForeignKey("cities.id"), nullable=False)
    scenario_name = Column(String(100), nullable=False)
    time_horizon = Column(String(50), nullable=False)
    projected_annual_rainfall_change_pct = Column(Float, default=12.5)
    extreme_rainfall_frequency_multiplier = Column(Float, default=1.75)
    vulnerable_ward_count = Column(Integer, default=9)
    projected_runoff_increase_pct = Column(Float, default=24.0)
    data_source_citation = Column(String(255), default="INDRA-CMIP6 Ensemble")
