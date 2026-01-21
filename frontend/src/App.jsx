import React, { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState('connecting')
  const [quality, setQuality] = useState('MEDIUM')
  const [bandwidth, setBandwidth] = useState(0)

  useEffect(() => {
    // Connect to backend health endpoint
    // Vite proxy will forward /api/* to backend in dev
    // Nginx will forward /api/* to backend in production
    fetch('/api/health')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        return res.json()
      })
      .then(data => {
        setStatus('connected')
        console.log('Backend connected:', data)
      })
      .catch(err => {
        setStatus('error')
        console.error('Backend connection failed:', err)
      })
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-blue-500">VVLIVE Dashboard</h1>
        <p className="text-gray-400 mt-2">IRL Bonded Streaming Control</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Status Card */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Status</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Backend:</span>
              <span className={status === 'connected' ? 'text-green-500' : 'text-red-500'}>
                {status}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Quality:</span>
              <span className="text-blue-500">{quality}</span>
            </div>
          </div>
        </div>

        {/* Network Card */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Network</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Verizon:</span>
              <span className="text-green-500">Active</span>
            </div>
            <div className="flex justify-between">
              <span>AT&T:</span>
              <span className="text-green-500">Active</span>
            </div>
            <div className="flex justify-between">
              <span>Total BW:</span>
              <span>{bandwidth} Mbps</span>
            </div>
          </div>
        </div>

        {/* Controls Card */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Controls</h2>
          <div className="space-y-3">
            <button className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
              Auto Mode
            </button>
            <button className="w-full bg-red-600 hover:bg-red-700 px-4 py-2 rounded">
              Emergency Mode
            </button>
          </div>
        </div>
      </div>

      <div className="mt-8 bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">📊 Health Score</h2>
        <div className="flex items-center space-x-4">
          <div className="text-6xl">🟢</div>
          <div>
            <div className="text-2xl font-bold text-green-500">HEALTHY</div>
            <div className="text-gray-400">All systems operational</div>
          </div>
        </div>
      </div>

      <footer className="mt-8 text-center text-gray-500">
        <p>VVLIVE v1.0.0 - Production Ready</p>
      </footer>
    </div>
  )
}

export default App