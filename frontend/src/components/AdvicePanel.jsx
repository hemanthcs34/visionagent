import { Bot, Zap } from 'lucide-react'

export default function AdvicePanel({ advice, isLoading }) {
    return (
        <div className="glass-panel p-5 min-h-[110px] relative overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-cyan-400" />
                </div>
                <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Agent Advice</span>
                {isLoading && (
                    <div className="ml-auto flex items-center gap-1.5">
                        <Zap className="w-3 h-3 text-yellow-400 animate-pulse" />
                        <span className="text-yellow-400 text-xs font-mono">Processing...</span>
                    </div>
                )}
            </div>

            {/* Advice text */}
            {advice ? (
                <div className="advice-card">
                    <p className="text-white/90 text-sm leading-relaxed font-medium">{advice}</p>
                </div>
            ) : (
                <div className="flex items-center gap-3 py-2">
                    <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                            <span
                                key={i}
                                className="w-1.5 h-1.5 rounded-full bg-cyan-400/40"
                                style={{ animation: `pulse 1.5s ease-in-out ${i * 0.2}s infinite` }}
                            />
                        ))}
                    </div>
                    <span className="text-white/30 text-xs font-mono">
                        {isLoading ? 'Generating advice...' : 'Waiting for analysis data...'}
                    </span>
                </div>
            )}
        </div>
    )
}
