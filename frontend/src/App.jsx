import { useState } from "react";
import QueryPanel from "./components/QueryPanel";
import AnswerDisplay from "./components/AnswerDisplay";
import SourcesPanel from "./components/SourcesPanel";
import AnalyticsDashboard from "./components/AnalyticsDashboard";

export default function App() {
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("query");

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#FDFCF9" }}>

      {/* ── HEADER ── */}
      <header style={{ borderBottom: "1px solid #DDD6C8", backgroundColor: "#FDFCF9" }}
        className="sticky top-0 z-10">

        {/* Top strip — very thin, near-black */}
        <div style={{ backgroundColor: "#0D0D0D", height: "3px" }} />

        <div className="max-w-7xl mx-auto px-8 py-5 flex items-center justify-between">

          {/* Logo — editorial serif style */}
          <div>
            <h1 className="font-display text-xl font-semibold tracking-wide"
              style={{ color: "#0D0D0D", letterSpacing: "0.08em" }}>
              FINREG
            </h1>
            <p className="text-xs tracking-widest uppercase mt-0.5"
              style={{ color: "#8C8C8C", letterSpacing: "0.2em" }}>
              Regulatory Intelligence
            </p>
          </div>

          {/* Tab navigation — minimal text links */}
          <nav className="flex items-center gap-8">
            {["query", "analytics"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="text-xs uppercase tracking-widest font-medium transition-all duration-200 pb-1"
                style={{
                  color: activeTab === tab ? "#0D0D0D" : "#8C8C8C",
                  borderBottom: activeTab === tab ? "1px solid #0D0D0D" : "1px solid transparent",
                  letterSpacing: "0.18em",
                }}
              >
                {tab}
              </button>
            ))}
          </nav>

          {/* Status — minimal */}
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full breathe"
              style={{ backgroundColor: "#0D0D0D" }} />
            <span className="text-xs tracking-widest uppercase"
              style={{ color: "#8C8C8C", letterSpacing: "0.15em", fontSize: "0.65rem" }}>
              Basel III
            </span>
          </div>
        </div>
      </header>

      {/* ── MAIN ── */}
      <main className="max-w-7xl mx-auto px-8 py-12">

        {activeTab === "query" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">

            {/* Left: input + answer */}
            <div className="lg:col-span-2 space-y-8">

              {/* Section heading */}
              <div>
                <p className="text-xs uppercase tracking-widest mb-2"
                  style={{ color: "#8C8C8C", letterSpacing: "0.2em" }}>
                  Query Interface
                </p>
                <h2 className="font-display text-2xl font-medium"
                  style={{ color: "#0D0D0D" }}>
                  Ask a Regulatory Question
                </h2>
                <div className="mt-3 w-12 h-px" style={{ backgroundColor: "#0D0D0D" }} />
              </div>

              <QueryPanel onResult={setResult} />
              {result && <AnswerDisplay result={result} />}
            </div>

            {/* Right: sources */}
            <div className="space-y-6">
              <div>
                <p className="text-xs uppercase tracking-widest mb-2"
                  style={{ color: "#8C8C8C", letterSpacing: "0.2em" }}>
                  Source Documents
                </p>
                <div className="w-8 h-px" style={{ backgroundColor: "#DDD6C8" }} />
              </div>
              <SourcesPanel sources={result?.sources} />
            </div>
          </div>
        )}

        {activeTab === "analytics" && <AnalyticsDashboard />}
      </main>

      {/* ── FOOTER ── */}
      <footer className="mt-24" style={{ borderTop: "1px solid #DDD6C8" }}>
        <div className="max-w-7xl mx-auto px-8 py-6 flex items-center justify-between">
          <p className="text-xs uppercase tracking-widest"
            style={{ color: "#8C8C8C", letterSpacing: "0.15em", fontSize: "0.65rem" }}>
            FinReg-RAG · Hybrid Retrieval · Citation Enforced
          </p>
          <p className="text-xs" style={{ color: "#C4BAA8", fontSize: "0.65rem" }}>
            97.5% Evaluation Score · 100% Citation Compliance
          </p>
        </div>
      </footer>
    </div>
  );
}