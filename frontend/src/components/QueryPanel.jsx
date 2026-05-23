import { useState } from "react";
import axios from "axios";

const EXAMPLE_QUESTIONS = [
  "What is the minimum CET1 capital ratio under Basel III?",
  "What is the capital conservation buffer requirement?",
  "What is the leverage ratio and why did Basel III introduce it?",
  "What is the countercyclical capital buffer?",
  "What reforms did Basel III introduce for counterparty credit risk?",
];

export default function QueryPanel({ onResult }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!question.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post("/api/query", { question: question.trim() });
      onResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to reach the API. Ensure FastAPI is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSubmit();
  };

  return (
    <div className="space-y-6">

      {/* Text area — clean, cream background */}
      <div>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. What is the minimum CET1 capital ratio under Basel III?"
          rows={4}
          className="w-full text-sm resize-none transition-all duration-200 focus:outline-none"
          style={{
            backgroundColor: "#F7F4EE",
            border: "1px solid #DDD6C8",
            borderTop: "2px solid #0D0D0D",
            color: "#0D0D0D",
            padding: "16px",
            fontFamily: "Inter, sans-serif",
            lineHeight: "1.7",
          }}
          onFocus={e => {
            e.target.style.borderColor = "#0D0D0D";
            e.target.style.borderTopColor = "#0D0D0D";
          }}
          onBlur={e => {
            e.target.style.borderColor = "#DDD6C8";
            e.target.style.borderTopColor = "#0D0D0D";
          }}
        />
        <p className="text-xs mt-1.5 text-right"
          style={{ color: "#8C8C8C", letterSpacing: "0.05em" }}>
          Ctrl + Enter to submit
        </p>
      </div>

      {/* Submit button — full black, very premium */}
      <button
        onClick={handleSubmit}
        disabled={loading || !question.trim()}
        className="w-full py-4 text-xs uppercase tracking-widest font-medium transition-all duration-200"
        style={{
          backgroundColor: loading || !question.trim() ? "#EDE8DE" : "#0D0D0D",
          color: loading || !question.trim() ? "#8C8C8C" : "#FDFCF9",
          cursor: loading || !question.trim() ? "not-allowed" : "pointer",
          letterSpacing: "0.2em",
          border: "none",
        }}
      >
        {loading ? "Analysing Documents  ···" : "Search Regulatory Documents"}
      </button>

      {/* Error */}
      {error && (
        <div className="p-4" style={{ backgroundColor: "#FDF0F0", border: "1px solid #DDD6C8", borderTop: "2px solid #8B1A1A" }}>
          <p className="text-xs" style={{ color: "#8B1A1A" }}>{error}</p>
        </div>
      )}

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px" style={{ backgroundColor: "#DDD6C8" }} />
        <span className="text-xs uppercase tracking-widest" style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.6rem" }}>
          Example Queries
        </span>
        <div className="flex-1 h-px" style={{ backgroundColor: "#DDD6C8" }} />
      </div>

      {/* Example questions — editorial list style */}
      <div style={{ borderTop: "1px solid #DDD6C8" }}>
        {EXAMPLE_QUESTIONS.map((q, i) => (
          <button
            key={q}
            onClick={() => setQuestion(q)}
            className="w-full text-left py-3.5 text-xs transition-all duration-150 flex items-center justify-between group"
            style={{
              borderBottom: "1px solid #EDE8DE",
              color: "#4A4A4A",
              fontFamily: "Inter, sans-serif",
            }}
            onMouseEnter={e => e.currentTarget.style.color = "#0D0D0D"}
            onMouseLeave={e => e.currentTarget.style.color = "#4A4A4A"}
          >
            <span className="flex items-center gap-3">
              <span style={{ color: "#C4BAA8", fontFamily: "JetBrains Mono, monospace", fontSize: "0.6rem" }}>
                {String(i + 1).padStart(2, "0")}
              </span>
              {q}
            </span>
            <span style={{ color: "#C4BAA8", fontSize: "0.7rem" }}>→</span>
          </button>
        ))}
      </div>
    </div>
  );
}