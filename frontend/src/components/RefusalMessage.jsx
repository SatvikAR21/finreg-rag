export default function RefusalMessage({ query }) {
  return (
    <div className="p-8 fade-in"
      style={{ backgroundColor: "#F7F4EE", border: "1px solid #DDD6C8", borderTop: "2px solid #8B1A1A" }}>

      <p className="text-xs uppercase tracking-widest mb-4"
        style={{ color: "#8B1A1A", letterSpacing: "0.2em", fontSize: "0.65rem" }}>
        Insufficient Source Material
      </p>

      <p className="font-display text-lg font-medium mb-4" style={{ color: "#0D0D0D" }}>
        Unable to Generate a Reliable Response
      </p>

      <p className="text-sm leading-relaxed mb-6" style={{ color: "#4A4A4A", lineHeight: "1.8" }}>
        The retrieved regulatory documents do not contain sufficient information
        to answer this question with confidence. To prevent hallucination, the
        system has declined to generate a response.
      </p>

      <div className="p-4" style={{ backgroundColor: "#EDE8DE", borderLeft: "2px solid #0D0D0D" }}>
        <p className="text-xs uppercase tracking-widest mb-1"
          style={{ color: "#8C8C8C", letterSpacing: "0.15em", fontSize: "0.6rem" }}>
          Query
        </p>
        <p className="text-sm italic" style={{ color: "#2C2C2C" }}>"{query}"</p>
      </div>
    </div>
  );
}