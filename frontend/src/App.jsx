import { useState, useCallback } from 'react'
import { Play, Square, Brain, Cpu, Wifi, WifiOff } from 'lucide-react'
import { useAnalysis } from './hooks/useAnalysis'
import VideoStream from './components/VideoStream'
import MetricsPanel from './components/MetricsPanel'
import SignalPanel from './components/SignalPanel'
import AdvicePanel from './components/AdvicePanel'
import AlertSystem from './components/AlertSystem'
import EngagementChart from './components/EngagementChart'

const MAX_HISTORY = 30

export default function App() {
    const [isActive, setIsActive] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [latestData, setLatestData] = useState(null)
    const [history, setHistory] = useState([])
    const [error, setError] = useState(null)
    const [frameCount, setFrameCount] = useState(0)
    const [backendOnline, setBackendOnline] = useState(null)


    const handleResult = useCallback((data) => {
        setIsLoading(false)
        setError(null)
        setLatestData(data)
        setFrameCount((c) => c + 1)
        setHistory((prev) => {
            const next = [...prev, data]
            return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next
        })
    }, [])

    const handleError = useCallback((msg) => {
        setIsLoading(false)
        setError(msg)
    }, [])

    const { videoRef, canvasRef, start, stop } = useAnalysis({
        onResult: handleResult,
        onError: handleError,
        intervalMs: 1000,
    })

    const checkBackend = async () => {
        try {
            const res = await fetch('/health', { signal: AbortSignal.timeout(3000) })
            setBackendOnline(res.ok)
        } catch {
            setBackendOnline(false)
        }
    }

    const handleStart = async () => {
        setError(null)
        setHistory([])
        setLatestData(null)
        setFrameCount(0)
        await checkBackend()
        setIsActive(true)
        setIsLoading(true)
        await start()
    }

    const handleStop = () => {
        stop()
        setIsActive(false)
        setIsLoading(false)
    }

    return (
        <div className="min-h-screen bg-cyber-900 font-display">
            {/* Ambient background blobs */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full opacity-10 blur-3xl"
                    style={{ background: 'radial-gradient(circle, #00f5ff, transparent)' }} />
                <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full opacity-10 blur-3xl"
                    style={{ background: 'radial-gradient(circle, #7c3aed, transparent)' }} />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-5 blur-3xl"
                    style={{ background: 'radial-gradient(circle, #10b981, transparent)' }} />
            </div>

            {/* ── Header ── */}
            <header className="relative z-10 border-b border-white/5 px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400/20 to-purple-600/20 border border-cyan-400/30 flex items-center justify-center">
                            <Brain className="w-5 h-5 text-cyan-400" />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-white tracking-tight">
                                Cogni<span className="text-cyan-400 glow-text">Sync</span>
                            </h1>
                            <p className="text-white/30 text-xs font-mono">Real-Time Social Intelligence</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Backend status */}
                        <div className="flex items-center gap-1.5">
                            {backendOnline === null ? (
                                <Cpu className="w-3.5 h-3.5 text-white/30" />
                            ) : backendOnline ? (
                                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                                <WifiOff className="w-3.5 h-3.5 text-red-400" />
                            )}
                            <span className="text-xs font-mono text-white/40">
                                {backendOnline === null ? 'API' : backendOnline ? 'Connected' : 'Offline'}
                            </span>
                        </div>

                        {/* Frame counter */}
                        {isActive && (
                            <div className="flex items-center gap-1.5 bg-white/5 px-3 py-1 rounded-full border border-white/10">
                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                                <span className="text-xs font-mono text-cyan-400">{frameCount} frames</span>
                            </div>
                        )}

                        {/* Start / Stop button */}
                        {!isActive ? (
                            <button onClick={handleStart} className="btn-primary">
                                <Play className="w-4 h-4" />
                                Start Analysis
                            </button>
                        ) : (
                            <button onClick={handleStop} className="btn-danger">
                                <Square className="w-4 h-4" />
                                Stop
                            </button>
                        )}
                    </div>
                </div>
            </header>

            {/* ── Main Layout ── */}
            <main className="relative z-10 max-w-7xl mx-auto px-6 py-6 grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-6">

                {/* ── LEFT COLUMN ── */}
                <div className="flex flex-col gap-5">
                    {/* Video + Alert strip */}
                    <div>
                        <VideoStream ref={videoRef} isActive={isActive} canvasRef={canvasRef} />
                        {latestData?.alerts?.length > 0 && (
                            <div className="mt-3">
                                <AlertSystem alerts={latestData.alerts} />
                            </div>
                        )}
                    </div>

                    {/* Metrics gauges */}
                    <MetricsPanel data={latestData} />

                    {/* Engagement chart */}
                    <EngagementChart history={history} />

                    {/* Error banner */}
                    {error && (
                        <div className="glass-panel border-red-500/30 bg-red-500/5 p-4 text-red-300 text-sm font-mono flex items-center gap-2">
                            <span className="text-red-500">✗</span>
                            {error}
                        </div>
                    )}
                </div>

                {/* ── RIGHT COLUMN ── */}
                <div className="flex flex-col gap-5">
                    {/* Agent Advice */}
                    <AdvicePanel advice={latestData?.advice} isLoading={isLoading} />

                    {/* Signal Stream */}
                    <SignalPanel data={latestData} />

                    {/* Session Stats */}
                    <div className="glass-panel p-5">
                        <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-3">Session Stats</div>
                        <div className="grid grid-cols-2 gap-3">
                            {[
                                { label: 'Frames', value: frameCount },
                                {
                                    label: 'Avg Engage',
                                    value: history.length
                                        ? `${Math.round(history.reduce((s, d) => s + d.engagement_score, 0) / history.length)}%`
                                        : '—',
                                },
                                {
                                    label: 'Avg Stress',
                                    value: history.length
                                        ? `${Math.round(history.reduce((s, d) => s + d.stress_score, 0) / history.length)}%`
                                        : '—',
                                },
                                {
                                    label: 'Last Ping',
                                    value: latestData ? `${latestData.processing_time_ms?.toFixed(0)}ms` : '—',
                                },
                            ].map(({ label, value }) => (
                                <div key={label} className="bg-white/5 rounded-lg p-3 text-center">
                                    <div className="text-white font-mono font-bold text-base">{value}</div>
                                    <div className="text-white/40 text-xs mt-0.5">{label}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* How it works */}
                    <div className="glass-panel p-5">
                        <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-3">Pipeline</div>
                        {[
                            { step: '01', label: 'Capture', detail: 'Frame every 1s via WebRTC' },
                            { step: '02', label: 'Vision', detail: 'MediaPipe: face + pose' },
                            { step: '03', label: 'Audio', detail: 'RMS + ZCR speech analysis' },
                            { step: '04', label: 'Fusion', detail: 'Unified behavioral state' },
                            { step: '05', label: 'Agent', detail: 'LLM strategic reasoning' },
                        ].map(({ step, label, detail }) => (
                            <div key={step} className="flex items-start gap-3 py-2 border-b border-white/5 last:border-0">
                                <span className="text-cyan-400/50 font-mono text-xs w-6 shrink-0 mt-0.5">{step}</span>
                                <div>
                                    <div className="text-white/70 text-xs font-semibold">{label}</div>
                                    <div className="text-white/30 text-xs">{detail}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    )
}
