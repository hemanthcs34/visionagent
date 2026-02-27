import { AlertTriangle, XCircle } from 'lucide-react'

const ALERT_STYLES = {
    '⚠️': 'border-yellow-500/40 bg-yellow-500/10 text-yellow-300',
    '🔴': 'border-red-500/40 bg-red-500/10 text-red-300',
}

function getAlertStyle(alert) {
    if (alert.startsWith('🔴')) return ALERT_STYLES['🔴']
    if (alert.startsWith('⚠️')) return ALERT_STYLES['⚠️']
    return 'border-white/20 bg-white/5 text-white/70'
}

export default function AlertSystem({ alerts }) {
    if (!alerts || alerts.length === 0) return null

    return (
        <div className="flex flex-col gap-2 animate-fade-in-up">
            <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
                <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Live Alerts</span>
            </div>
            {alerts.map((alert, i) => (
                <div
                    key={`${alert}-${i}`}
                    className={`alert-badge ${getAlertStyle(alert)}`}
                >
                    <span className="text-sm">{alert}</span>
                </div>
            ))}
        </div>
    )
}
