import { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import axios from "axios";

function StatCard({ label, value, sub }) {
  return (
    <div className="p-6 card-accent"
      style={{ backgroundColor: "#F7F4EE", border: "1px solid #DDD6C8" }}>
      <p className="text-xs uppercase tracking-widest mb-4"
        style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
        {label}
      </p>
      <p className="font-display text-3xl font-medium mb-1" style={{ color: "#0D0D0D" }}>
        {value}
      </p>
      {sub && <p className="text-xs" style={{ color: "#8C8C8C", lineHeight: "1.6" }}>{sub}</p>}
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get("/api/analytics");
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAnalytics(); }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-32">
      <div className="text-center">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-3" style={{ color: "#8C8C8C" }} />
        <p className="text-xs uppercase tracking-widest"
          style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
          Loading
        </p>
      </div>
    </div>
  );

  if (error) return (
    <div className="p-8" style={{ border: "1px solid #DDD6C8", borderTop: "2px solid #8B1A1A" }}>
      <p className="text-sm" style={{ color: "#8B1A1A" }}>{error}</p>
      <button onClick={fetchAnalytics} className="mt-3 text-xs underline" style={{ color: "#8C8C8C" }}>
        Try again
      </button>
    </div>
  );

  if (!data) return null;

  return (
    <div className="space-y-10 fade-in">

      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest mb-2"
            style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
            Performance
          </p>
          <h2 className="font-display text-2xl font-medium" style={{ color: "#0D0D0D" }}>
            System Analytics
          </h2>
          <div className="mt-3 w-12 h-px" style={{ backgroundColor: "#0D0D0D" }} />
        </div>
        <button onClick={fetchAnalytics}
          className="flex items-center gap-2 text-xs uppercase tracking-widest transition-colors pb-1"
          style={{ color: "#8C8C8C", letterSpacing: "0.15em", fontSize: "0.65rem", borderBottom: "1px solid #DDD6C8" }}>
          <RefreshCw className="w-3 h-3" />
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Queries" value={data.total_queries}
          sub={`${data.answered} answered · ${data.refused} refused`} />
        <StatCard label="Avg Latency" value={`${data.avg_total_ms}ms`}
          sub={`Retrieval ${data.avg_retrieval_ms}ms · Generation ${data.avg_generation_ms}ms`} />
        <StatCard label="Refusal Rate" value={`${data.refusal_rate}%`}
          sub="Hallucination prevention active" />
        <StatCard label="Avg Relevance" value={`${(data.avg_cohere_score * 100).toFixed(1)}%`}
          sub="Cohere cross-encoder score" />
      </div>

      {/* Recent queries table */}
      <div style={{ borderTop: "2px solid #0D0D0D" }}>

        <div className="py-4" style={{ borderBottom: "1px solid #DDD6C8" }}>
          <p className="text-xs uppercase tracking-widest"
            style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
            Recent Query History
          </p>
        </div>

        {data.recent_queries.length === 0 ? (
          <p className="text-xs uppercase tracking-widest py-12 text-center"
            style={{ color: "#C4BAA8", letterSpacing: "0.15em", fontSize: "0.65rem" }}>
            No queries logged yet
          </p>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: "1px solid #EDE8DE" }}>
                {["Timestamp", "Query", "Latency", "Status"].map((h, i) => (
                  <th key={h}
                    className={`py-3 font-medium uppercase tracking-widest ${i > 1 ? "text-right" : "text-left"}`}
                    style={{ color: "#8C8C8C", letterSpacing: "0.15em", fontSize: "0.6rem",
                      paddingLeft: i === 0 ? 0 : "16px", paddingRight: i === 3 ? 0 : "16px" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.recent_queries.map((row, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #EDE8DE" }}>
                  <td className="py-4 font-mono" style={{ color: "#8C8C8C", fontSize: "0.65rem", paddingRight: "16px" }}>
                    {row.timestamp}
                  </td>
                  <td className="py-4 max-w-xs truncate" style={{ color: "#2C2C2C", paddingRight: "16px" }}>
                    {row.query}
                  </td>
                  <td className="py-4 text-right font-mono" style={{ color: "#0D0D0D", paddingRight: "16px" }}>
                    {row.latency_ms}ms
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-xs uppercase tracking-widest font-medium"
                      style={{
                        color: row.refused ? "#8B1A1A" : "#2D6A4F",
                        letterSpacing: "0.1em",
                        fontSize: "0.6rem"
                      }}>
                      {row.refused ? "Refused" : "Answered"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}