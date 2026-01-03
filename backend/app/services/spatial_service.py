"""
Spatial Service - Detects and processes geospatial data for Talk2Map integration
Supports lat/lng coordinates, address geocoding, and Kepler.gl configuration
"""

import pandas as pd
import re
from typing import Dict, Optional, List, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

logger = logging.getLogger(__name__)


class SpatialService:
    """Service for detecting and processing geospatial data"""

    def __init__(self):
        self.geocoder = Nominatim(user_agent="aispreadsheets-talk2map")

    def detect_spatial_columns(self, df: pd.DataFrame) -> Dict:
        """
        Detect latitude/longitude, address, or geographic columns in a dataframe

        Returns:
            dict with structure:
            {
                "has_spatial": bool,
                "type": "coordinates" | "address" | "geographic" | None,
                "columns": dict,
                "bounding_box": dict (for coordinates),
                "geocoding_required": bool
            }
        """
        result = {
            "has_spatial": False,
            "type": None,
            "columns": {},
            "bounding_box": None,
            "geocoding_required": False
        }

        # Pattern 1: Explicit lat/lng columns (highest priority)
        lat_patterns = ['lat', 'latitude', 'y', 'lat_', '_lat', 'ycoord']
        lng_patterns = ['lng', 'lon', 'longitude', 'x', 'lng_', '_lng', 'long', 'xcoord']

        lat_col = self._find_column(df, lat_patterns)
        lng_col = self._find_column(df, lng_patterns)

        if lat_col and lng_col:
            print(f"[SPATIAL] Found potential coordinate columns: {lat_col}, {lng_col}")
            logger.info(f"Found potential coordinate columns: {lat_col}, {lng_col}")
            # Validate numeric and in valid range
            is_valid = self._validate_coordinates(df, lat_col, lng_col)
            print(f"[SPATIAL] Coordinate validation result: {is_valid}")
            logger.info(f"Coordinate validation result: {is_valid}")

            if is_valid:
                print(f"[SPATIAL] ✓ Detected coordinate columns: {lat_col}, {lng_col}")
                logger.info(f"Detected coordinate columns: {lat_col}, {lng_col}")
                result.update({
                    "has_spatial": True,
                    "type": "coordinates",
                    "columns": {"lat": lat_col, "lng": lng_col},
                    "bounding_box": self._calculate_bbox(df, lat_col, lng_col),
                    "geocoding_required": False
                })
                return result
            else:
                print(f"[SPATIAL] ✗ Coordinate columns found but validation failed: {lat_col}, {lng_col}")
                logger.warning(f"Coordinate columns found but validation failed: {lat_col}, {lng_col}")

        # Pattern 2: Single address column
        address_patterns = ['address', 'location', 'addr', 'street', 'place']
        address_col = self._find_column(df, address_patterns)

        if address_col:
            logger.info(f"Detected address column: {address_col}")
            result.update({
                "has_spatial": True,
                "type": "address",
                "columns": {"address": address_col},
                "geocoding_required": True
            })
            return result

        # Pattern 3: City/State/Zip columns (can geocode to centroids)
        geo_cols = {}
        for pattern, key in [
            (['city', 'municipality', 'town'], 'city'),
            (['state', 'province', 'region'], 'state'),
            (['zip', 'postal', 'zipcode', 'postcode'], 'zip'),
            (['country', 'nation'], 'country')
        ]:
            col = self._find_column(df, pattern)
            if col:
                geo_cols[key] = col

        if geo_cols:
            logger.info(f"Detected geographic columns: {geo_cols}")
            result.update({
                "has_spatial": True,
                "type": "geographic",
                "columns": geo_cols,
                "geocoding_required": True
            })
            return result

        logger.info("No spatial columns detected")
        return result

    def _find_column(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """Find column matching any pattern (case-insensitive, exact match first, then contains)"""
        # First pass: exact match
        for col in df.columns:
            col_lower = col.lower().strip()
            for pattern in patterns:
                if pattern == col_lower:
                    return col

        # Second pass: contains match (but only for multi-character patterns)
        for col in df.columns:
            col_lower = col.lower().strip()
            for pattern in patterns:
                # Only match if pattern is in the column name AND pattern is meaningful (3+ chars)
                if len(pattern) >= 3 and pattern in col_lower:
                    return col

        return None

    def _validate_coordinates(self, df: pd.DataFrame, lat_col: str, lng_col: str) -> bool:
        """Check if lat/lng are numeric and in valid ranges"""
        try:
            # Sample first few values for logging
            sample_lat = df[lat_col].head(3).tolist()
            sample_lng = df[lng_col].head(3).tolist()
            print(f"[SPATIAL] Sample lat values: {sample_lat}")
            print(f"[SPATIAL] Sample lng values: {sample_lng}")
            logger.info(f"Sample lat values: {sample_lat}")
            logger.info(f"Sample lng values: {sample_lng}")

            # Convert to numeric, coerce errors to NaN
            lat = pd.to_numeric(df[lat_col], errors='coerce')
            lng = pd.to_numeric(df[lng_col], errors='coerce')

            # Count NaN values
            lat_nan_count = lat.isna().sum()
            lng_nan_count = lng.isna().sum()
            print(f"[SPATIAL] NaN counts - lat: {lat_nan_count}/{len(lat)}, lng: {lng_nan_count}/{len(lng)}")
            logger.info(f"NaN counts - lat: {lat_nan_count}/{len(lat)}, lng: {lng_nan_count}/{len(lng)}")

            # Drop NaN values for validation
            valid_pairs = df[[lat_col, lng_col]].dropna()
            if len(valid_pairs) == 0:
                logger.warning("No valid coordinate pairs found (all NaN)")
                return False

            lat_valid = pd.to_numeric(valid_pairs[lat_col], errors='coerce')
            lng_valid = pd.to_numeric(valid_pairs[lng_col], errors='coerce')

            # Check valid ranges: lat [-90, 90], lng [-180, 180]
            valid_lat = (lat_valid >= -90) & (lat_valid <= 90)
            valid_lng = (lng_valid >= -180) & (lng_valid <= 180)

            # Count how many are in valid ranges
            valid_count = (valid_lat & valid_lng).sum()
            total_count = len(valid_pairs)

            # At least 80% should be valid
            validity_ratio = valid_count / total_count

            print(f"[SPATIAL] Coordinate validation: {valid_count}/{total_count} valid pairs ({validity_ratio:.2%})")
            logger.info(f"Coordinate validation: {valid_count}/{total_count} valid pairs ({validity_ratio:.2%})")
            return validity_ratio > 0.8
        except Exception as e:
            logger.error(f"Error validating coordinates: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _calculate_bbox(self, df: pd.DataFrame, lat_col: str, lng_col: str) -> Dict:
        """Calculate bounding box for map centering"""
        try:
            lat = pd.to_numeric(df[lat_col], errors='coerce')
            lng = pd.to_numeric(df[lng_col], errors='coerce')

            # Remove NaN values
            valid_lats = lat.dropna()
            valid_lngs = lng.dropna()

            if len(valid_lats) == 0 or len(valid_lngs) == 0:
                # Default to world view
                return {
                    "min_lat": -90,
                    "max_lat": 90,
                    "min_lng": -180,
                    "max_lng": 180
                }

            return {
                "min_lat": float(valid_lats.min()),
                "max_lat": float(valid_lats.max()),
                "min_lng": float(valid_lngs.min()),
                "max_lng": float(valid_lngs.max())
            }
        except Exception as e:
            logger.error(f"Error calculating bbox: {e}")
            return {
                "min_lat": -90,
                "max_lat": 90,
                "min_lng": -180,
                "max_lng": 180
            }

    def geocode_addresses(
        self,
        addresses: List[str],
        limit: int = 100
    ) -> List[Dict]:
        """
        Convert addresses to lat/lng coordinates using geocoding
        Limited to avoid rate limits on free Nominatim service

        Args:
            addresses: List of address strings
            limit: Max number to geocode (default 100)

        Returns:
            List of dicts with {lat, lng, formatted} or {lat: None, lng: None, formatted: None}
        """
        results = []

        for i, addr in enumerate(addresses[:limit]):
            if pd.isna(addr) or not addr or str(addr).strip() == '':
                results.append({"lat": None, "lng": None, "formatted": None})
                continue

            try:
                location = self.geocoder.geocode(str(addr), timeout=10)
                if location:
                    results.append({
                        "lat": location.latitude,
                        "lng": location.longitude,
                        "formatted": location.address
                    })
                    logger.debug(f"Geocoded: {addr} -> ({location.latitude}, {location.longitude})")
                else:
                    logger.warning(f"Could not geocode: {addr}")
                    results.append({"lat": None, "lng": None, "formatted": None})
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                logger.warning(f"Geocoding error for '{addr}': {e}")
                results.append({"lat": None, "lng": None, "formatted": None})
            except Exception as e:
                logger.error(f"Unexpected geocoding error for '{addr}': {e}")
                results.append({"lat": None, "lng": None, "formatted": None})

        return results

    def generate_kepler_config(self, spatial_info: Dict, df: pd.DataFrame) -> Dict:
        """
        Generate default Kepler.gl configuration based on detected spatial data

        Args:
            spatial_info: Output from detect_spatial_columns()
            df: The dataframe being visualized

        Returns:
            Kepler.gl configuration dict
        """
        if spatial_info["type"] != "coordinates":
            # Return empty config for non-coordinate data (needs geocoding first)
            return {}

        bbox = spatial_info.get("bounding_box")
        if not bbox:
            return {}

        # Calculate center point
        center_lat = (bbox["min_lat"] + bbox["max_lat"]) / 2
        center_lng = (bbox["min_lng"] + bbox["max_lng"]) / 2

        # Calculate zoom level based on bbox size
        lat_diff = abs(bbox["max_lat"] - bbox["min_lat"])
        lng_diff = abs(bbox["max_lng"] - bbox["min_lng"])
        max_diff = max(lat_diff, lng_diff)

        # Rough zoom estimation (Web Mercator)
        if max_diff > 50:
            zoom = 3
        elif max_diff > 10:
            zoom = 6
        elif max_diff > 1:
            zoom = 10
        elif max_diff > 0.1:
            zoom = 13
        else:
            zoom = 15

        # Get first few columns for tooltip
        tooltip_fields = list(df.columns[:5])

        config = {
            "version": "v1",
            "config": {
                "visState": {
                    "filters": [],
                    "layers": [
                        {
                            "id": "point-layer",
                            "type": "point",
                            "config": {
                                "dataId": "dataset",
                                "label": "Data Points",
                                "color": [255, 203, 153],
                                "columns": {
                                    "lat": spatial_info["columns"]["lat"],
                                    "lng": spatial_info["columns"]["lng"]
                                },
                                "isVisible": True,
                                "visConfig": {
                                    "radius": 10,
                                    "fixedRadius": False,
                                    "opacity": 0.8,
                                    "outline": False,
                                    "thickness": 2,
                                    "strokeColor": None,
                                    "colorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": [
                                            "#5A1846",
                                            "#900C3F",
                                            "#C70039",
                                            "#E3611C",
                                            "#F1920E",
                                            "#FFC300"
                                        ]
                                    },
                                    "strokeColorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": [
                                            "#5A1846",
                                            "#900C3F",
                                            "#C70039",
                                            "#E3611C",
                                            "#F1920E",
                                            "#FFC300"
                                        ]
                                    },
                                    "radiusRange": [0, 50],
                                    "filled": True
                                },
                                "hidden": False,
                                "textLabel": [
                                    {
                                        "field": None,
                                        "color": [255, 255, 255],
                                        "size": 18,
                                        "offset": [0, 0],
                                        "anchor": "start",
                                        "alignment": "center"
                                    }
                                ]
                            },
                            "visualChannels": {
                                "colorField": None,
                                "colorScale": "quantile",
                                "strokeColorField": None,
                                "strokeColorScale": "quantile",
                                "sizeField": None,
                                "sizeScale": "linear"
                            }
                        }
                    ],
                    "interactionConfig": {
                        "tooltip": {
                            "fieldsToShow": {
                                "dataset": tooltip_fields
                            },
                            "compareMode": False,
                            "compareType": "absolute",
                            "enabled": True
                        },
                        "brush": {
                            "size": 0.5,
                            "enabled": False
                        },
                        "geocoder": {
                            "enabled": False
                        },
                        "coordinate": {
                            "enabled": False
                        }
                    },
                    "layerBlending": "normal",
                    "splitMaps": [],
                    "animationConfig": {
                        "currentTime": None,
                        "speed": 1
                    }
                },
                "mapState": {
                    "bearing": 0,
                    "dragRotate": False,
                    "latitude": center_lat,
                    "longitude": center_lng,
                    "pitch": 0,
                    "zoom": zoom,
                    "isSplit": False
                },
                "mapStyle": {
                    "styleType": "dark",
                    "topLayerGroups": {},
                    "visibleLayerGroups": {
                        "label": True,
                        "road": True,
                        "border": False,
                        "building": True,
                        "water": True,
                        "land": True,
                        "3d building": False
                    },
                    "threeDBuildingColor": [
                        9.665468314072013,
                        17.18305478057247,
                        31.1442867897876
                    ],
                    "mapStyles": {}
                }
            }
        }

        logger.info(f"Generated Kepler config: center=({center_lat:.4f}, {center_lng:.4f}), zoom={zoom}")
        return config
