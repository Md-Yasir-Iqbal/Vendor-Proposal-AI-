import React from "react";
import { createRoot } from "react-dom/client";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import "./shell.css";

const pageMeta = {
  "Home": ["Workspace overview", "Your current procurement decision brief."],
  "Create Analysis": ["New analysis", "Configure the rules used to evaluate every proposal."],
  "Upload Proposals": ["Proposal intake", "Securely process source documents and prepare them for analysis."],
  "Analysis Dashboard": ["Analysis dashboard", "Scores, signals, and ranking from the Python evaluation engine."],
  "Vendor Comparison": ["Vendor comparison", "Evaluate every requirement side by side."],
  "Vendor Details": ["Vendor profile", "Commercial, delivery, technical, and risk detail."],
  "Risk Analysis": ["Risk register", "Exceptions and review items requiring attention."],
  "Evidence": ["Evidence library", "Source-grounded excerpts behind the analysis."],
  "Recommendation": ["Decision brief", "The evidence-backed recommendation for this analysis."],
  "Analysis History": ["Analysis history", "Your saved procurement decision workspaces."],
  "Account": ["Account", "Your secure Vendorlens workspace."],
};

function App({ args }) {
  const page = args.page || "Home";
  const [eyebrow, title] = pageMeta[page] || pageMeta.Home;
  const metrics = args.metrics || [];
  React.useEffect(() => Streamlit.setFrameHeight(218), [page, metrics.length]);
  const navigate = (next) => Streamlit.setComponentValue({ action: "navigate", page: next });

  return <main className="shell">
    <header className="topbar">
      <button className="identity" onClick={() => navigate("Home")} aria-label="Go to home">
        <span className="mark">VL</span><span><strong>Vendorlens</strong><small>PROCUREMENT INTELLIGENCE</small></span>
      </button>
      <div className="topbar-right"><span className="secure"><i /> Secure workspace</span><span className="avatar">{(args.user || "U")[0].toUpperCase()}</span></div>
    </header>
    <section className="context">
      <div><p>{eyebrow}</p><h1>{title}</h1></div>
      <nav aria-label="Primary navigation">
        {["Home", "Create Analysis", "Upload Proposals", "Analysis Dashboard", "Vendor Comparison", "Recommendation"].map(item =>
          <button key={item} onClick={() => navigate(item)} className={item === page ? "active" : ""}>{item}</button>
        )}
      </nav>
    </section>
    {metrics.length > 0 && <section className="metrics">{metrics.map((metric) => <div className="metric" key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.sub || ""}</small></div>)}</section>}
  </main>;
}

createRoot(document.getElementById("root")).render(withStreamlitConnection(App));
