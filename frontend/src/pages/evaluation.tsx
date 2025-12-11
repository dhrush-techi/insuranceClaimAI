import React, { useEffect, useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from "recharts";

// --- Types ---
interface MetricMap {
  [key: string]: number | string | MetricMap;
}

interface EvaluationData {
  decision_metrics: MetricMap;
  evidence_metrics: MetricMap;
  calibration_metrics: MetricMap;
  explainability_metrics: MetricMap;
  improvement_metrics: MetricMap;
  pattern_metrics: MetricMap;
}

interface ChartItem {
  name: string;
  value: number;
  fullValue: string | number | MetricMap;
}

// --- DARK MODE Styles ---
const styles = {
  container: { padding: "2rem", fontFamily: "system-ui, sans-serif", backgroundColor: "#0d1117", minHeight: "100vh", color: "#e6edf3" },
  header: { marginBottom: "2rem", borderBottom: "1px solid #30363d", paddingBottom: "1rem" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(450px, 1fr))", gap: "1.5rem" },
  card: { backgroundColor: "#161b22", padding: "1.5rem", borderRadius: "12px", boxShadow: "0 4px 10px rgba(0,0,0,0.4)", display: "flex", flexDirection: "column" as const, minHeight: "350px", border: "1px solid #30363d" },
  cardTitle: { marginTop: 0, fontSize: "1.1rem", color: "#e6edf3", marginBottom: "1rem", borderLeft: "4px solid #00b4ff", paddingLeft: "10px" },
  kpiGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "10px", marginBottom: "1rem" },
  kpiBox: { padding: "10px", background: "#1c2128", borderRadius: "8px", textAlign: "center" as const, border: "1px solid #30363d" },
  kpiValue: { fontSize: "1.2rem", fontWeight: "bold", color: "#3ddc97" },
  kpiLabel: { fontSize: "0.75rem", color: "#8b949e", marginTop: "4px", textTransform: "uppercase" as const },
  tableContainer: { flex: 1, overflowY: "auto" as const },
  table: { width: "100%", borderCollapse: "collapse" as const, fontSize: "0.9rem", color: "#e6edf3" },
  th: { textAlign: "left" as const, padding: "8px", borderBottom: "2px solid #30363d", color: "#8b949e", fontSize: "0.8rem" },
  td: { padding: "8px", borderBottom: "1px solid #21262d", color: "#e6edf3" },
  loading: { display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", fontSize: "1.2rem", color: "#8b949e" }
};

// --- Colors for Pie Charts ---
const COLORS = ['#00b4ff', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

// --- Helper Functions ---
const formatKey = (key: string) => key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());

const renderValue = (val: string | number | MetricMap): string | number => {
  if (typeof val === 'object' && val !== null) return JSON.stringify(val);
  if (typeof val === 'number' && !Number.isInteger(val)) return val.toFixed(4);
  return val;
};

const processData = (metrics: any): ChartItem[] => {
  if (!metrics) return [];
  return Object.keys(metrics).map((key) => {
    const val = metrics[key];
    const parsed = typeof val === 'string' ? parseFloat(val) : val;
    return {
      name: formatKey(key),
      value: (typeof parsed === 'number' && !isNaN(parsed)) ? parsed : 0,
      fullValue: val
    };
  });
};

export default function EvaluationPage() {
  const [data, setData] = useState<EvaluationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/evaluation")
      .then(res => res.json())
      .then(setData)
      .catch(err => console.error("Fetch error:", err))
      .finally(() => setLoading(false));
  }, []);

  const decisionData = useMemo(() => processData(data?.decision_metrics), [data]);
  const evidenceData = useMemo(() => processData(data?.evidence_metrics), [data]);
  const calibrationData = useMemo(() => processData(data?.calibration_metrics), [data]);
  const explainabilityData = useMemo(() => processData(data?.explainability_metrics), [data]);
  const improvementData = useMemo(() => processData(data?.improvement_metrics), [data]);
  const patternData = useMemo(() => processData(data?.pattern_metrics).filter(i => i.value > 0), [data]);

  if (loading) return <div style={styles.loading}>Loading System Analytics...</div>;
  if (!data) return <div style={styles.loading}>No Data Available</div>;

  return (
    <div style={styles.container}>

      <header style={styles.header}>
        <h1 style={{ margin: 0, color: "#e6edf3" }}>System Evaluation Dashboard</h1>
        <p style={{ margin: "5px 0 0", color: "#8b949e" }}>Live AI Performance Metrics</p>
      </header>

      <div style={styles.grid}>

        {/* DECISION METRICS */}
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Decision Metrics</h2>
          <div style={{ flex: 1, minHeight: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={decisionData}>
                <CartesianGrid stroke="#30363d" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#e6edf3" }} />
                <YAxis tick={{ fill: "#e6edf3" }} />
                <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3" }} />
                <Bar dataKey="value" fill="#4dabf7" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* EXPLAINABILITY */}
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Explainability Score</h2>
          <div style={{ flex: 1, minHeight: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={explainabilityData}>
                <PolarGrid stroke="#30363d" />
                <PolarAngleAxis dataKey="name" tick={{ fontSize: 11, fill: "#e6edf3" }} />
                <PolarRadiusAxis tick={{ fill: "#e6edf3" }} />
                <Radar name="Score" dataKey="value" stroke="#38d9a9" fill="#38d9a9" fillOpacity={0.6} />
                <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3" }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* CALIBRATION */}
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Calibration Metrics</h2>
          <div style={{ flex: 1, minHeight: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={calibrationData}>
                <defs>
                  <linearGradient id="colorCal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ffc658" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ffc658" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#30363d" />
                <XAxis dataKey="name" tick={{ fill: "#e6edf3" }} />
                <YAxis tick={{ fill: "#e6edf3" }} />
                <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3" }} />
                <Area type="monotone" dataKey="value" stroke="#ffc658" fillOpacity={1} fill="url(#colorCal)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* PATTERN */}
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Pattern Recognition Distribution</h2>
          <div style={{ flex: 1, minHeight: 250 }}>
            {patternData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={patternData} cx="50%" cy="50%" innerRadius={60} outerRadius={80}
                       paddingAngle={5} dataKey="value">
                    {patternData.map((entry, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3" }} />
                  <Legend wrapperStyle={{ color: "#e6edf3" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <tbody>
                    {Object.entries(data.pattern_metrics).map(([k, v], i) => (
                      <tr key={i}>
                        <td style={styles.td}><strong>{formatKey(k)}</strong></td>
                        <td style={styles.td}>{renderValue(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {/* IMPROVEMENT */}
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Improvement Over Baseline</h2>
          <div style={styles.kpiGrid}>
            {improvementData.slice(0, 3).map((item) => (
              <div key={item.name} style={styles.kpiBox}>
                <div style={styles.kpiLabel}>{item.name}</div>
                <div style={{...styles.kpiValue, color: item.value >= 0 ? '#3ddc97' : '#ff6b6b'}}>
                  {item.value > 0 ? '+' : ''}{item.value}%
                </div>
              </div>
            ))}
          </div>
          <div style={{ flex: 1, minHeight: 150 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={improvementData}>
                <CartesianGrid stroke="#30363d" />
                <XAxis dataKey="name" hide />
                <YAxis tick={{ fill: "#e6edf3" }} />
                <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", color: "#e6edf3" }} />
                <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* EVIDENCE */}
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Evidence Metrics</h2>
          <div style={styles.tableContainer}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Metric Name</th>
                  <th style={styles.th}>Details</th>
                </tr>
              </thead>
              <tbody>
                {evidenceData.map((item, idx) => {
                  const isNested = typeof item.fullValue === 'object' && item.fullValue !== null;
                  return (
                    <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? "#161b22" : "#1c2128" }}>
                      <td style={styles.td}>{item.name}</td>
                      <td style={styles.td}>
                        {isNested ? (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {Object.entries(item.fullValue as MetricMap).map(([subKey, subVal]) => (
                              <div key={subKey} style={{
                                backgroundColor: "#1c7ed6",
                                color: "white",
                                borderRadius: "4px",
                                padding: "4px 8px",
                                fontSize: "0.8rem"
                              }}>
                                {formatKey(subKey)}: {String(subVal)}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span style={{ fontFamily: "monospace" }}>{renderValue(item.fullValue)}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

      </div>

    </div>
  );
}
