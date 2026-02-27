function GaugeArc({ value, color, size = 80 }) {
    const radius = 34
    const circumference = Math.PI * radius  // half-circle
    const stroke = circumference * (1 - value / 100)
    const cx = size / 2
    const cy = size / 2

    return (
        <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`}>
            {/* Background arc */}
            <path
                d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
                fill="none"
                stroke="rgba(255,255,255,0.06)"
                strokeWidth="6"
                strokeLinecap="round"
            />
            {/* Value arc */}
            <path
                d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
                fill="none"
                stroke={color}
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={stroke}
                style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: 'stroke-dashoffset 0.8s ease' }}
            />
        </svg>
    )
}

function MetricGauge({ label, value, color, description }) {
    const safeValue = Math.round(Number(value) || 0)

    const textColor =
        color === '#10b981'
            ? 'text-emerald-400'
            : color === '#ef4444'
                ? 'text-red-400'
                : 'text-cyan-400'

    return (
        <div className="metric-card flex flex-col items-center gap-1 py-3">
            <div className="scan-line" />
            <GaugeArc value={safeValue} color={color} />
            <div className="text-center -mt-2">
                <div className={`text-2xl font-bold font-mono ${textColor}`} style={{ textShadow: `0 0 12px ${color}` }}>
                    {safeValue}%
                </div>
                <div className="text-white/60 text-xs font-mono uppercase tracking-widest mt-0.5">{label}</div>
                <div className="text-white/30 text-xs mt-1">{description}</div>
            </div>
        </div>
    )
}

export default function MetricsPanel({ data }) {
    const engagement = data?.engagement_score ?? 0
    const stress = data?.stress_score ?? 0
    const confidence = data?.confidence_score ?? 0

    return (
        <div className="grid grid-cols-3 gap-3">
            <MetricGauge
                label="Engagement"
                value={engagement}
                color="#10b981"
                description={engagement > 70 ? 'In the zone' : engagement > 40 ? 'Moderate' : 'Low'}
            />
            <MetricGauge
                label="Stress"
                value={stress}
                color="#ef4444"
                description={stress > 70 ? 'Critical' : stress > 40 ? 'Elevated' : 'Calm'}
            />
            <MetricGauge
                label="Confidence"
                value={confidence}
                color="#00f5ff"
                description={confidence > 70 ? 'Strong' : confidence > 40 ? 'Stable' : 'Low'}
            />
        </div>
    )
}
