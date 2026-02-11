
// import { ApiError } from "@/components/ApiError";
// import { EmptyState } from "@/components/EmptyState";

// import {
//   ComposedChart,
//   LineChart,
//   Line,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Scatter,
//   Area,
// } from "recharts";

// type DatasetItem = {
//   key: string;
//   size: number;
//   last_modified: string;
// };

// type AnomalyPoint = {
//   timestamp: string;
//   anomaly_score: number;
//   is_anomaly: boolean;
// };

// type FailurePredictionPoint = {
//   timestamp: string;
//   failure_probability: number;
//   predicted_failure: boolean;
//   time_to_failure_hours: number;
// };

// type ForecastPoint = {
//   timestamp: string;
//   forecast: number;
//   lower: number;
//   upper: number;
// };

// type SupportedModels = {
//   anomaly_detection: string[];
//   failure_prediction: string[];
//   forecasting: string[];
// };

// export default function DeviceAnalyticsPage() {
//   const params = useParams();
//   const deviceId = params.deviceId as string;

//   const [datasets, setDatasets] = useState<DatasetItem[]>([]);
//   const [supportedModels, setSupportedModels] =
//     useState<SupportedModels | null>(null);

//   const [analysisType, setAnalysisType] =
//     useState<AnalyticsType>("anomaly");

//   const [models, setModels] = useState<string[]>([]);
//   const [selectedModel, setSelectedModel] = useState<string>("");

//   const [selectedDataset, setSelectedDataset] = useState<string>("");

//   const [jobId, setJobId] = useState<string | null>(null);
//   const [status, setStatus] = useState<string | null>(null);

//   const [anomalyPoints, setAnomalyPoints] = useState<AnomalyPoint[]>([]);
//   const [predictionPoints, setPredictionPoints] = useState<
//     FailurePredictionPoint[]
//   >([]);

//   const [forecastPoints, setForecastPoints] = useState<ForecastPoint[]>([]);

//   const [totalAnomalies, setTotalAnomalies] = useState<number | null>(null);
//   const [anomalyPercentage, setAnomalyPercentage] = useState<number | null>(
//     null
//   );

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
//         setSupportedModels(modelsRes);

//         if (ds.length > 0) setSelectedDataset(ds[0].key);
//       } catch (e: any) {
//         setError(e.message || "Failed to load analytics data");
//       } finally {
//         setLoading(false);
//       }
//     }

//     load();
//   }, [deviceId]);

//   /* ---------------- update model list when analysis type changes ---------------- */

//   useEffect(() => {
//     if (!supportedModels) return;

//     let list: string[] = [];

//     if (analysisType === "anomaly") {
//       list = supportedModels.anomaly_detection;
//     } else if (analysisType === "prediction") {
//       list = supportedModels.failure_prediction;
//     } else if (analysisType === "forecast") {
//       list = supportedModels.forecasting;
//     }

//     setModels(list);
//     setSelectedModel(list[0] || "");

//     setAnomalyPoints([]);
//     setPredictionPoints([]);
//     setForecastPoints([]);
//     setTotalAnomalies(null);
//     setAnomalyPercentage(null);
//     setJobId(null);
//     setStatus(null);
//   }, [analysisType, supportedModels]);

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

//           if (analysisType === "anomaly") {
//             const backendPoints: AnomalyPoint[] =
//               r?.results?.points || [];

//             setAnomalyPoints(backendPoints);
//             setTotalAnomalies(r?.results?.total_anomalies ?? 0);
//             setAnomalyPercentage(
//               r?.results?.anomaly_percentage ?? null
//             );
//           }

//           if (analysisType === "prediction") {
//             const backendPoints: FailurePredictionPoint[] =
//               r?.results?.points || [];

//             setPredictionPoints(backendPoints);
//           }

//           if (analysisType === "forecast") {
//             const timestamps: string[] =
//               r?.results?.forecast_timestamps || [];
//             const forecast: number[] = r?.results?.forecast || [];
//             const lower: number[] = r?.results?.forecast_lower || [];
//             const upper: number[] = r?.results?.forecast_upper || [];

//             const n = Math.min(
//               timestamps.length,
//               forecast.length,
//               lower.length,
//               upper.length
//             );

//             const points: ForecastPoint[] = [];

//             for (let i = 0; i < n; i++) {
//               points.push({
//                 timestamp: timestamps[i],
//                 forecast: forecast[i],
//                 lower: lower[i],
//                 upper: upper[i],
//               });
//             }

//             setForecastPoints(points);
//           }

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
//   }, [jobId, analysisType]);

//   /* ---------------- run job ---------------- */

//   async function onRun() {
//     if (!selectedDataset || !selectedModel) return;

//     try {
//       setError(null);
//       setRunning(true);
//       setStatus(null);

//       setAnomalyPoints([]);
//       setPredictionPoints([]);
//       setForecastPoints([]);
//       setTotalAnomalies(null);
//       setAnomalyPercentage(null);

//       const res = await runAnalytics({
//         device_id: deviceId,
//         analysis_type: analysisType,
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
//           <label className="block text-sm font-medium mb-1">
//             Analysis type
//           </label>
//           <select
//             className="border rounded px-3 py-2"
//             value={analysisType}
//             onChange={(e) =>
//               setAnalysisType(e.target.value as AnalyticsType)
//             }
//           >
//             <option value="anomaly">anomaly</option>
//             <option value="prediction">failure prediction</option>
//             <option value="forecast">forecast</option>
//           </select>
//         </div>

//         <div>
//           <label className="block text-sm font-medium mb-1">
//             Dataset
//           </label>
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
//           <label className="block text-sm font-medium mb-1">
//             Model
//           </label>
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
//           disabled={running || !selectedModel}
//           className="px-4 py-2 rounded bg-zinc-900 text-white disabled:opacity-60"
//         >
//           {running ? "Running..." : "Run analytics"}
//         </button>

//         {status && (
//           <div className="text-sm text-zinc-600">
//             Status: {status}
//           </div>
//         )}
//       </div>

//       {/* ---------------- anomaly UI ---------------- */}

//       {analysisType === "anomaly" && totalAnomalies !== null && (
//         <div className="flex gap-6 text-sm text-zinc-700">
//           <div>
//             Total anomalies detected:{" "}
//             <b className="text-zinc-900">{totalAnomalies}</b>
//           </div>

//           {anomalyPercentage !== null && (
//             <div>
//               Anomaly rate:{" "}
//               <b className="text-zinc-900">
//                 {anomalyPercentage.toFixed(2)}%
//               </b>
//             </div>
//           )}
//         </div>
//       )}

//       {analysisType === "anomaly" &&
//         anomalyPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "anomaly" && anomalyPoints.length > 0 && (
//         <div className="border rounded p-4">
//           <h3 className="font-medium mb-4">Anomaly score</h3>

//           <div style={{ height: 320 }}>
//             <ResponsiveContainer width="100%" height="100%">
//               <ComposedChart data={anomalyPoints}>
//                 <CartesianGrid strokeDasharray="3 3" />

//                 <XAxis
//                   dataKey="timestamp"
//                   tickFormatter={(v) =>
//                     new Date(v).toLocaleTimeString()
//                   }
//                 />

//                 <YAxis />

//                 <Tooltip
//                   labelFormatter={(v) =>
//                     new Date(v as string).toLocaleString()
//                   }
//                 />

//                 <Line
//                   type="monotone"
//                   dataKey="anomaly_score"
//                   dot={false}
//                   stroke="#2563eb"
//                 />

//                 <Scatter
//                   data={anomalyPoints.filter((p) => p.is_anomaly)}
//                   dataKey="anomaly_score"
//                   fill="#dc2626"
//                 />
//               </ComposedChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* ---------------- failure prediction UI ---------------- */}

//       {analysisType === "prediction" &&
//         predictionPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "prediction" &&
//         predictionPoints.length > 0 && (
//           <div className="border rounded p-4">
//             <h3 className="font-medium mb-4">
//               Failure prediction – probability
//             </h3>

//             <div style={{ height: 320 }}>
//               <ResponsiveContainer width="100%" height="100%">
//                 <LineChart data={predictionPoints}>
//                   <CartesianGrid strokeDasharray="3 3" />

//                   <XAxis
//                     dataKey="timestamp"
//                     tickFormatter={(v) =>
//                       new Date(v).toLocaleTimeString()
//                     }
//                   />

//                   <YAxis domain={[0, 1]} />

//                   <Tooltip
//                     labelFormatter={(v) =>
//                       new Date(v as string).toLocaleString()
//                     }
//                   />

//                   <Line
//                     type="monotone"
//                     dataKey="failure_probability"
//                     stroke="#2563eb"
//                     dot={false}
//                   />

//                   <Scatter
//                     data={predictionPoints.filter(
//                       (p) => p.predicted_failure
//                     )}
//                     dataKey="failure_probability"
//                     fill="#dc2626"
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </div>
//           </div>
//         )}

//       {/* ---------------- forecast UI ---------------- */}

//       {analysisType === "forecast" &&
//         forecastPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "forecast" &&
//         forecastPoints.length > 0 && (
//           <div className="border rounded p-4">
//             <h3 className="font-medium mb-4">
//               Forecast (with confidence interval)
//             </h3>

//             <div style={{ height: 320 }}>
//               <ResponsiveContainer width="100%" height="100%">
//                 <LineChart data={forecastPoints}>
//                   <CartesianGrid strokeDasharray="3 3" />

//                   <XAxis
//                     dataKey="timestamp"
//                     tickFormatter={(v) =>
//                       new Date(v).toLocaleTimeString()
//                     }
//                   />

//                   <YAxis />

//                   <Tooltip
//                     labelFormatter={(v) =>
//                       new Date(v as string).toLocaleString()
//                     }
//                   />

//                   <Area
//                     type="monotone"
//                     dataKey="upper"
//                     stroke="none"
//                     fill="#93c5fd"
//                     fillOpacity={0.3}
//                     name="Upper bound"
//                   />

//                   <Area
//                     type="monotone"
//                     dataKey="lower"
//                     stroke="none"
//                     fill="#ffffff"
//                     fillOpacity={1}
//                     name="Lower bound"
//                   />

//                   <Line
//                     type="monotone"
//                     dataKey="forecast"
//                     stroke="#2563eb"
//                     dot={false}
//                     name="Forecast"
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </div>
//           </div>
//         )}
//     </div>
//   );
// }




// "use client";

// import { useEffect, useState } from "react";
// import { useParams } from "next/navigation";

// import {
//   getAvailableDatasets,
//   getSupportedModels,
//   runAnalytics,
//   getAnalyticsStatus,
//   getAnalyticsResults,
//   AnalyticsType,
// } from "@/lib/analyticsApi";

// import { ApiError } from "@/components/ApiError";
// import { EmptyState } from "@/components/EmptyState";

// import {
//   ComposedChart,
//   LineChart,
//   Line,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Scatter,
//   Area,
// } from "recharts";

// type DatasetItem = {
//   key: string;
//   size: number;
//   last_modified: string;
// };

// type AnomalyPoint = {
//   timestamp: string;
//   anomaly_score: number;
//   is_anomaly: boolean;
// };

// type FailurePredictionPoint = {
//   timestamp: string;
//   failure_probability: number;
//   predicted_failure: boolean;
//   time_to_failure_hours: number;
// };

// type ForecastPoint = {
//   timestamp: string;
//   forecast: number;
//   lower: number;
//   upper: number;
// };

// type SupportedModels = {
//   anomaly_detection: string[];
//   failure_prediction: string[];
//   forecasting: string[];
// };

// export default function DeviceAnalyticsPage() {
//   const params = useParams();
//   const deviceId = params.deviceId as string;

//   const [datasets, setDatasets] = useState<DatasetItem[]>([]);
//   const [supportedModels, setSupportedModels] =
//     useState<SupportedModels | null>(null);

//   const [analysisType, setAnalysisType] =
//     useState<AnalyticsType>("anomaly");

//   const [models, setModels] = useState<string[]>([]);
//   const [selectedModel, setSelectedModel] = useState<string>("");

//   const [selectedDataset, setSelectedDataset] = useState<string>("");

//   const [jobId, setJobId] = useState<string | null>(null);
//   const [status, setStatus] = useState<string | null>(null);

//   const [anomalyPoints, setAnomalyPoints] = useState<AnomalyPoint[]>([]);
//   const [predictionPoints, setPredictionPoints] = useState<
//     FailurePredictionPoint[]
//   >([]);

//   const [forecastPoints, setForecastPoints] = useState<ForecastPoint[]>([]);

//   // ✅ forecast summary (already available in backend)
//   const [forecastMean, setForecastMean] = useState<number | null>(null);
//   const [forecastMin, setForecastMin] = useState<number | null>(null);
//   const [forecastMax, setForecastMax] = useState<number | null>(null);

//   const [totalAnomalies, setTotalAnomalies] = useState<number | null>(null);
//   const [anomalyPercentage, setAnomalyPercentage] = useState<number | null>(
//     null
//   );

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
//         setSupportedModels(modelsRes);

//         if (ds.length > 0) setSelectedDataset(ds[0].key);
//       } catch (e: any) {
//         setError(e.message || "Failed to load analytics data");
//       } finally {
//         setLoading(false);
//       }
//     }

//     load();
//   }, [deviceId]);

//   /* ---------------- update model list when analysis type changes ---------------- */

//   useEffect(() => {
//     if (!supportedModels) return;

//     let list: string[] = [];

//     if (analysisType === "anomaly") {
//       list = supportedModels.anomaly_detection;
//     } else if (analysisType === "prediction") {
//       list = supportedModels.failure_prediction;
//     } else if (analysisType === "forecast") {
//       list = supportedModels.forecasting;
//     }

//     setModels(list);
//     setSelectedModel(list[0] || "");

//     setAnomalyPoints([]);
//     setPredictionPoints([]);
//     setForecastPoints([]);

//     setForecastMean(null);
//     setForecastMin(null);
//     setForecastMax(null);

//     setTotalAnomalies(null);
//     setAnomalyPercentage(null);
//     setJobId(null);
//     setStatus(null);
//   }, [analysisType, supportedModels]);

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

//           if (analysisType === "anomaly") {
//             const backendPoints: AnomalyPoint[] =
//               r?.results?.points || [];

//             setAnomalyPoints(backendPoints);
//             setTotalAnomalies(r?.results?.total_anomalies ?? 0);
//             setAnomalyPercentage(
//               r?.results?.anomaly_percentage ?? null
//             );
//           }

//           if (analysisType === "prediction") {
//             const backendPoints: FailurePredictionPoint[] =
//               r?.results?.points || [];

//             setPredictionPoints(backendPoints);
//           }

//           if (analysisType === "forecast") {
//             const timestamps: string[] =
//               r?.results?.forecast_timestamps || [];
//             const forecast: number[] = r?.results?.forecast || [];
//             const lower: number[] = r?.results?.forecast_lower || [];
//             const upper: number[] = r?.results?.forecast_upper || [];

//             const n = Math.min(
//               timestamps.length,
//               forecast.length,
//               lower.length,
//               upper.length
//             );

//             const points: ForecastPoint[] = [];

//             for (let i = 0; i < n; i++) {
//               points.push({
//                 timestamp: timestamps[i],
//                 forecast: forecast[i],
//                 lower: lower[i],
//                 upper: upper[i],
//               });
//             }

//             setForecastPoints(points);

//             // ✅ summary numbers
//             setForecastMean(r?.results?.mean_forecast ?? null);
//             setForecastMin(r?.results?.min_forecast ?? null);
//             setForecastMax(r?.results?.max_forecast ?? null);
//           }

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
//   }, [jobId, analysisType]);

//   /* ---------------- run job ---------------- */

//   async function onRun() {
//     if (!selectedDataset || !selectedModel) return;

//     try {
//       setError(null);
//       setRunning(true);
//       setStatus(null);

//       setAnomalyPoints([]);
//       setPredictionPoints([]);
//       setForecastPoints([]);

//       setForecastMean(null);
//       setForecastMin(null);
//       setForecastMax(null);

//       setTotalAnomalies(null);
//       setAnomalyPercentage(null);

//       const res = await runAnalytics({
//         device_id: deviceId,
//         analysis_type: analysisType,
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
//           <label className="block text-sm font-medium mb-1">
//             Analysis type
//           </label>
//           <select
//             className="border rounded px-3 py-2"
//             value={analysisType}
//             onChange={(e) =>
//               setAnalysisType(e.target.value as AnalyticsType)
//             }
//           >
//             <option value="anomaly">anomaly</option>
//             <option value="prediction">failure prediction</option>
//             <option value="forecast">forecast</option>
//           </select>
//         </div>

//         <div>
//           <label className="block text-sm font-medium mb-1">
//             Dataset
//           </label>
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
//           <label className="block text-sm font-medium mb-1">
//             Model
//           </label>
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
//           disabled={running || !selectedModel}
//           className="px-4 py-2 rounded bg-zinc-900 text-white disabled:opacity-60"
//         >
//           {running ? "Running..." : "Run analytics"}
//         </button>

//         {status && (
//           <div className="text-sm text-zinc-600">
//             Status: {status}
//           </div>
//         )}
//       </div>

//       {/* ---------------- anomaly UI ---------------- */}

//       {analysisType === "anomaly" && totalAnomalies !== null && (
//         <div className="flex gap-6 text-sm text-zinc-700">
//           <div>
//             Total anomalies detected:{" "}
//             <b className="text-zinc-900">{totalAnomalies}</b>
//           </div>

//           {anomalyPercentage !== null && (
//             <div>
//               Anomaly rate:{" "}
//               <b className="text-zinc-900">
//                 {anomalyPercentage.toFixed(2)}%
//               </b>
//             </div>
//           )}
//         </div>
//       )}

//       {analysisType === "anomaly" &&
//         anomalyPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "anomaly" && anomalyPoints.length > 0 && (
//         <div className="border rounded p-4">
//           <h3 className="font-medium mb-4">Anomaly score</h3>

//           <div style={{ height: 320 }}>
//             <ResponsiveContainer width="100%" height="100%">
//               <ComposedChart data={anomalyPoints}>
//                 <CartesianGrid strokeDasharray="3 3" />

//                 <XAxis
//                   dataKey="timestamp"
//                   tickFormatter={(v) =>
//                     new Date(v).toLocaleTimeString()
//                   }
//                 />

//                 <YAxis />

//                 <Tooltip
//                   labelFormatter={(v) =>
//                     new Date(v as string).toLocaleString()
//                   }
//                 />

//                 <Line
//                   type="monotone"
//                   dataKey="anomaly_score"
//                   dot={false}
//                   stroke="#2563eb"
//                 />

//                 <Scatter
//                   data={anomalyPoints.filter((p) => p.is_anomaly)}
//                   dataKey="anomaly_score"
//                   fill="#dc2626"
//                 />
//               </ComposedChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* ---------------- failure prediction UI ---------------- */}

//       {analysisType === "prediction" &&
//         predictionPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "prediction" &&
//         predictionPoints.length > 0 && (
//           <div className="border rounded p-4">
//             <h3 className="font-medium mb-4">
//               Failure prediction – probability
//             </h3>

//             <div style={{ height: 320 }}>
//               <ResponsiveContainer width="100%" height="100%">
//                 <LineChart data={predictionPoints}>
//                   <CartesianGrid strokeDasharray="3 3" />

//                   <XAxis
//                     dataKey="timestamp"
//                     tickFormatter={(v) =>
//                       new Date(v).toLocaleTimeString()
//                     }
//                   />

//                   <YAxis domain={[0, 1]} />

//                   <Tooltip
//                     labelFormatter={(v) =>
//                       new Date(v as string).toLocaleString()
//                     }
//                   />

//                   <Line
//                     type="monotone"
//                     dataKey="failure_probability"
//                     stroke="#2563eb"
//                     dot={false}
//                   />

//                   <Scatter
//                     data={predictionPoints.filter(
//                       (p) => p.predicted_failure
//                     )}
//                     dataKey="failure_probability"
//                     fill="#dc2626"
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </div>
//           </div>
//         )}

//       {/* ---------------- forecast UI ---------------- */}

//       {analysisType === "forecast" &&
//         forecastPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "forecast" &&
//         forecastPoints.length > 0 && (
//           <div className="border rounded p-4">
//             {/* ✅ wording fix */}
//             <h3 className="font-medium mb-2">
//               Forecasted power consumption (W)
//             </h3>

//             <div style={{ height: 320 }}>
//               <ResponsiveContainer width="100%" height="100%">
//                 <LineChart data={forecastPoints}>
//                   <CartesianGrid strokeDasharray="3 3" />

//                   <XAxis
//                     dataKey="timestamp"
//                     tickFormatter={(v) =>
//                       new Date(v).toLocaleTimeString()
//                     }
//                   />

//                   <YAxis />

//                   <Tooltip
//                     labelFormatter={(v) =>
//                       new Date(v as string).toLocaleString()
//                     }
//                   />

//                   <Area
//                     type="monotone"
//                     dataKey="upper"
//                     stroke="none"
//                     fill="#93c5fd"
//                     fillOpacity={0.3}
//                     name="Upper bound"
//                   />

//                   <Area
//                     type="monotone"
//                     dataKey="lower"
//                     stroke="none"
//                     fill="#ffffff"
//                     fillOpacity={1}
//                     name="Lower bound"
//                   />

//                   <Line
//                     type="monotone"
//                     dataKey="forecast"
//                     stroke="#2563eb"
//                     dot={false}
//                     name="Forecast"
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </div>

//             {/* ✅ tiny UX summary */}
//             {(forecastMean !== null ||
//               forecastMin !== null ||
//               forecastMax !== null) && (
//               <div className="mt-4 text-sm text-zinc-700 space-y-1">
//                 {forecastMean !== null && (
//                   <div>
//                     Average predicted power:{" "}
//                     <b>{forecastMean.toFixed(2)} W</b>
//                   </div>
//                 )}
//                 {forecastMin !== null && (
//                   <div>
//                     Expected minimum:{" "}
//                     <b>{forecastMin.toFixed(2)} W</b>
//                   </div>
//                 )}
//                 {forecastMax !== null && (
//                   <div>
//                     Expected maximum:{" "}
//                     <b>{forecastMax.toFixed(2)} W</b>
//                   </div>
//                 )}

//                 <div className="text-xs text-zinc-500 pt-1">
//                   Based on historical telemetry power readings.
//                 </div>
//               </div>
//             )}
//           </div>
//         )}
//     </div>
//   );
// }



















// "use client";

// import { useEffect, useState } from "react";
// import { useParams } from "next/navigation";

// import {
//   getAvailableDatasets,
//   getSupportedModels,
//   runAnalytics,
//   getAnalyticsStatus,
//   getAnalyticsResults,
//   AnalyticsType,
// } from "@/lib/analyticsApi";

// import { runExport } from "@/lib/dataExportApi";

// import { ApiError } from "@/components/ApiError";
// import { EmptyState } from "@/components/EmptyState";

// import {
//   ComposedChart,
//   LineChart,
//   Line,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Scatter,
//   Area,
// } from "recharts";

// type DatasetItem = {
//   key: string;
//   size: number;
//   last_modified: string;
// };

// type AnomalyPoint = {
//   timestamp: string;
//   anomaly_score: number;
//   is_anomaly: boolean;
// };

// type FailurePredictionPoint = {
//   timestamp: string;
//   failure_probability: number;
//   predicted_failure: boolean;
//   time_to_failure_hours: number;
// };

// type ForecastPoint = {
//   timestamp: string;
//   forecast: number;
//   lower: number;
//   upper: number;
// };

// type SupportedModels = {
//   anomaly_detection: string[];
//   failure_prediction: string[];
//   forecasting: string[];
// };

// export default function DeviceAnalyticsPage() {
//   const params = useParams();
//   const deviceId = params.deviceId as string;

//   const [datasets, setDatasets] = useState<DatasetItem[]>([]);
//   const [supportedModels, setSupportedModels] =
//     useState<SupportedModels | null>(null);

//   const [analysisType, setAnalysisType] =
//     useState<AnalyticsType>("anomaly");

//   const [models, setModels] = useState<string[]>([]);
//   const [selectedModel, setSelectedModel] = useState<string>("");

//   const [selectedDataset, setSelectedDataset] = useState<string>("");

//   const [jobId, setJobId] = useState<string | null>(null);
//   const [status, setStatus] = useState<string | null>(null);

//   const [anomalyPoints, setAnomalyPoints] = useState<AnomalyPoint[]>([]);
//   const [predictionPoints, setPredictionPoints] = useState<
//     FailurePredictionPoint[]
//   >([]);

//   const [forecastPoints, setForecastPoints] = useState<ForecastPoint[]>([]);

//   const [forecastMean, setForecastMean] = useState<number | null>(null);
//   const [forecastMin, setForecastMin] = useState<number | null>(null);
//   const [forecastMax, setForecastMax] = useState<number | null>(null);

//   const [totalAnomalies, setTotalAnomalies] = useState<number | null>(null);
//   const [anomalyPercentage, setAnomalyPercentage] = useState<number | null>(
//     null
//   );

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
//         setSupportedModels(modelsRes);

//         if (ds.length > 0) setSelectedDataset(ds[0].key);
//       } catch (e: any) {
//         setError(e.message || "Failed to load analytics data");
//       } finally {
//         setLoading(false);
//       }
//     }

//     load();
//   }, [deviceId]);

//   /* ---------------- update model list when analysis type changes ---------------- */

//   useEffect(() => {
//     if (!supportedModels) return;

//     let list: string[] = [];

//     if (analysisType === "anomaly") {
//       list = supportedModels.anomaly_detection;
//     } else if (analysisType === "prediction") {
//       list = supportedModels.failure_prediction;
//     } else if (analysisType === "forecast") {
//       list = supportedModels.forecasting;
//     }

//     setModels(list);
//     setSelectedModel(list[0] || "");

//     setAnomalyPoints([]);
//     setPredictionPoints([]);
//     setForecastPoints([]);

//     setForecastMean(null);
//     setForecastMin(null);
//     setForecastMax(null);

//     setTotalAnomalies(null);
//     setAnomalyPercentage(null);
//     setJobId(null);
//     setStatus(null);
//   }, [analysisType, supportedModels]);

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

//           if (analysisType === "anomaly") {
//             const backendPoints: AnomalyPoint[] =
//               r?.results?.points || [];

//             setAnomalyPoints(backendPoints);
//             setTotalAnomalies(r?.results?.total_anomalies ?? 0);
//             setAnomalyPercentage(
//               r?.results?.anomaly_percentage ?? null
//             );
//           }

//           if (analysisType === "prediction") {
//             const backendPoints: FailurePredictionPoint[] =
//               r?.results?.points || [];

//             setPredictionPoints(backendPoints);
//           }

//           if (analysisType === "forecast") {
//             const timestamps: string[] =
//               r?.results?.forecast_timestamps || [];
//             const forecast: number[] = r?.results?.forecast || [];
//             const lower: number[] = r?.results?.forecast_lower || [];
//             const upper: number[] = r?.results?.forecast_upper || [];

//             const n = Math.min(
//               timestamps.length,
//               forecast.length,
//               lower.length,
//               upper.length
//             );

//             const points: ForecastPoint[] = [];

//             for (let i = 0; i < n; i++) {
//               points.push({
//                 timestamp: timestamps[i],
//                 forecast: forecast[i],
//                 lower: lower[i],
//                 upper: upper[i],
//               });
//             }

//             setForecastPoints(points);

//             setForecastMean(r?.results?.mean_forecast ?? null);
//             setForecastMin(r?.results?.min_forecast ?? null);
//             setForecastMax(r?.results?.max_forecast ?? null);
//           }

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
//   }, [jobId, analysisType]);

//   /* ---------------- run job ---------------- */

//   async function onRun() {
//     if (!selectedDataset || !selectedModel) return;

//     try {
//       setError(null);
//       setRunning(true);
//       setStatus(null);

//       setAnomalyPoints([]);
//       setPredictionPoints([]);
//       setForecastPoints([]);

//       setForecastMean(null);
//       setForecastMin(null);
//       setForecastMax(null);

//       setTotalAnomalies(null);
//       setAnomalyPercentage(null);

//       const res = await runAnalytics({
//         device_id: deviceId,
//         analysis_type: analysisType,
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

//   /* ---------------- export + refresh datasets ---------------- */

//   async function onExportAndRefresh() {
//     try {
//       setError(null);
//       setRunning(true);

//       await runExport(deviceId);

//       const datasetsRes = await getAvailableDatasets(deviceId);
//       const ds = datasetsRes.datasets || [];

//       setDatasets(ds);

//       if (ds.length > 0) {
//         setSelectedDataset(ds[0].key);
//       }
//     } catch (e: any) {
//       setError(e.message || "Export failed");
//     } finally {
//       setRunning(false);
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
//           <label className="block text-sm font-medium mb-1">
//             Analysis type
//           </label>
//           <select
//             className="border rounded px-3 py-2"
//             value={analysisType}
//             onChange={(e) =>
//               setAnalysisType(e.target.value as AnalyticsType)
//             }
//           >
//             <option value="anomaly">anomaly</option>
//             <option value="prediction">failure prediction</option>
//             <option value="forecast">forecast</option>
//           </select>
//         </div>

//         <div>
//           <label className="block text-sm font-medium mb-1">
//             Dataset
//           </label>
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
//           <label className="block text-sm font-medium mb-1">
//             Model
//           </label>
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
//           disabled={running || !selectedModel}
//           className="px-4 py-2 rounded bg-zinc-900 text-white disabled:opacity-60"
//         >
//           {running ? "Running..." : "Run analytics"}
//         </button>

//         <button
//           onClick={onExportAndRefresh}
//           disabled={running}
//           className="px-4 py-2 rounded border border-zinc-300 text-zinc-800 disabled:opacity-60"
//         >
//           Export latest data
//         </button>

//         {status && (
//           <div className="text-sm text-zinc-600">
//             Status: {status}
//           </div>
//         )}
//       </div>

//       {/* ---------------- anomaly UI ---------------- */}

//       {analysisType === "anomaly" && totalAnomalies !== null && (
//         <div className="flex gap-6 text-sm text-zinc-700">
//           <div>
//             Total anomalies detected:{" "}
//             <b className="text-zinc-900">{totalAnomalies}</b>
//           </div>

//           {anomalyPercentage !== null && (
//             <div>
//               Anomaly rate:{" "}
//               <b className="text-zinc-900">
//                 {anomalyPercentage.toFixed(2)}%
//               </b>
//             </div>
//           )}
//         </div>
//       )}

//       {analysisType === "anomaly" &&
//         anomalyPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "anomaly" && anomalyPoints.length > 0 && (
//         <div className="border rounded p-4">
//           <h3 className="font-medium mb-4">Anomaly score</h3>

//           <div style={{ height: 320 }}>
//             <ResponsiveContainer width="100%" height="100%">
//               <ComposedChart data={anomalyPoints}>
//                 <CartesianGrid strokeDasharray="3 3" />

//                 <XAxis
//                   dataKey="timestamp"
//                   tickFormatter={(v) =>
//                     new Date(v).toLocaleTimeString()
//                   }
//                 />

//                 <YAxis />

//                 <Tooltip
//                   labelFormatter={(v) =>
//                     new Date(v as string).toLocaleString()
//                   }
//                 />

//                 <Line
//                   type="monotone"
//                   dataKey="anomaly_score"
//                   dot={false}
//                   stroke="#2563eb"
//                 />

//                 <Scatter
//                   data={anomalyPoints.filter((p) => p.is_anomaly)}
//                   dataKey="anomaly_score"
//                   fill="#dc2626"
//                 />
//               </ComposedChart>
//             </ResponsiveContainer>
//           </div>
//         </div>
//       )}

//       {/* ---------------- failure prediction UI ---------------- */}

//       {analysisType === "prediction" &&
//         predictionPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "prediction" &&
//         predictionPoints.length > 0 && (
//           <div className="border rounded p-4">
//             <h3 className="font-medium mb-4">
//               Failure prediction – probability
//             </h3>

//             <div style={{ height: 320 }}>
//               <ResponsiveContainer width="100%" height="100%">
//                 <LineChart data={predictionPoints}>
//                   <CartesianGrid strokeDasharray="3 3" />

//                   <XAxis
//                     dataKey="timestamp"
//                     tickFormatter={(v) =>
//                       new Date(v).toLocaleTimeString()
//                     }
//                   />

//                   <YAxis domain={[0, 1]} />

//                   <Tooltip
//                     labelFormatter={(v) =>
//                       new Date(v as string).toLocaleString()
//                     }
//                   />

//                   <Line
//                     type="monotone"
//                     dataKey="failure_probability"
//                     stroke="#2563eb"
//                     dot={false}
//                   />

//                   <Scatter
//                     data={predictionPoints.filter(
//                       (p) => p.predicted_failure
//                     )}
//                     dataKey="failure_probability"
//                     fill="#dc2626"
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </div>
//           </div>
//         )}

//       {/* ---------------- forecast UI ---------------- */}

//       {analysisType === "forecast" &&
//         forecastPoints.length === 0 &&
//         !running && (
//           <EmptyState message="Run analytics to see results" />
//         )}

//       {analysisType === "forecast" &&
//         forecastPoints.length > 0 && (
//           <div className="border rounded p-4">
//             <h3 className="font-medium mb-2">
//               Forecasted power consumption (W)
//             </h3>

//             <div style={{ height: 320 }}>
//               <ResponsiveContainer width="100%" height="100%">
//                 <LineChart data={forecastPoints}>
//                   <CartesianGrid strokeDasharray="3 3" />

//                   <XAxis
//                     dataKey="timestamp"
//                     tickFormatter={(v) =>
//                       new Date(v).toLocaleTimeString()
//                     }
//                   />

//                   <YAxis />

//                   <Tooltip
//                     labelFormatter={(v) =>
//                       new Date(v as string).toLocaleString()
//                     }
//                   />

//                   <Area
//                     type="monotone"
//                     dataKey="upper"
//                     stroke="none"
//                     fill="#93c5fd"
//                     fillOpacity={0.3}
//                     name="Upper bound"
//                   />

//                   <Area
//                     type="monotone"
//                     dataKey="lower"
//                     stroke="none"
//                     fill="#ffffff"
//                     fillOpacity={1}
//                     name="Lower bound"
//                   />

//                   <Line
//                     type="monotone"
//                     dataKey="forecast"
//                     stroke="#2563eb"
//                     dot={false}
//                     name="Forecast"
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </div>

//             {(forecastMean !== null ||
//               forecastMin !== null ||
//               forecastMax !== null) && (
//               <div className="mt-4 text-sm text-zinc-700 space-y-1">
//                 {forecastMean !== null && (
//                   <div>
//                     Average predicted power:{" "}
//                     <b>{forecastMean.toFixed(2)} W</b>
//                   </div>
//                 )}
//                 {forecastMin !== null && (
//                   <div>
//                     Expected minimum:{" "}
//                     <b>{forecastMin.toFixed(2)} W</b>
//                   </div>
//                 )}
//                 {forecastMax !== null && (
//                   <div>
//                     Expected maximum:{" "}
//                     <b>{forecastMax.toFixed(2)} W</b>
//                   </div>
//                 )}

//                 <div className="text-xs text-zinc-500 pt-1">
//                   Based on historical telemetry power readings.
//                 </div>
//               </div>
//             )}
//           </div>
//         )}
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
  AnalyticsType,
} from "@/lib/analyticsApi";

import {
  runExport,
  getExportStatus,
} from "@/lib/dataExportApi";

import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";

import {
  ComposedChart,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Scatter,
  Area,
} from "recharts";

type DatasetItem = {
  key: string;
  size: number;
  last_modified: string;
};

type AnomalyPoint = {
  timestamp: string;
  anomaly_score: number;
  is_anomaly: boolean;
};

type FailurePredictionPoint = {
  timestamp: string;
  failure_probability: number;
  predicted_failure: boolean;
  time_to_failure_hours: number;
};

type ForecastPoint = {
  timestamp: string;
  forecast: number;
  lower: number;
  upper: number;
};

type SupportedModels = {
  anomaly_detection: string[];
  failure_prediction: string[];
  forecasting: string[];
};

export default function DeviceAnalyticsPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [supportedModels, setSupportedModels] =
    useState<SupportedModels | null>(null);

  const [analysisType, setAnalysisType] =
    useState<AnalyticsType>("anomaly");

  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");

  const [selectedDataset, setSelectedDataset] = useState<string>("");

  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const [anomalyPoints, setAnomalyPoints] = useState<AnomalyPoint[]>([]);
  const [predictionPoints, setPredictionPoints] =
    useState<FailurePredictionPoint[]>([]);

  const [forecastPoints, setForecastPoints] = useState<ForecastPoint[]>([]);

  const [forecastMean, setForecastMean] = useState<number | null>(null);
  const [forecastMin, setForecastMin] = useState<number | null>(null);
  const [forecastMax, setForecastMax] = useState<number | null>(null);

  const [totalAnomalies, setTotalAnomalies] = useState<number | null>(null);
  const [anomalyPercentage, setAnomalyPercentage] = useState<number | null>(
    null
  );

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
        setSupportedModels(modelsRes);

        if (ds.length > 0) setSelectedDataset(ds[0].key);
      } catch (e: any) {
        setError(e.message || "Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [deviceId]);

  /* ---------------- update model list ---------------- */

  useEffect(() => {
    if (!supportedModels) return;

    let list: string[] = [];

    if (analysisType === "anomaly") {
      list = supportedModels.anomaly_detection;
    } else if (analysisType === "prediction") {
      list = supportedModels.failure_prediction;
    } else if (analysisType === "forecast") {
      list = supportedModels.forecasting;
    }

    setModels(list);
    setSelectedModel(list[0] || "");

    setAnomalyPoints([]);
    setPredictionPoints([]);
    setForecastPoints([]);

    setForecastMean(null);
    setForecastMin(null);
    setForecastMax(null);

    setTotalAnomalies(null);
    setAnomalyPercentage(null);
    setJobId(null);
    setStatus(null);
  }, [analysisType, supportedModels]);

  /* ---------------- analytics polling ---------------- */

  useEffect(() => {
    if (!jobId) return;

    const timer = setInterval(async () => {
      try {
        const s = await getAnalyticsStatus(jobId);
        setStatus(s.status);

        if (s.status === "completed") {
          clearInterval(timer);

          const r = await getAnalyticsResults(jobId);

          if (analysisType === "anomaly") {
            const backendPoints: AnomalyPoint[] =
              r?.results?.points || [];

            setAnomalyPoints(backendPoints);
            setTotalAnomalies(r?.results?.total_anomalies ?? 0);
            setAnomalyPercentage(
              r?.results?.anomaly_percentage ?? null
            );
          }

          if (analysisType === "prediction") {
            const backendPoints: FailurePredictionPoint[] =
              r?.results?.points || [];

            setPredictionPoints(backendPoints);
          }

          if (analysisType === "forecast") {
            const timestamps: string[] =
              r?.results?.forecast_timestamps || [];
            const forecast: number[] = r?.results?.forecast || [];
            const lower: number[] = r?.results?.forecast_lower || [];
            const upper: number[] = r?.results?.forecast_upper || [];

            const n = Math.min(
              timestamps.length,
              forecast.length,
              lower.length,
              upper.length
            );

            const points: ForecastPoint[] = [];

            for (let i = 0; i < n; i++) {
              points.push({
                timestamp: timestamps[i],
                forecast: forecast[i],
                lower: lower[i],
                upper: upper[i],
              });
            }

            setForecastPoints(points);

            setForecastMean(r?.results?.mean_forecast ?? null);
            setForecastMin(r?.results?.min_forecast ?? null);
            setForecastMax(r?.results?.max_forecast ?? null);
          }

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
  }, [jobId, analysisType]);

  /* ---------------- run analytics ---------------- */

  async function onRun() {
    if (!selectedDataset || !selectedModel) return;

    try {
      setError(null);
      setRunning(true);
      setStatus(null);

      setAnomalyPoints([]);
      setPredictionPoints([]);
      setForecastPoints([]);

      setForecastMean(null);
      setForecastMin(null);
      setForecastMax(null);

      setTotalAnomalies(null);
      setAnomalyPercentage(null);

      const res = await runAnalytics({
        device_id: deviceId,
        analysis_type: analysisType,
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

  /* ---------------- export + wait + refresh (PERMANENT FIX) ---------------- */

  async function onExportAndRefresh() {
    try {
      setError(null);
      setRunning(true);

      await runExport(deviceId);

      const startedAt = Date.now();

      const poll = setInterval(async () => {
        try {
          const s = await getExportStatus(deviceId);

          if (s.status === "completed") {
            clearInterval(poll);

            const datasetsRes = await getAvailableDatasets(deviceId);
            const ds = datasetsRes.datasets || [];

            setDatasets(ds);

            if (ds.length > 0) {
              setSelectedDataset(ds[0].key);
            }

            setRunning(false);
          }

          if (s.status === "failed") {
            clearInterval(poll);
            setRunning(false);
            setError("Export failed");
          }

          if (Date.now() - startedAt > 60000) {
            clearInterval(poll);
            setRunning(false);
            setError("Export timeout");
          }
        } catch (e: any) {
          clearInterval(poll);
          setRunning(false);
          setError(e.message || "Failed to check export status");
        }
      }, 2000);
    } catch (e: any) {
      setRunning(false);
      setError(e.message || "Export failed");
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

      {/* ---------------- controls ---------------- */}

      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-sm font-medium mb-1">
            Analysis type
          </label>
          <select
            className="border rounded px-3 py-2"
            value={analysisType}
            onChange={(e) =>
              setAnalysisType(e.target.value as AnalyticsType)
            }
          >
            <option value="anomaly">anomaly</option>
            <option value="prediction">failure prediction</option>
            <option value="forecast">forecast</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Dataset
          </label>
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
          <label className="block text-sm font-medium mb-1">
            Model
          </label>
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
          disabled={running || !selectedModel}
          className="px-4 py-2 rounded bg-zinc-900 text-white disabled:opacity-60"
        >
          {running ? "Running..." : "Run analytics"}
        </button>

        <button
          onClick={onExportAndRefresh}
          disabled={running}
          className="px-4 py-2 rounded border border-zinc-300 text-zinc-800 disabled:opacity-60"
        >
          {running ? "Exporting..." : "Export latest data"}
        </button>

        {status && (
          <div className="text-sm text-zinc-600">
            Status: {status}
          </div>
        )}
      </div>

      {/* ---------------- anomaly ---------------- */}

      {analysisType === "anomaly" && totalAnomalies !== null && (
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

      {analysisType === "anomaly" &&
        anomalyPoints.length === 0 &&
        !running && (
          <EmptyState message="Run analytics to see results" />
        )}

      {analysisType === "anomaly" && anomalyPoints.length > 0 && (
        <div className="border rounded p-4">
          <h3 className="font-medium mb-4">Anomaly score</h3>

          <div style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={anomalyPoints}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(v) =>
                    new Date(v).toLocaleTimeString()
                  }
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(v) =>
                    new Date(v as string).toLocaleString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="anomaly_score"
                  dot={false}
                  stroke="#2563eb"
                />
                <Scatter
                  data={anomalyPoints.filter((p) => p.is_anomaly)}
                  dataKey="anomaly_score"
                  fill="#dc2626"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ---------------- prediction ---------------- */}

      {analysisType === "prediction" &&
        predictionPoints.length === 0 &&
        !running && (
          <EmptyState message="Run analytics to see results" />
        )}

      {analysisType === "prediction" &&
        predictionPoints.length > 0 && (
          <div className="border rounded p-4">
            <h3 className="font-medium mb-4">
              Failure prediction – probability
            </h3>

            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={predictionPoints}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(v) =>
                      new Date(v).toLocaleTimeString()
                    }
                  />
                  <YAxis domain={[0, 1]} />
                  <Tooltip
                    labelFormatter={(v) =>
                      new Date(v as string).toLocaleString()
                    }
                  />
                  <Line
                    type="monotone"
                    dataKey="failure_probability"
                    stroke="#2563eb"
                    dot={false}
                  />
                  <Scatter
                    data={predictionPoints.filter(
                      (p) => p.predicted_failure
                    )}
                    dataKey="failure_probability"
                    fill="#dc2626"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

      {/* ---------------- forecast ---------------- */}

      {analysisType === "forecast" &&
        forecastPoints.length === 0 &&
        !running && (
          <EmptyState message="Run analytics to see results" />
        )}

      {analysisType === "forecast" &&
        forecastPoints.length > 0 && (
          <div className="border rounded p-4">
            <h3 className="font-medium mb-2">
              Forecasted power consumption (W)
            </h3>

            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastPoints}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(v) =>
                      new Date(v).toLocaleTimeString()
                    }
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(v) =>
                      new Date(v as string).toLocaleString()
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="none"
                    fill="#93c5fd"
                    fillOpacity={0.3}
                  />
                  <Area
                    type="monotone"
                    dataKey="lower"
                    stroke="none"
                    fill="#ffffff"
                    fillOpacity={1}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    stroke="#2563eb"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {(forecastMean !== null ||
              forecastMin !== null ||
              forecastMax !== null) && (
              <div className="mt-4 text-sm text-zinc-700 space-y-1">
                {forecastMean !== null && (
                  <div>
                    Average predicted power:{" "}
                    <b>{forecastMean.toFixed(2)} W</b>
                  </div>
                )}
                {forecastMin !== null && (
                  <div>
                    Expected minimum:{" "}
                    <b>{forecastMin.toFixed(2)} W</b>
                  </div>
                )}
                {forecastMax !== null && (
                  <div>
                    Expected maximum:{" "}
                    <b>{forecastMax.toFixed(2)} W</b>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

    </div>
  );
}