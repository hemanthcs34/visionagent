const EMOTION_CONFIG = {
    happy: { icon: '😊', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
    neutral: { icon: '😐', color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/30' },
    sad: { icon: '😔', color: 'text-indigo-400', bg: 'bg-indigo-400/10 border-indigo-400/30' },
    angry: { icon: '😠', color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
    fearful: { icon: '😨', color: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/30' },
    surprised: { icon: '😲', color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/30' },
    disgusted: { icon: '🤢', color: 'text-purple-400', bg: 'bg-purple-400/10 border-purple-400/30' },
}

const POSTURE_CONFIG = {
    upright: { label: 'Upright', icon: '⬆', color: 'text-emerald-400' },
    leaning_forward: { label: 'Leaning Fwd', icon: '↗', color: 'text-cyan-400' },
    neutral: { label: 'Neutral', icon: '↔', color: 'text-blue-400' },
    slouched: { label: 'Slouched', icon: '↘', color: 'text-orange-400' },
}

const ATTENTION_CONFIG = {
    high: { label: 'Focused', dot: 'bg-emerald-400', text: 'text-emerald-400' },
    medium: { label: 'Moderate', dot: 'bg-yellow-400', text: 'text-yellow-400' },
    low: { label: 'Distracted', dot: 'bg-red-400', text: 'text-red-400' },
}

function SignalRow({ label, value, children }) {
    return (
        <div className="flex items-center justify-between py-2 border-b border-white/5">
            <span className="text-white/50 text-xs font-mono uppercase tracking-wider">{label}</span>
            <div className="flex items-center gap-2">{children || <span className="text-white text-xs font-mono">{value}</span>}</div>
        </div>
    )
}

export default function SignalPanel({ data }) {
    if (!data) {
        return (
            <div className="glass-panel p-5 flex flex-col gap-3 animate-pulse">
                <p className="text-white/30 text-xs font-mono text-center py-4">Waiting for signal...</p>
            </div>
        )
    }

    const emotion = EMOTION_CONFIG[data.emotion] || EMOTION_CONFIG.neutral
    const posture = POSTURE_CONFIG[data.posture] || POSTURE_CONFIG.neutral
    const attention = ATTENTION_CONFIG[data.attention] || ATTENTION_CONFIG.medium

    return (
        <div className="glass-panel p-5 flex flex-col gap-1">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-mono text-white/40 uppercase tracking-widest">Signal Stream</h3>
                <span className="text-xs font-mono text-white/25">{data.processing_time_ms?.toFixed(0)}ms</span>
            </div>

            {/* Emotion */}
            <SignalRow label="Emotion">
                <span className={`text-sm px-2.5 py-0.5 rounded-full border font-mono ${emotion.bg} ${emotion.color}`}>
                    {emotion.icon} {data.emotion}
                </span>
            </SignalRow>

            {/* Posture */}
            <SignalRow label="Posture">
                <span className={`text-xs font-mono ${posture.color}`}>
                    {posture.icon} {posture.label}
                </span>
            </SignalRow>

            {/* Attention */}
            <SignalRow label="Attention">
                <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${attention.dot} animate-pulse`} />
                    <span className={`text-xs font-mono ${attention.text}`}>{attention.label}</span>
                </div>
            </SignalRow>

            {/* Movement */}
            <SignalRow label="Movement" value={data.movement} />

            {/* Audio */}
            {data.audio && (
                <>
                    <SignalRow label="Speech">
                        <span className="text-xs font-mono text-purple-300">{data.audio?.speech_speed || '—'}</span>
                    </SignalRow>
                    <SignalRow label="Pauses">
                        <span className="text-xs font-mono text-purple-300">{data.audio?.pauses || '—'}</span>
                    </SignalRow>
                    <SignalRow label="Tone">
                        <span className="text-xs font-mono text-purple-300">{data.audio?.tone_indicator || '—'}</span>
                    </SignalRow>
                </>
            )}
        </div>
    )
}
