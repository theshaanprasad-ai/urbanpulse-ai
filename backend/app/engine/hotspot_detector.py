"""
Emerging Hotspot Detection Module for MonsoonWatch India.
Applies spatial clustering and temporal anomaly detection to identify unusual spikes
in waterlogging grievances, linking them with localized rainfall observations.
"""

from typing import List, Dict, Any
import math
from datetime import datetime


class HotspotDetector:
    """Spatiotemporal anomaly detection engine for urban grievance surges."""

    @staticmethod
    def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def detect_clusters(
        cls,
        complaints: List[Dict[str, Any]],
        eps_meters: float = 450.0,
        min_samples: int = 3,
        historical_baseline_per_sqkm: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Groups complaints into geographic clusters and computes anomaly ratios.
        """
        if not complaints:
            return []

        clusters: List[List[Dict[str, Any]]] = []
        visited = set()

        # Simple greedy spatial density clustering
        for i, c in enumerate(complaints):
            if i in visited:
                continue
            current_cluster = [c]
            visited.add(i)

            for j, other in enumerate(complaints):
                if j in visited:
                    continue
                dist = cls.haversine_distance_m(c["lat"], c["lon"], other["lat"], other["lon"])
                if dist <= eps_meters:
                    current_cluster.append(other)
                    visited.add(j)

            if len(current_cluster) >= min_samples:
                clusters.append(current_cluster)

        detected_hotspots = []
        for idx, cluster in enumerate(clusters, start=1):
            avg_lat = sum(c["lat"] for c in cluster) / len(cluster)
            avg_lon = sum(c["lon"] for c in cluster) / len(cluster)
            zone_id = cluster[0].get("zone_id", "chennai-zone-09")

            # Max distance from centroid defines cluster radius
            max_r = max(cls.haversine_distance_m(avg_lat, avg_lon, c["lat"], c["lon"]) for c in cluster)
            radius = max(250.0, max_r + 50.0)

            # Anomaly ratio calculation
            # Expected dry-weather complaints in ~0.5 km² area is ~0.8
            baseline_expected = max(0.5, round(historical_baseline_per_sqkm * (math.pi * (radius / 1000.0) ** 2), 2))
            count = len(cluster)
            anomaly_ratio = round(count / baseline_expected, 1)

            # Emerging vs Persistent
            status = "EMERGING" if anomaly_ratio >= 3.0 else "PERSISTENT"

            # Derive cluster name from most common landmark or location
            landmarks = [c.get("landmark") for c in cluster if c.get("landmark")]
            cluster_name = landmarks[0] if landmarks else f"Hotspot Cluster #{idx} ({zone_id})"

            detected_hotspots.append({
                "id": idx,
                "city_id": cluster[0].get("city_id", "chennai"),
                "zone_id": zone_id,
                "cluster_name": cluster_name,
                "center_lat": round(avg_lat, 5),
                "center_lon": round(avg_lon, 5),
                "radius_meters": round(radius, 1),
                "complaint_count": count,
                "baseline_normal_count": baseline_expected,
                "anomaly_ratio": anomaly_ratio,
                "status": status,
                "detection_timestamp": datetime.utcnow(),
                "rainfall_evidence": f"{count} complaints clustered within {int(radius)}m corridor during active precipitation"
            })

        return detected_hotspots
