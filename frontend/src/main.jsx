// =============================================================================
// What this file does:
// React application entry point. Mounts the root App component into the
// #root div in index.html. StrictMode enables extra development warnings.
// =============================================================================

import { StrictMode } from "react";           // enables extra React warnings in dev
import { createRoot } from "react-dom/client"; // modern React 18 rendering API
import "./index.css";                          // global styles + Tailwind
import App from "./App";                       // root component

createRoot(document.getElementById("root")).render(  // mount into <div id="root">
  <StrictMode>
    <App />
  </StrictMode>
);