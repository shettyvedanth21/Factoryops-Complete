from enum import Enum


class Intent(str, Enum):
    WHATIF_QUERY = "WHATIF_QUERY"
    FORECAST_QUERY = "FORECAST_QUERY"
    OPTIMISE_QUERY = "OPTIMISE_QUERY"
    ANOMALY_QUERY = "ANOMALY_QUERY"
    COMPARE_QUERY = "COMPARE_QUERY"
    HISTORICAL_QUERY = "HISTORICAL_QUERY"
    GENERAL_QUERY = "GENERAL_QUERY"


class IntentClassifier:
    def classify(self, user_text: str) -> Intent:
        text = (user_text or "").lower()

        if any(k in text for k in ["what if", "what-if", "tariff", "efficiency", "idle reduction", "downtime"]):
            return Intent.WHATIF_QUERY
        if any(k in text for k in ["forecast", "predict", "projection", "next month", "future"]):
            return Intent.FORECAST_QUERY
        if any(k in text for k in ["optimize", "optimise", "improve", "reduce cost", "recommend"]):
            return Intent.OPTIMISE_QUERY
        if any(k in text for k in ["anomaly", "outlier", "abnormal", "spike", "pressure", "voltage"]):
            return Intent.ANOMALY_QUERY
        if any(k in text for k in ["compare", "versus", "vs", "between"]):
            return Intent.COMPARE_QUERY
        if any(k in text for k in ["history", "historical", "trend", "past", "last"]):
            return Intent.HISTORICAL_QUERY
        return Intent.GENERAL_QUERY
