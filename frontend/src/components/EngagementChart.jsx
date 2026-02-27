import {
    LineChart, Line, XAxis, YAxis, Tooltip,
    CartesianGrid, ResponsiveContainer, Legend
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="glass-panel p-2 text-xs font-mono border border-white/10">
                {payload.map((p) => (
                    <div key={p.name} className="flex gap-2 items-center">
                        <span style={{ color: p.color }}>{p.name}:</span>
                        <span className="text-white">{p.value}%</span>
                    </div>
                ))}
            </div>
        )
    }
    return null
}

export default function EngagementChart({ history }) {
    if (!history || history.length < 2) {
        return (
            <div className="glass-panel p-5">
                <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Timeline</span>
                </div>
                <div className="h-24 flex items-center justify-center">
                    <p className="text-white/25 text-xs font-mono">Building history... (need 2+ data points)</p>
                </div>
            </div>
        )
    }

    const data = history.map((item, idx) => ({
        t: `${idx + 1}`,
        Engagement: Math.round(item.engagement_score),
        Stress: Math.round(item.stress_score),
        Confidence: Math.round(item.confidence_score),
    }))

    return (
        <div className="glass-panel p-5">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Behavioral Timeline</span>
                <span className="text-white/20 text-xs font-mono ml-auto">Last {history.length} readings</span>
            </div>
            <ResponsiveContainer width="100%" height={140}>
                <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="t" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'monospace' }} />
                    <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'monospace' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                        wrapperStyle={{ fontSize: '10px', fontFamily: 'monospace', color: 'rgba(255,255,255,0.4)' }}
                    />
                    <Line
                        type="monotone" dataKey="Engagement"
                        stroke="#10b981" strokeWidth={2} dot={false}
                        style={{ filter: 'drop-shadow(0 0 4px #10b981)' }}
                    />
                    <Line
                        type="monotone" dataKey="Stress"
                        stroke="#ef4444" strokeWidth={2} dot={false}
                        style={{ filter: 'drop-shadow(0 0 4px #ef4444)' }}
                    />
                    <Line
                        type="monotone" dataKey="Confidence"
                        stroke="#00f5ff" strokeWidth={2} dot={false}
                        style={{ filter: 'drop-shadow(0 0 4px #00f5ff)' }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}
