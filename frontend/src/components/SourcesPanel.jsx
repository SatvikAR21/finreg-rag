export default function SourcesPanel({ sources }) {
  if (!sources || sources.length === 0) {
    return (
      <div className="p-8 text-center" style={{ border: "1px solid #DDD6C8", backgroundColor: "#F7F4EE" }}>
        <p className="text-xs uppercase tracking-widest"
          style={{ color: "#C4BAA8", letterSpacing: "0.15em", fontSize: "0.65rem" }}>
          No sources yet
        </p>
      </div>
    );
  }

  const getScoreLabel = (score) => {
    if (!score) return null;
    if (score >= 0.9) return { label: "High", color: "#2D6A4F" };
    if (score >= 0.7) return { label: "Mid",  color: "#8B5E1A" };
    return { label: "Low", color: "#8B1A1A" };
  };

  return (
    <div style={{ border: "1px solid #DDD6C8", borderTop: "2px solid #0D0D0D" }}>

      {/* Header */}
      <div className="px-5 py-4" style={{ borderBottom: "1px solid #DDD6C8", backgroundColor: "#F7F4EE" }}>
        <p className="text-xs uppercase tracking-widest"
          style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
          Cited Sources · {sources.length}
        </p>
      </div>

      {/* Source entries */}
      <div style={{ backgroundColor: "#FDFCF9" }}>
        {sources.map((source, i) => {
          const scoreInfo = getScoreLabel(source.cohere_score);
          return (
            <div key={source.citation_number} className="px-5 py-5"
              style={{ borderBottom: i < sources.length - 1 ? "1px solid #EDE8DE" : "none" }}>

              {/* Citation + doc */}
              <div className="flex items-start gap-3 mb-3">
                <span className="citation-marker flex-shrink-0 mt-0.5">
                  {source.citation_number}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate" style={{ color: "#0D0D0D" }}>
                    {source.source}
                  </p>
                  <p className="text-xs mt-0.5 font-mono"
                    style={{ color: "#8C8C8C", fontSize: "0.65rem" }}>
                    p. {source.page === "unknown" || source.page === "?" ? "—" : source.page}
                  </p>
                </div>
                {scoreInfo && (
                  <span className="text-xs font-mono flex-shrink-0"
                    style={{ color: scoreInfo.color, fontSize: "0.65rem" }}>
                    {scoreInfo.label} · {(source.cohere_score * 100).toFixed(0)}%
                  </span>
                )}
              </div>

              {/* Text preview */}
              <p className="text-xs leading-relaxed ml-7 line-clamp-3"
                style={{ color: "#6B6B6B", lineHeight: "1.7" }}>
                {source.text_preview}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}