'use client';

import { useEffect, useState } from 'react';

export default function DebugPage() {
  const [apiUrl, setApiUrl] = useState('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'ok' | 'error'>('checking');
  const [errorDetails, setErrorDetails] = useState<string>('');
  const [responseData, setResponseData] = useState<any>(null);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_API_URL || 'NOT SET';
    setApiUrl(url);

    // Test direct fetch
    const testConnection = async () => {
      try {
        const response = await fetch(`${url}/health`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          setBackendStatus('ok');
          setResponseData(data);
        } else {
          setBackendStatus('error');
          setErrorDetails(`HTTP ${response.status}: ${response.statusText}`);
        }
      } catch (error: any) {
        setBackendStatus('error');
        setErrorDetails(error.message || String(error));
      }
    };

    if (url !== 'NOT SET') {
      testConnection();
    }
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">API Debug Page</h1>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Environment</h2>
        <div className="space-y-2">
          <div>
            <span className="font-medium">API URL:</span>{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">{apiUrl}</code>
          </div>
          <div>
            <span className="font-medium">Browser URL:</span>{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">{typeof window !== 'undefined' ? window.location.origin : 'SSR'}</code>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Backend Connection Test</h2>

        {backendStatus === 'checking' && (
          <div className="text-yellow-600">
            Checking connection to {apiUrl}/health...
          </div>
        )}

        {backendStatus === 'ok' && (
          <div className="space-y-4">
            <div className="text-green-600 font-semibold">
              ✓ Backend is responding correctly
            </div>
            <div>
              <h3 className="font-medium mb-2">Response Data:</h3>
              <pre className="bg-gray-100 p-4 rounded overflow-auto">
                {JSON.stringify(responseData, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {backendStatus === 'error' && (
          <div className="space-y-4">
            <div className="text-red-600 font-semibold">
              ✗ Backend connection failed
            </div>
            <div>
              <h3 className="font-medium mb-2">Error Details:</h3>
              <pre className="bg-red-50 text-red-800 p-4 rounded">
                {errorDetails}
              </pre>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
              <h3 className="font-semibold text-yellow-800 mb-2">Troubleshooting:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-900">
                <li>Make sure the backend is running on port 8000</li>
                <li>Check that NEXT_PUBLIC_API_URL is set in .env.local</li>
                <li>Restart the Next.js dev server after changing .env.local</li>
                <li>Try opening <a href={`${apiUrl}/health`} target="_blank" className="text-blue-600 underline">{apiUrl}/health</a> directly</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 p-4 rounded">
        <h3 className="font-semibold text-blue-900 mb-2">Manual Tests:</h3>
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-medium">Health:</span>{' '}
            <a href={`${apiUrl}/health`} target="_blank" className="text-blue-600 underline">
              {apiUrl}/health
            </a>
          </div>
          <div>
            <span className="font-medium">Recent Trades:</span>{' '}
            <a href={`${apiUrl}/api/trades/recent?limit=5`} target="_blank" className="text-blue-600 underline">
              {apiUrl}/api/trades/recent?limit=5
            </a>
          </div>
          <div>
            <span className="font-medium">API Docs:</span>{' '}
            <a href={`${apiUrl}/docs`} target="_blank" className="text-blue-600 underline">
              {apiUrl}/docs
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
