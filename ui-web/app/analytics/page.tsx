"use client";

import { useEffect, useState } from "react";

import {
  runAnalytics,
  getAnalyticsStatus,
  getAnalyticsResults,
  getSupportedModels,
  AnalyticsType,
} from "@/lib/analyticsApi";

export default function AnalyticsPage() {

  const [deviceId, setDeviceId] = useState("D1");

  // ✅ FIX: backend expects: "anomaly" | "prediction" | "forecast"
  const [analysisType, setAnalysisType] =
    useState<AnalyticsType>("anomaly");

  const [modelName, setModelName] = useState("");
  const [models, setModels] = useState<any>(null);

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ---------------- load models ---------------- */

  useEffect(() => {
    getSupportedModels()
      .then(setModels)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!models) return;

    const list = models[analysisType] || [];

    setModelName(list[0] ?? "");
  }, [analysisType, models]);

  /* ---------------- poll job ---------------- */

  useEffect(() => {
    if (!jobId) return;

    const t = setInterval(async () => {
      try {
        const s = await getAnalyticsStatus(jobId);
        setStatus(s.status);

        if (s.status === "completed") {
          clearInterval(t);
          const r = await getAnalyticsResults(jobId);
          setResults(r);
        }

        if (s.status === "failed") {
          clearInterval(t);
        }

      } catch (e: any) {
        setError(e.message);
        clearInterval(t);
      }
    }, 2000);

    return () => clearInterval(t);
  }, [jobId]);

  /* ---------------- run job ---------------- */

  const handleRun = async () => {
    setError(null);
    setResults(null);
    setStatus(null);

    if (!modelName) {
      setError("Model not selected");
      return;
    }

    if (!startDate || !endDate) {
      setError("Please select date range");
      return;
    }

    try {
      setLoading(true);

      const res = await runAnalytics({
        device_id: deviceId,

        // ✅ FIX: send correct enum to backend
        analysis_type: analysisType,

        model_name: modelName,
        date_range_start: startDate,
        date_range_end: endDate,
      });

      setJobId(res.job_id);
      setStatus(res.status);

    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">

      <h2 className="text-lg font-semibold">
        Analytics
      </h2>

      {/* ---------------- form ---------------- */}

      <div className="space-y-4 max-w-xl">

        <div>
          <label className="block text-sm">Device ID</label>
          <input
            className="border px-3 py-1 rounded w-full"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm">Analysis type</label>
          <select
            className="border px-3 py-1 rounded w-full"
            value={analysisType}
            onChange={(e) =>
              setAnalysisType(e.target.value as AnalyticsType)
            }
          >
            {/* ✅ FIXED VALUES */}
            <option value="anomaly">Anomaly detection</option>
            <option value="prediction">Failure prediction</option>
            <option value="forecast">Forecasting</option>
          </select>
        </div>

        <div>
          <label className="block text-sm">Model</label>
          <select
            className="border px-3 py-1 rounded w-full"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
          >
            {models &&
              (models[analysisType] || []).map((m: string) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm">Start date</label>
            <input
              type="datetime-local"
              className="border px-3 py-1 rounded w-full"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm">End date</label>
            <input
              type="datetime-local"
              className="border px-3 py-1 rounded w-full"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Run analytics
        </button>

        {error && (
          <div className="text-red-600 text-sm">{error}</div>
        )}

      </div>

      {/* ---------------- status ---------------- */}

      {jobId && (
        <div className="text-sm">
          Job ID: {jobId} <br />
          Status: {status}
        </div>
      )}

      {/* ---------------- results ---------------- */}

      {results && (
        <div>
          <h3 className="font-medium mb-2">
            Results
          </h3>

          <pre className="bg-zinc-100 dark:bg-zinc-900 p-4 rounded text-xs overflow-auto">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}