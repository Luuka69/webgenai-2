import { useState } from 'react';

function App() {
  const [description, setDescription] = useState('');
  const [result, setResult] = useState('');

  const generate = async () => {
    const res = await fetch('http://localhost:8000/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    const data = await res.json();
    setResult(data.html);
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>🧠 AI Web Screen Generator</h1>
      <textarea
        style={{ width: '100%', height: 100 }}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe your screen..."
      />
      <button onClick={generate}>Generate</button>
      <div
        style={{
          marginTop: 20,
          padding: 20,
          border: '1px solid #ccc',
          borderRadius: 8,
        }}
      >
        <iframe
          title="Generated Output"
          srcDoc={result}
          style={{ width: '100%', height: 400 }}
        />
      </div>
    </div>
  );
}

export default App;
