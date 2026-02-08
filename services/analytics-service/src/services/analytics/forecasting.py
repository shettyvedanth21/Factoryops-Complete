"""Forecasting pipeline implementations."""

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import structlog
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.services.analytics.base import BasePipeline

logger = structlog.get_logger()


class ForecastingPipeline(BasePipeline):
    """Pipeline for time series forecasting."""
    
    def __init__(self):
        self._logger = logger.bind(pipeline="Forecasting")
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        parameters: Optional[Dict[str, Any]],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for forecasting."""
        params = parameters or {}
        
        target_col = params.get("target_column", "power")
        timestamp_col = params.get("timestamp_column", "_time")
        
        # Ensure timestamp is datetime
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        elif "timestamp" in df.columns:
            df[timestamp_col] = pd.to_datetime(df["timestamp"])
            timestamp_col = "timestamp"
        
        # Sort by time
        df = df.sort_values(by=timestamp_col)
        
        # Split: use last 20% for validation
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()
        
        return train_df, test_df
    
    def train(
        self,
        train_df: pd.DataFrame,
        model_name: str,
        parameters: Optional[Dict[str, Any]],
    ) -> Any:
        """Train forecasting model."""
        params = parameters or {}
        
        if model_name == "prophet":
            return self._train_prophet(train_df, params)
        elif model_name == "arima":
            return self._train_arima(train_df, params)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def _train_prophet(
        self,
        train_df: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Train Prophet forecasting model."""
        timestamp_col = params.get("timestamp_column", "_time")
        target_col = params.get("target_column", "power")
        
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = pd.DataFrame({
            "ds": pd.to_datetime(train_df[timestamp_col]),
            "y": train_df[target_col].values,
        })
        
        # Configure model
        model = Prophet(
            daily_seasonality=params.get("daily_seasonality", True),
            weekly_seasonality=params.get("weekly_seasonality", True),
            yearly_seasonality=params.get("yearly_seasonality", False),
        )
        
        model.fit(prophet_df)
        
        return {
            "model": model,
            "target_col": target_col,
            "timestamp_col": timestamp_col,
        }
    
    def _train_arima(
        self,
        train_df: pd.DataFrame,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Train ARIMA forecasting model."""
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            logger.error("statsmodels not installed, cannot use ARIMA")
            raise
        
        target_col = params.get("target_column", "power")
        y = train_df[target_col].values
        
        order = params.get("order", [1, 1, 1])
        seasonal_order = params.get("seasonal_order", [1, 1, 1, 24])
        
        model = ARIMA(
            y,
            order=tuple(order),
            seasonal_order=tuple(seasonal_order),
        )
        
        fitted_model = model.fit()
        
        return {
            "model": fitted_model,
            "target_col": target_col,
            "order": order,
        }
    
    def predict(
        self,
        test_df: pd.DataFrame,
        model: Dict[str, Any],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate forecasts."""
        params = parameters or {}
        forecast_periods = params.get("forecast_periods", len(test_df))
        
        if "model" in model and hasattr(model["model"], "predict"):
            # ARIMA model
            return self._predict_arima(test_df, model, forecast_periods)
        else:
            # Prophet model
            return self._predict_prophet(test_df, model, forecast_periods)
    
    def _predict_prophet(
        self,
        test_df: pd.DataFrame,
        model: Dict[str, Any],
        periods: int,
    ) -> Dict[str, Any]:
        """Generate Prophet forecasts."""
        prophet_model = model["model"]
        target_col = model["target_col"]
        timestamp_col = model["timestamp_col"]
        
        # Create future dataframe
        future = prophet_model.make_future_dataframe(
            periods=periods,
            freq=params.get("freq", "H"),
        )
        
        forecast = prophet_model.predict(future)
        
        # Extract predictions
        forecast_values = forecast["yhat"].tail(periods).values
        forecast_lower = forecast["yhat_lower"].tail(periods).values
        forecast_upper = forecast["yhat_upper"].tail(periods).values
        
        return {
            "forecast": forecast_values.tolist(),
            "forecast_lower": forecast_lower.tolist(),
            "forecast_upper": forecast_upper.tolist(),
            "forecast_timestamps": forecast["ds"].tail(periods).dt.strftime("%Y-%m-%d %H:%M:%S").tolist(),
            "mean_forecast": float(np.mean(forecast_values)),
            "max_forecast": float(np.max(forecast_values)),
            "min_forecast": float(np.min(forecast_values)),
        }
    
    def _predict_arima(
        self,
        test_df: pd.DataFrame,
        model: Dict[str, Any],
        periods: int,
    ) -> Dict[str, Any]:
        """Generate ARIMA forecasts."""
        arima_model = model["model"]
        
        # Get forecast
        forecast_result = arima_model.get_forecast(steps=periods)
        forecast_mean = forecast_result.predicted_mean
        forecast_conf_int = forecast_result.conf_int()
        
        return {
            "forecast": forecast_mean.tolist(),
            "forecast_lower": forecast_conf_int.iloc[:, 0].tolist(),
            "forecast_upper": forecast_conf_int.iloc[:, 1].tolist(),
            "mean_forecast": float(np.mean(forecast_mean)),
            "max_forecast": float(np.max(forecast_mean)),
            "min_forecast": float(np.min(forecast_mean)),
        }
    
    def evaluate(
        self,
        test_df: pd.DataFrame,
        results: Dict[str, Any],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Evaluate forecasting performance."""
        target_col = parameters.get("target_column", "power")
        
        y_true = test_df[target_col].values
        y_pred = np.array(results["forecast"])
        
        # Calculate metrics
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        metrics = {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "mean_actual": float(np.mean(y_true)),
            "mean_predicted": float(np.mean(y_pred)),
        }
        
        return metrics
