"""Data serializers."""

import json
from datetime import datetime
from typing import Any, Dict

import numpy as np
import pandas as pd


class AnalyticsJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for analytics data."""
    
    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)


def serialize_results(results: Dict[str, Any]) -> str:
    """Serialize results to JSON string."""
    return json.dumps(results, cls=AnalyticsJSONEncoder)


def deserialize_results(json_str: str) -> Dict[str, Any]:
    """Deserialize results from JSON string."""
    return json.loads(json_str)
