export default function LatencyBar({ latency }) {
  if (!latency) return null;
  const total = latency.total_ms || 1;

  const stages = [
    { label: "Retrieval",  ms: latency.retrieval_ms,  flex: latency.retrieval_ms / total },
    { label: "Reranking",  ms: latency.reranking_ms,  flex: latency.reranking_ms / total },
    { label: "Generation", ms: latency.generation_ms, flex: latency.generation_ms / total },
  ];

  return (
    <div className="p-6" style={{ backgroundColor: "#F7F4EE", border: "1px solid #DDD6C8" }}>

      <div className="flex items-center justify-between mb-4">
        <p className="text-xs uppercase tracking-widest"
          style={{ color: "#8C8C8C", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
          Latency Breakdown
        </p>
        <p className="text-xs font-mono" style={{ color: "#0D0D0D" }}>
          {latency.total_ms}ms
        </p>
      </div>

      {/* Segmented bar — three shades of ink */}
      <div className="flex w-full h-1 mb-5 gap-px" style={{ backgroundColor: "#EDE8DE" }}>
        {stages.map((stage, i) => (
          <div
            key={stage.label}
            className="transition-all duration-700"
            style={{
              width: `${stage.flex * 100}%`,
              backgroundColor: i === 0 ? "#0D0D0D" : i === 1 ? "#4A4A4A" : "#8C8C8C",
            }}
          />
        ))}
      </div>

      {/* Stage labels */}
      <div className="flex justify-between">
        {stages.map((stage, i) => (
          <div key={stage.label} className="flex flex-col">
            <span className="text-xs font-mono" style={{ color: "#0D0D0D" }}>
              {stage.ms}ms
            </span>
            <span className="text-xs mt-0.5 uppercase tracking-widest"
              style={{ color: "#8C8C8C", fontSize: "0.6rem", letterSpacing: "0.15em" }}>
              {stage.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}