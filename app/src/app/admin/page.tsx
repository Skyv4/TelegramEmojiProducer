"use client";

import { useState, useEffect, useCallback } from "react";
import { getAllConversionRequests, completeConversionRequest, type ConversionResult as ApiConversionResult, getDownloadUrl } from "@/lib/api";

export default function AdminPage() {
  const [requests, setRequests] = useState<ApiConversionResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState<string>("");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  const handleLogin = () => {
    if (password === "hamilton jacobi bellman") { // Basic hardcoded password for demonstration
      setIsAuthenticated(true);
    } else {
      alert("Incorrect password!");
    }
  };

  const fetchRequests = useCallback(async () => {
    try {
      const fetchedRequests = await getAllConversionRequests();
      setRequests(fetchedRequests);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchRequests();
    }
  }, [isAuthenticated, fetchRequests]);

  const handleCompleteRequest = async (requestId: string) => {
    try {
      await completeConversionRequest(requestId);
      alert("Request marked as completed!");
      fetchRequests(); // Refresh the list
    } catch (err: any) {
      console.error("Error marking request as complete:", err);
      alert(`Failed to mark request as complete: ${err.message}`);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center flex-col">
        <h1 className="text-2xl font-bold mb-4">Admin Login</h1>
        <input
          type="password"
          placeholder="Enter password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="p-2 border border-gray-300 rounded mb-4 text-black"
        />
        <button
          onClick={handleLogin}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center">Loading admin data...</div>;
  }

  if (error) {
    return <div className="flex min-h-screen items-center justify-center text-red-500">Error: {error}</div>;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold mb-8">Admin Dashboard</h1>
      <div className="w-full max-w-4xl">
        <h2 className="text-2xl font-semibold mb-4">Conversion Requests</h2>
        {requests.length === 0 ? (
          <p>No conversion requests yet.</p>
        ) : (
          <ul className="space-y-4">
            {requests.map((request: ApiConversionResult) => (
              <li key={request.id} className="p-4 border rounded shadow-sm bg-white dark:bg-gray-800">
                <p><strong>ID:</strong> {request.id}</p>
                <p><strong>Type:</strong> {request.original_filename ? "File" : "URL"}</p>
                <p><strong>Source:</strong> {request.original_filename || request.original_url}</p>
                <p><strong>Status:</strong> {request.status}</p>
                {request.download_url && (
                  <div className="mt-2">
                    <h3 className="font-semibold">Converted Sticker:</h3>
                    <video
                      src={getDownloadUrl(request.converted_filename!)}
                      width="100"
                      height="100"
                      autoPlay
                      loop
                      muted
                      controls
                      className="mx-auto mt-2"
                    >
                      Your browser does not support the video tag.
                    </video>
                  </div>
                )}
                {request.status !== "admin_completed" && (
                  <button
                    onClick={() => handleCompleteRequest(request.id)}
                    className="mt-4 px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                  >
                    Mark as Complete
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
