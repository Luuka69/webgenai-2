import { useState } from "react";
import "./App.css";

function App() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [html, setHtml] = useState("");

  const API_URL = import.meta.env.VITE_API_URL || "http://51.75.240.22:8010";

  const generateScreen = async () => {
    if (!description.trim()) {
      setError("Please enter a description before generating.");
      return;
    }

    setLoading(true);
    setError("");
    setHtml("");

    try {
      const response = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.error) throw new Error(data.error);

      setHtml(data.code || data.html || "<p>No HTML returned.</p>");
    } catch (err) {
      console.error("Error generating screen:", err);
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <div className="sidebar">
        <div className="header">
          {/* Inline SVG logo */}
          <svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 64 64"
  width="60"
  height="60"
  className="logo"
>
  <defs>
    <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stopColor="#ff4b91" />
      <stop offset="100%" stopColor="#ff77d4" />
    </linearGradient>
  </defs>
  <path
    fill="url(#brainGradient)"
    d="M32 2C18 2 8 12 8 24c0 6 3 10 6 13-1 4 0 8 3 11 3 3 8 5 15 5s12-2 15-5c3-3 4-7 3-11 3-3 6-7 6-13 0-12-10-22-24-22zm-8 6c3-1 7 1 9 4s2 7 1 10l-3-1c1-3 0-6-2-8s-5-3-7-2c-2 1-3 3-3 5h-3c0-3 2-6 5-8zm16 0c3 2 5 5 5 8h-3c0-2-1-4-3-5s-5 0-7 2-3 5-2 8l-3 1c-1-3-1-7 1-10s6-5 9-4zm-17 27c-2-1-3-2-3-3s1-2 3-3c2 1 3 2 3 3s-1 2-3 3zm18 0c-2-1-3-2-3-3s1-2 3-3c2 1 3 2 3 3s-1 2-3 3zm-9 14c-4 0-7-1-9-3s-3-4-2-7l3 1c0 2 1 4 3 5s4 2 5 2 4-1 5-2 3-3 3-5l3-1c1 3 0 5-2 7s-5 3-9 3z"
  />
</svg>


          <h1>WebGen AI</h1>
        </div>

        <p className="subtitle">
          Generate a full web screen just by describing it.
        </p>

        <textarea
          className="description-input"
          placeholder="Example: A login page with a blue header, username & password fields, and a 'Login' button."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <button onClick={generateScreen} disabled={loading}>
          {loading ? "⏳ Generating..." : "🚀 Generate Screen"}
        </button>

        {error && <p className="error">❌ {error}</p>}

        <footer>
          <p>
            Powered by <strong>Ollama + Mistral</strong>
          </p>
        </footer>
      </div>

      <div className="output-container">
        {loading ? (
          <div className="loading">✨ Generating your page...</div>
        ) : (
          <iframe
            title="Generated Page"
            id="generated-frame"
            srcDoc={html || "<p>No output yet.</p>"}
            sandbox="allow-scripts allow-same-origin"
          ></iframe>
        )}
      </div>
    </div>
  );
}

export default App;
