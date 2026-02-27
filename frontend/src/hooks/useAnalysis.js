import { useRef, useEffect, useCallback } from 'react'

/**
 * useAnalysis hook
 * Manages webcam capture + periodic frame sending to the backend.
 */
export function useAnalysis({ onResult, onError, intervalMs = 1000 }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const streamRef = useRef(null)
    const intervalRef = useRef(null)
    const isRunningRef = useRef(false)
    const audioContextRef = useRef(null)
    const analyserRef = useRef(null)
    const audioStreamRef = useRef(null)

    // Backend URL: try the Vite proxy first, fall back to direct localhost
    const BACKEND_URL = 'http://localhost:8000'

    // --- Audio Analysis Setup ---
    const initAudio = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
            audioStreamRef.current = stream
            const ctx = new AudioContext()
            audioContextRef.current = ctx
            const analyser = ctx.createAnalyser()
            analyser.fftSize = 2048
            analyserRef.current = analyser
            const source = ctx.createMediaStreamSource(stream)
            source.connect(analyser)
        } catch {
            // Audio is optional – continue without it
        }
    }, [])

    const getAudioFeatures = useCallback(() => {
        const analyser = analyserRef.current
        if (!analyser) return null

        const bufferLength = analyser.fftSize
        const dataArray = new Float32Array(bufferLength)
        analyser.getFloatTimeDomainData(dataArray)

        let sumSq = 0
        for (let i = 0; i < bufferLength; i++) sumSq += dataArray[i] * dataArray[i]
        const rms = Math.sqrt(sumSq / bufferLength)

        let zeroCrossings = 0
        for (let i = 1; i < bufferLength; i++) {
            if ((dataArray[i] >= 0) !== (dataArray[i - 1] >= 0)) zeroCrossings++
        }
        const zcr = zeroCrossings / bufferLength

        let speech_speed = 'normal'
        let pauses = 'minimal'
        let tone_indicator = 'neutral'

        if (rms < 0.01) {
            speech_speed = 'silent'
            pauses = 'frequent'
        } else if (zcr > 0.15) {
            speech_speed = 'fast'
            pauses = 'none'
        } else if (zcr < 0.05) {
            speech_speed = 'slow'
            pauses = 'minimal'
        }

        if (rms > 0.1) tone_indicator = 'excited'
        else if (rms > 0.05 && zcr > 0.12) tone_indicator = 'stressed'
        else if (rms < 0.02) tone_indicator = 'calm'

        return { speech_speed, pauses, tone_indicator }
    }, [])

    // --- Frame Capture + API Call ---
    const captureAndSend = useCallback(async () => {
        if (!isRunningRef.current) return

        const video = videoRef.current
        const canvas = canvasRef.current

        // Wait for video to be ready
        if (!video || !canvas) {
            console.warn('[CogniSync] video or canvas ref not attached yet')
            return
        }
        if (video.readyState < 2) {
            console.warn('[CogniSync] video not ready yet, readyState:', video.readyState)
            return
        }

        const ctx = canvas.getContext('2d')
        const w = video.videoWidth || 640
        const h = video.videoHeight || 480
        canvas.width = w
        canvas.height = h
        ctx.drawImage(video, 0, 0, w, h)

        const dataUrl = canvas.toDataURL('image/jpeg', 0.7)
        const base64 = dataUrl.split(',')[1]
        if (!base64) {
            console.warn('[CogniSync] empty base64 from canvas')
            return
        }

        const audioFeatures = getAudioFeatures()

        try {
            const response = await fetch(`${BACKEND_URL}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    frame_base64: base64,
                    audio_features: audioFeatures,
                }),
                signal: AbortSignal.timeout(8000),
            })
            if (!response.ok) throw new Error(`HTTP ${response.status}`)
            const data = await response.json()
            onResult(data)
        } catch (err) {
            if (err.name !== 'AbortError' && err.name !== 'TimeoutError') {
                onError(err.message || 'Analysis request failed')
            }
        }
    }, [getAudioFeatures, onResult, onError, BACKEND_URL])

    // Wait for video to be ready (polls readyState)
    const waitForVideoReady = (video, timeout = 10000) =>
        new Promise((resolve, reject) => {
            if (video.readyState >= 2) return resolve()
            const start = Date.now()
            const check = () => {
                if (video.readyState >= 2) return resolve()
                if (Date.now() - start > timeout) return reject(new Error('Video timed out'))
                setTimeout(check, 100)
            }
            check()
        })

    // --- Start ---
    const start = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
            })
            streamRef.current = stream

            if (videoRef.current) {
                videoRef.current.srcObject = stream
                videoRef.current.play().catch(() => { })
                // Wait until video frames are actually flowing
                await waitForVideoReady(videoRef.current)
            }

            await initAudio()
            isRunningRef.current = true

            // Fire first analysis immediately, then on interval
            captureAndSend()
            intervalRef.current = setInterval(captureAndSend, intervalMs)
        } catch (err) {
            onError(err.message || 'Camera access denied')
        }
    }, [captureAndSend, initAudio, intervalMs, onError])

    // --- Stop ---
    const stop = useCallback(() => {
        isRunningRef.current = false
        clearInterval(intervalRef.current)
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop())
            streamRef.current = null
        }
        if (audioStreamRef.current) {
            audioStreamRef.current.getTracks().forEach((t) => t.stop())
            audioStreamRef.current = null
        }
        if (audioContextRef.current) {
            audioContextRef.current.close()
            audioContextRef.current = null
        }
        if (videoRef.current) videoRef.current.srcObject = null
    }, [])

    useEffect(() => () => stop(), [stop])

    return { videoRef, canvasRef, start, stop }
}
