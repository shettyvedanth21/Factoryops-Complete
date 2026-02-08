"""Anomaly detection pipeline implementations."""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import IsolationForest
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from src.services.analytics.base import BasePipeline
from src.services.analytics.feature_engineering import FeatureEngineer

logger = structlog.get_logger()


class AnomalyDetectionPipeline(BasePipeline):
    """Pipeline for anomaly detection analytics."""
    
    def __init__(self):
        self._logger = logger.bind(pipeline="AnomalyDetection")
        self._feature_engineer = FeatureEngineer()
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        parameters: Optional[Dict[str, Any]],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for anomaly detection."""
        params = parameters or {}
        
        # Feature engineering
        features = params.get("features", ["voltage", "current", "power", "temperature"])
        df = self._feature_engineer.engineer_features(df, features)
        
        # Select feature columns
        feature_cols = [col for col in df.columns if col in features or col.endswith("_rolling")]
        
        # Split: use 70% for training, 30% for validation
        split_idx = int(len(df) * 0.7)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
        
        return train_df, test_df
    
    def train(
        self,
        train_df: pd.DataFrame,
        model_name: str,
        parameters: Optional[Dict[str, Any]],
    ) -> Any:
        """Train anomaly detection model."""
        params = parameters or {}
        
        if model_name == "isolation_forest":
            return self._train_isolation_forest(train_df, params)
        elif model_name == "autoencoder":
            return self._train_autoencoder(train_df, params)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def _train_isolation_forest(
        self,
        train_df: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Train Isolation Forest model."""
        feature_cols = params.get("feature_cols", ["voltage", "current", "power", "temperature"])
        
        # Get numeric features only
        available_cols = [col for col in feature_cols if col in train_df.columns]
        X = train_df[available_cols].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = IsolationForest(
            contamination=params.get("contamination", 0.1),
            random_state=params.get("random_state", 42),
            n_estimators=params.get("n_estimators", 100),
        )
        model.fit(X_scaled)
        
        return {
            "model": model,
            "scaler": scaler,
            "feature_cols": available_cols,
        }
    
    def _train_autoencoder(
        self,
        train_df: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Train Autoencoder model for anomaly detection."""
        feature_cols = params.get("feature_cols", ["voltage", "current", "power", "temperature"])
        
        available_cols = [col for col in feature_cols if col in train_df.columns]
        X = train_df[available_cols].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Configure hidden layers
        hidden_layers = params.get("hidden_layers", [64, 32, 16])
        
        # Train autoencoder
        model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            activation=params.get("activation", "relu"),
            max_iter=params.get("epochs", 100),
            batch_size=params.get("batch_size", 32),
            random_state=42,
        )
        model.fit(X_scaled, X_scaled)
        
        # Calculate reconstruction errors on training data
        reconstructed = model.predict(X_scaled)
        errors = np.mean((X_scaled - reconstructed) ** 2, axis=1)
        threshold = np.percentile(errors, 95)  # 95th percentile as threshold
        
        return {
            "model": model,
            "scaler": scaler,
            "threshold": threshold,
            "feature_cols": available_cols,
        }
    
    def predict(
        self,
        test_df: pd.DataFrame,
        model: Dict[str, Any],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run anomaly detection on test data."""
        scaler = model["scaler"]
        feature_cols = model["feature_cols"]
        
        X = test_df[feature_cols].values
        X_scaled = scaler.transform(X)
        
        if "model" in model and hasattr(model["model"], "predict"):
            # Autoencoder
            mlp_model = model["model"]
            reconstructed = mlp_model.predict(X_scaled)
            errors = np.mean((X_scaled - reconstructed) ** 2, axis=1)
            
            threshold = model.get("threshold", np.percentile(errors, 95))
            is_anomaly = errors > threshold
            
            return {
                "is_anomaly": is_anomaly.tolist(),
                "anomaly_score": errors.tolist(),
                "threshold": float(threshold),
                "total_anomalies": int(np.sum(is_anomaly)),
                "anomaly_percentage": float(np.mean(is_anomaly) * 100),
            }
        else:
            # Isolation Forest
            clf = model["model"]
            predictions = clf.predict(X_scaled)
            scores = clf.decision_function(X_scaled)
            
            is_anomaly = predictions == -1
            
            return {
                "is_anomaly": is_anomaly.tolist(),
                "anomaly_score": (-scores).tolist(),  # Convert to positive scores
                "total_anomalies": int(np.sum(is_anomaly)),
                "anomaly_percentage": float(np.mean(is_anomaly) * 100),
            }
    
    def evaluate(
        self,
        test_df: pd.DataFrame,
        results: Dict[str, Any],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Evaluate anomaly detection performance."""
        # For unsupervised anomaly detection, we return descriptive metrics
        total_points = len(test_df)
        anomalies = results.get("total_anomalies", 0)
        
        metrics = {
            "total_points": float(total_points),
            "anomalies_detected": float(anomalies),
            "anomaly_rate": float(anomalies / total_points * 100),
            "mean_anomaly_score": float(np.mean(results.get("anomaly_score", [0]))),
            "max_anomaly_score": float(np.max(results.get("anomaly_score", [0]))),
        }
        
        return metrics
