import React, { useState } from "react";

function App() {
  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setOutput("Generating...");

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: prompt }),
      });

      if (!response.ok) throw new Error("Failed to fetch API");

      const data = await response.json();
      setOutput(data.result || "No result received.");
    } catch (error) {
      console.error(error);
      setOutput("Error: Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      <div className="w-1/3 bg-white p-8 border-r">
        <div className="flex items-center space-x-3 mb-8">
          <img src="/logo.svg" alt="WebGen Logo" className="h-12 w-12" />
          <h1 className="text-3xl font-bold text-gray-900">WebGen AI</h1>
        </div>

        <p className="text-gray-500 mb-4">
          Generate a full web screen just by describing it.
        </p>

        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your web page idea..."
          className="w-full h-40 p-3 bg-gray-900 text-white rounded-md resize-none focus:ring-2 focus:ring-blue-400"
        />

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 mt-4 rounded-md font-semibold flex items-center justify-center"
        >
          🚀 {loading ? "Generating..." : "Generate Screen"}
        </button>

        <p className="mt-6 text-center text-gray-400 text-sm">
          Powered by <span className="font-semibold">Ollama + Mistral</span>
        </p>
      </div>

      <div className="w-2/3 p-8 bg-gray-50">
        <div className="bg-white shadow-lg rounded-lg p-6 h-full overflow-auto">
          <pre className="text-sm text-gray-800 whitespace-pre-wrap">
            {output || "No output yet."}
          </pre>
        </div>
      </div>
    </div>
  );
}

export default App;
