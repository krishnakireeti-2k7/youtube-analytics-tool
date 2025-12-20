"use client";

import { useState } from "react";

export default function Home() {
  const [channel, setChannel] = useState("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    if (!channel) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const res = await fetch(
        `http://localhost:8000/analytics?channel=${encodeURIComponent(
          channel
        )}&scope=90d`
      );

      if (!res.ok) {
        throw new Error("Failed to fetch analytics");
      }

      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">
        YouTube Analytics Tool
      </h1>

      <div className="flex gap-2 mb-6">
        <input
          className="border px-3 py-2 w-full rounded"
          placeholder="Enter channel name (e.g. mrbeast)"
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
        />
        <button
          onClick={fetchAnalytics}
          className="bg-black text-white px-4 py-2 rounded"
          disabled={loading}
        >
          {loading ? "Loading..." : "Analyze"}
        </button>
      </div>

      {error && (
        <p className="text-red-500 mb-4">{error}</p>
      )}

      {data && (
        <pre className="bg-gray-100 p-4 rounded overflow-x-auto text-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </main>
  );
}
