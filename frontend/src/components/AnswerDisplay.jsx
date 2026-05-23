import LatencyBar from "./LatencyBar";
import RefusalMessage from "./RefusalMessage";

function parseCitations(text) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) return <span key={index} className="citation-marker">{match[1]}</span>;
    return <span key={index}>{part}</span>;
  });
}

export default function AnswerDisplay({ result }) {
  if (!result) return null;
  if (result.refused) return <div className="fade-in"><RefusalMessage query={result.query} /></div>;

  const paragraphs = result.answer.split("\n").filter((p) => p.trim().length > 0);
  const sourcesHeaderIndex = paragraphs.findIndex((p) => p.toLowerCase().startsWith("sources used"));
  const mainParagraphs = sourcesHeaderIndex > -1 ? paragraphs.slice(0, sourcesHeaderIndex) : paragraphs;
  const sourcesLines = sourcesHeaderIndex > -1 ? paragraphs.slice(sourcesHeaderIndex) : [];

  return (
    <div className="fade-in space-y-6">

      {/* Answer card */}
      <div className="card-accent p-8"
        style={{ backgroundColor: "#F7F4EE", border: "1px solid #DDD6C8" }}>

        {/* Label */}
        <p className="text-xs uppercase tracking-widest mb-6"
          style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
          Response
        </p>

        {/* Answer text */}
        <div className="space-y-4">
          {mainParagraphs.map((paragraph, i) => (
            <p key={i} className="text-sm leading-relaxed" style={{ color: "#1A1A1A", lineHeight: "1.85" }}>
              {parseCitations(paragraph)}
            </p>
          ))}
        </div>

        {/* Sources used */}
        {sourcesLines.length > 0 && (
          <div className="mt-6 pt-6" style={{ borderTop: "1px solid #DDD6C8" }}>
            {sourcesLines.map((line, i) => (
              <p key={i} className="text-xs leading-relaxed font-mono"
                style={{ color: "#8C8C8C", lineHeight: "1.8" }}>
                {line}
              </p>
            ))}
          </div>
        )}
      </div>

      <LatencyBar latency={result.latency} />
    </div>
  );
}