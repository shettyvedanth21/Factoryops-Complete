// "use client";

// import { useEffect, useState } from "react";
// import { useParams } from "next/navigation";

// import {
//   getAvailableDatasets,
//   getSupportedModels,
//   runAnalytics,
//   getAnalyticsStatus,
//   getAnalyticsResults,
// } from "@/lib/analyticsApi";

// import { ApiError } from "@/components/ApiError";
// import { EmptyState } from "@/components/EmptyState";

// import {
//   ComposedChart,
//   Line,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Scatter,
// } from "recharts";

// type DatasetItem = {
//   key: string;
//   size: number;
//   last_modified: string;
// };

// type Point = {
//   x: number;
//   anomaly_score: number;
//   is_anomaly: boolean;
// };

// export default function DeviceAnalyticsPage() {
//   const params = useParams();
//   const deviceId = params.deviceId as string;

//   const [datasets, setDatasets] = useState<DatasetItem[]>([]);
//   const [models, setModels] = useState<string[]>([]);

//   const [selectedDataset, setSelectedDataset] = useState<string>("");
//   const [selectedModel, setSelectedModel] = useState<string>("");

//   const [jobId, setJobId] = useState<string | null>(null);
//   const [status, setStatus] = useState<string | null>(null);

//   const [points, setPoints] = useState<Point[]>([]);

//   const [loading, setLoading] = useState(true);
//   const [running, setRunning] = useState(false);
//   const [error, setError] = useState<string | null>(null);

//   /* ---------------- load datasets & models ---------------- */

//   useEffect(() => {
//     async function load() {
//       try {
//         setLoading(true);

//         const datasetsRes = await getAvailableDatasets(deviceId);
//         const modelsRes = await getSupportedModels();

//         const ds = datasetsRes.datasets || [];
//         setDatasets(ds);

//         if (ds.length > 0) {
//           setSelectedDataset(ds[0].key);
//         }

//         setModels(modelsRes || []);
//         if (modelsRes?.length) {
//           setSelectedModel(modelsRes[0]);
//         }
//       } catch (e: any) {
//         setError(e.message || "Failed to load analytics data");
//       } finally {
//         setLoading(false);
//       }
//     }

//     load();
//   }, [deviceId]);

//   /* ---------------- polling ---------------- */

//   useEffect(() => {
//     if (!jobId) return;

//     const timer = setInterval(async () => {
//       try {
//         const s = await getAnalyticsStatus(jobId);
//         setStatus(s.status);

//         if (s.status === "completed") {
//           clearInterval(timer);

//           const r = await getAnalyticsResults(jobId);

//           const scores: number[] = r?.results?.anomaly_score || [];
//           const flags: boolean[] = r?.results?.is_anomaly || [];

//           const builtPoints: Point[] = scores.map((v, i) => ({
//             x: i,
//             anomaly_score: v,
//             is_anomaly: Boolean(flags[i]),
//           }));

//           setPoints(builtPoints);
//           setRunning(false);
//         }

//         if (s.status === "failed") {
//           clearInterval(timer);
//           setRunning(false);
//           setError("Analytics job failed");
//         }
//       } catch (e: any) {
//         clearInterval(timer);
//         setRunning(false);
//         setError(e.message || "Polling failed");
//       }
//     }, 2000);

//     return () => clearInterval(timer);
//   }, [jobId]);

//   /* ---------------- run job ---------------- */

//   async function onRun() {
//     if (!selectedDataset || !selectedModel) return;

//     try {
//       setError(null);
//       setRunning(true);
//       setPoints([]);
//       setStatus(null);

//       const res = await runAnalytics({
//         device_id: deviceId,
//         analysis_type: "anomaly",
//         model_name: selectedModel,
//         dataset_key: selectedDataset,
//       });

//       setJobId(res.job_id);
//       setStatus(res.status);
//     } catch (e: any) {
//       setRunning(false);
//       setError(e.message || "Failed to start analytics job");
//     }
//   }

//   /* ---------------- render ---------------- */

//   if (loading) {
//     return (
//       <div className="flex items-center justify-center h-64">
//         <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900" />
//         <p className="ml-4">Loading...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return <ApiError message={error} />;
//   }

//   if (!datasets.length) {
//     return <EmptyState message="No datasets available for this device" />;
//   }

//   return (
//     <div className="space-y-6">
//       {/* controls */}
//       <div className="flex flex-wrap gap-4 items-end">
//         <div>
//           <label className="block text-sm font-medium mb-1">Dataset</label>
//           <select
//             className="border rounded px-3 py-2 min-w-[320px]"
//             value={selectedDataset}
//             onChange={(e) => setSelectedDataset(e.target.value)}
//           >
//             {datasets.map((d) => (
//               <option key={d.key} value={d.key}>
//                 {d.key}
//               </option>
//             ))}
//           </select>
//         </div>

//         <div>
//           <label className="block text-sm font-medium mb-1">Model</label>
//           <select
//             className="border rounded px-3 py-2"
//             value={selectedModel}
//             onChange={(e) => setSelectedModel(e.target.value)}
//           >
//             {models.map((m) => (
//               <option key={m} value={m}>
//                 {m}
//               </option>
//             ))}
//           </select>
//         </div>

//         <button
//           onClick={onRun}
//           disabled={running}
//           className="px-4 py-2 rounded bg-zinc-900 text-white disabled:opacity-60"
//         >
//           {running ? "Running..." : "Run analytics"}
//         </button>

//         {status && (
//           <div className="text-sm text-zinc-600">Status: {status}</div>
//         )}
//       </div>

//       {points.length === 0 && !running && (
//         <EmptyState message="Run analytics to see results" />
//       )}

//       {points.length > 0 && (
//         <div className="border rounded p-4">
//           <h3 className="font-medium mb-4">Anomaly score</h3>

//           {/* ✅ IMPORTANT FIX – fixed height */}
//           <div style={{ height: 320 }}>
//             <ResponsiveContainer width="100%" height="100%">
//               <ComposedChart data={points}>
//                 <CartesianGrid strokeDasharray="3 3" />

//                 <XAxis dataKey="x" />

//                 <YAxis />
//                 <Tooltip />

//                 <Line
//                   type="monotone"
//                   dataKey="anomaly_score"
//                   dot={false}
//                   stroke="#2563eb"
//                 />

//                 <Scatter
//                   data={points.filter((p) => p.is_anomaly)}
//                   dataKey="anomaly_score"
//                   xAxisId={0}
//                   yAxisId={0}
//                   fill="#dc2626"
//                   line={false}
//                 />
//               </ComposedChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }













"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import {
  getAvailableDatasets,
  getSupportedModels,
  runAnalytics,
  getAnalyticsStatus,
  getAnalyticsResults,
} from "@/lib/analyticsApi";

import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";

import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Scatter,
} from "recharts";

type DatasetItem = {
  key: string;
  size: number;
  last_modified: string;
};

type Point = {
  x: number;
  anomaly_score: number;
  is_anomaly: boolean;
};

export default function DeviceAnalyticsPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [models, setModels] = useState<string[]>([]);

  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");

  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const [points, setPoints] = useState<Point[]>([]);

  // ✅ NEW – summary values
  const [totalAnomalies, setTotalAnomalies] = useState<number | null>(null);
  const [anomalyPercentage, setAnomalyPercentage] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ---------------- load datasets & models ---------------- */

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);

        const datasetsRes = await getAvailableDatasets(deviceId);
        const modelsRes = await getSupportedModels();

        const ds = datasetsRes.datasets || [];
        setDatasets(ds);

        if (ds.length > 0) {
          setSelectedDataset(ds[0].key);
        }

        setModels(modelsRes || []);
        if (modelsRes?.length) {
          setSelectedModel(modelsRes[0]);
        }
      } catch (e: any) {
        setError(e.message || "Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [deviceId]);

  /* ---------------- polling ---------------- */

  useEffect(() => {
    if (!jobId) return;

    const timer = setInterval(async () => {
      try {
        const s = await getAnalyticsStatus(jobId);
        setStatus(s.status);

        if (s.status === "completed") {
          clearInterval(timer);

          const r = await getAnalyticsResults(jobId);

          const scores: number[] = r?.results?.anomaly_score || [];
          const flags: boolean[] = r?.results?.is_anomaly || [];

          const builtPoints: Point[] = scores.map((v, i) => ({
            x: i,
            anomaly_score: v,
            is_anomaly: Boolean(flags[i]),
          }));

          setPoints(builtPoints);

          // ✅ NEW – read backend summary
          setTotalAnomalies(r?.results?.total_anomalies ?? 0);
          setAnomalyPercentage(r?.results?.anomaly_percentage ?? null);

          setRunning(false);
        }

        if (s.status === "failed") {
          clearInterval(timer);
          setRunning(false);
          setError("Analytics job failed");
        }
      } catch (e: any) {
        clearInterval(timer);
        setRunning(false);
        setError(e.message || "Polling failed");
      }
    }, 2000);

    return () => clearInterval(timer);
  }, [jobId]);

  /* ---------------- run job ---------------- */

  async function onRun() {
    if (!selectedDataset || !selectedModel) return;

    try {
      setError(null);
      setRunning(true);
      setPoints([]);
      setStatus(null);

      // ✅ reset summaries
      setTotalAnomalies(null);
      setAnomalyPercentage(null);

      const res = await runAnalytics({
        device_id: deviceId,
        analysis_type: "anomaly",
        model_name: selectedModel,
        dataset_key: selectedDataset,
      });

      setJobId(res.job_id);
      setStatus(res.status);
    } catch (e: any) {
      setRunning(false);
      setError(e.message || "Failed to start analytics job");
    }
  }

  /* ---------------- render ---------------- */

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900" />
        <p className="ml-4">Loading...</p>
      </div>
    );
  }

  if (error) {
    return <ApiError message={error} />;
  }

  if (!datasets.length) {
    return <EmptyState message="No datasets available for this device" />;
  }

  return (
    <div className="space-y-6">
      {/* controls */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-sm font-medium mb-1">Dataset</label>
          <select
            className="border rounded px-3 py-2 min-w-[320px]"
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
          >
            {datasets.map((d) => (
              <option key={d.key} value={d.key}>
                {d.key}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Model</label>
          <select
            className="border rounded px-3 py-2"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onRun}
          disabled={running}
          className="px-4 py-2 rounded bg-zinc-900 text-white disabled:opacity-60"
        >
          {running ? "Running..." : "Run analytics"}
        </button>

        {status && (
          <div className="text-sm text-zinc-600">Status: {status}</div>
        )}
      </div>

      {/* ✅ SUMMARY */}
      {totalAnomalies !== null && (
        <div className="flex gap-6 text-sm text-zinc-700">
          <div>
            Total anomalies detected:{" "}
            <b className="text-zinc-900">{totalAnomalies}</b>
          </div>

          {anomalyPercentage !== null && (
            <div>
              Anomaly rate:{" "}
              <b className="text-zinc-900">
                {anomalyPercentage.toFixed(2)}%
              </b>
            </div>
          )}
        </div>
      )}

      {points.length === 0 && !running && (
        <EmptyState message="Run analytics to see results" />
      )}

      {points.length > 0 && (
        <div className="border rounded p-4">
          <h3 className="font-medium mb-4">Anomaly score</h3>

          <div style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={points}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="x" />

                <YAxis />
                <Tooltip />

                <Line
                  type="monotone"
                  dataKey="anomaly_score"
                  dot={false}
                  stroke="#2563eb"
                />

                <Scatter
                  data={points.filter((p) => p.is_anomaly)}
                  dataKey="anomaly_score"
                  xAxisId={0}
                  yAxisId={0}
                  fill="#dc2626"
                  line={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}