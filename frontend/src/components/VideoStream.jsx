import { forwardRef } from 'react'
import { Activity } from 'lucide-react'

const VideoStream = forwardRef(function VideoStream({ isActive, canvasRef }, videoRef) {
    return (
        <div className="relative w-full aspect-video bg-cyber-800 rounded-xl overflow-hidden border border-white/10 shadow-2xl">
            {/* Hidden canvas for frame capture */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Live video element */}
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className={`w-full h-full object-cover transition-opacity duration-500 ${isActive ? 'opacity-100' : 'opacity-0'
                    }`}
            />

            {/* Idle overlay */}
            {!isActive && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                    <div className="w-20 h-20 rounded-full border-2 border-dashed border-white/20 flex items-center justify-center">
                        <svg className="w-8 h-8 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                        </svg>
                    </div>
                    <p className="text-white/40 text-sm font-mono">Camera inactive</p>
                    <p className="text-white/25 text-xs">Press Start Analysis to begin</p>
                </div>
            )}

            {/* Active scanning overlay */}
            {isActive && (
                <>
                    {/* Corner brackets */}
                    <div className="absolute top-3 left-3 w-8 h-8 border-t-2 border-l-2 border-cyan-400 opacity-70" />
                    <div className="absolute top-3 right-3 w-8 h-8 border-t-2 border-r-2 border-cyan-400 opacity-70" />
                    <div className="absolute bottom-3 left-3 w-8 h-8 border-b-2 border-l-2 border-cyan-400 opacity-70" />
                    <div className="absolute bottom-3 right-3 w-8 h-8 border-b-2 border-r-2 border-cyan-400 opacity-70" />

                    {/* Scan line */}
                    <div className="scan-line" />

                    {/* Bottom gradient */}
                    <div className="video-overlay absolute inset-0 pointer-events-none" />

                    {/* LIVE badge */}
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-1 rounded-full border border-red-500/40">
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        <span className="text-red-400 text-xs font-mono font-bold tracking-widest">LIVE</span>
                    </div>

                    {/* Processing indicator */}
                    <div className="absolute bottom-4 left-4 flex items-center gap-2">
                        <Activity className="w-3 h-3 text-cyan-400 animate-pulse" />
                        <span className="text-cyan-400 text-xs font-mono">ANALYZING</span>
                    </div>
                </>
            )}
        </div>
    )
})

export default VideoStream
