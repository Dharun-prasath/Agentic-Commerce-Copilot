import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Grid3x3, Volume2, Plus, Video, User } from 'lucide-react'
import './index.css'

type CallState = 'IDLE' | 'INCOMING' | 'RINGING' | 'ACCEPTED' | 'CONNECTING' | 'CONNECTED' | 'ENDED' | 'DECLINED'

declare global {
  interface Window {
    electronAPI?: {
      onIncomingCall: (callback: (sessionId?: string) => void) => void;
      hideWindow: () => void;
    }
  }
}

function App() {
  const [callState, setCallState] = useState<CallState>('IDLE')
  const [sessionId, setSessionId] = useState<string>('')
  const [callDuration, setCallDuration] = useState(0)
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeaker, setIsSpeaker] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const captureContextRef = useRef<AudioContext | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onIncomingCall((id) => {
        setCallState(prevState => {
          if (prevState !== 'IDLE' && prevState !== 'ENDED' && prevState !== 'DECLINED') {
            console.log("Call already in progress, ignoring incoming trigger.");
            return prevState;
          }
          if (id && id !== "undefined") {
            setSessionId(id);
          } else {
            setSessionId(""); // clear if undefined to prevent weird state
          }
          return 'INCOMING';
        });
      })
    }
  }, [])

  useEffect(() => {
    let timer: number;
    if (callState === 'CONNECTED') {
      timer = window.setInterval(() => {
        setCallDuration(prev => prev + 1)
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [callState])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0')
    const s = (seconds % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  const handleAccept = async () => {
    setCallState('CONNECTING')
    try {
      // Create audio contexts immediately during user gesture
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 })
      audioContextRef.current = audioCtx
      if (audioCtx.state === 'suspended') await audioCtx.resume()

      const captureCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 })
      captureContextRef.current = captureCtx
      if (captureCtx.state === 'suspended') await captureCtx.resume()

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      streamRef.current = stream

      const wsUrl = sessionId ? `ws://localhost:8000/api/v1/voice/stream?session_id=${sessionId}` : 'ws://localhost:8000/api/v1/voice/stream'
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = async () => {
        setCallState('CONNECTED')

        const source = captureCtx.createMediaStreamSource(stream)
        const processor = captureCtx.createScriptProcessor(512, 1, 1)
        processorRef.current = processor

        let silenceFrames = 0;
        
        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0)
          const pcm16 = new Int16Array(inputData.length)
          let hasAudio = false
          
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]))
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
            if (Math.abs(pcm16[i]) > 300) {
              hasAudio = true
            }
          }
          
          if (hasAudio) {
            silenceFrames = 0;
          } else {
            silenceFrames++;
          }
          
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(pcm16.buffer)
          }
        }

        source.connect(processor)

        const gainNode = captureCtx.createGain()
        gainNode.gain.value = 0
        processor.connect(gainNode)
        gainNode.connect(captureCtx.destination)

        let nextPlayTime = audioCtx.currentTime

        ws.onmessage = async (event) => {
          if (event.data instanceof Blob) {
            const arrayBuffer = await event.data.arrayBuffer()

            // Decode raw PCM 24kHz 16-bit little-endian
            const pcm16 = new Int16Array(arrayBuffer)
            const float32 = new Float32Array(pcm16.length)
            for (let i = 0; i < pcm16.length; i++) {
              float32[i] = pcm16[i] / 32768.0
            }

            const audioBuffer = audioCtx.createBuffer(1, float32.length, 24000)
            audioBuffer.getChannelData(0).set(float32)

            const bufferSource = audioCtx.createBufferSource()
            bufferSource.buffer = audioBuffer
            bufferSource.connect(audioCtx.destination)

            const startTime = Math.max(nextPlayTime, audioCtx.currentTime)
            bufferSource.start(startTime)
            nextPlayTime = startTime + audioBuffer.duration
          }
        }
      }

      ws.onclose = (e) => {
        console.log("WebSocket Closed!", e.code, e.reason)
        handleEnd()
      }
      
      ws.onerror = (e) => {
        console.error("WebSocket Error!", e)
      }

    } catch (err: any) {
      console.error("Failed to establish call", err)
      alert("Failed to establish call: " + err.message)
      setCallState('ENDED')
    }
  }

  const handleDecline = () => {
    setCallState('DECLINED')
    setTimeout(() => {
      setCallState('IDLE')
      if (window.electronAPI?.hideWindow) window.electronAPI.hideWindow()
    }, 2000)
  }

  const handleEnd = () => {
    if (wsRef.current) wsRef.current.close()
    if (processorRef.current) processorRef.current.disconnect()
    if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop())
    if (audioContextRef.current) audioContextRef.current.close()
    if (captureContextRef.current) captureContextRef.current.close()

    setCallState('ENDED')
    setCallDuration(0)
    setTimeout(() => {
      setCallState('IDLE')
      if (window.electronAPI?.hideWindow) window.electronAPI.hideWindow()
    }, 2000)
  }

  if (callState === 'IDLE') {
    return null;
  }

  const IconButton = ({ icon: Icon, label, isActive = false, onClick = () => { } }: any) => (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={onClick}
        className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${isActive
            ? 'bg-white text-black'
            : 'bg-[#2C2C2C] text-white hover:bg-[#3C3C3C]'
          }`}
      >
        <Icon size={28} strokeWidth={1.5} />
      </button>
      <span className="text-[13px] text-[#A0A0A0]">{label}</span>
    </div>
  )

  return (
    <div
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
      className="w-screen h-screen flex flex-col bg-[#1A1A1A]/95 backdrop-blur-3xl overflow-hidden font-sans text-white border border-white/10 rounded-[44px]"
    >

      {callState === 'INCOMING' && (
        <audio src="/ringtone.mp3" autoPlay loop className="hidden" />
      )}

      {/* Status Bar Spacer for iPhone */}
      <div className="h-14 w-full"></div>

      {/* Caller Info */}
      <div className="flex flex-col items-center flex-1 pt-8">
        <h1 className="text-3xl font-normal tracking-wide text-white/90">Agentic Commerce</h1>

        {callState === 'INCOMING' && (
          <p className="mt-2 text-white/60 text-lg">Sales Consultant</p>
        )}
        {callState === 'CONNECTING' && (
          <p className="mt-2 text-white/60 text-lg">Connecting...</p>
        )}
        {callState === 'CONNECTED' && (
          <p className="mt-2 text-white/60 text-lg tabular-nums">{formatTime(callDuration)}</p>
        )}
        {callState === 'ENDED' && (
          <p className="mt-2 text-white/60 text-lg">Call Ended</p>
        )}
        {callState === 'DECLINED' && (
          <p className="mt-2 text-white/60 text-lg">Call Declined</p>
        )}
      </div>

      {/* Controls */}
      <div
        style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
        className="w-full pb-16 px-8"
      >

        {/* Active Call Controls Grid */}
        {(callState === 'CONNECTED' || callState === 'CONNECTING') && (
          <div className="grid grid-cols-3 gap-y-6 gap-x-4 mb-16 px-4">
            <IconButton
              icon={isMuted ? MicOff : Mic}
              label="mute"
              isActive={isMuted}
              onClick={() => setIsMuted(!isMuted)}
            />
            <IconButton icon={Grid3x3} label="keypad" />
            <IconButton
              icon={Volume2}
              label="speaker"
              isActive={isSpeaker}
              onClick={() => setIsSpeaker(!isSpeaker)}
            />
            <IconButton icon={Plus} label="add call" />
            <IconButton icon={Video} label="FaceTime" />
            <IconButton icon={User} label="contacts" />
          </div>
        )}

        {/* Bottom Actions */}
        <div
          style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
          className="flex justify-between items-end px-4 h-24"
        >
          {callState === 'INCOMING' ? (
            <>
              <div className="flex flex-col items-center gap-2">
                <button
                  onClick={handleDecline}
                  className="w-[72px] h-[72px] bg-[#FF3B30] rounded-full flex items-center justify-center hover:bg-[#FF3B30]/80 transition-colors"
                >
                  <FilledPhone className="text-white fill-current transform rotate-[135deg]" size={36} />
                </button>
                <span className="text-sm text-white/90">Decline</span>
              </div>

              <div className="flex flex-col items-center gap-2">
                <button
                  onClick={handleAccept}
                  className="w-[72px] h-[72px] bg-[#34C759] rounded-full flex items-center justify-center hover:bg-[#34C759]/80 transition-colors animate-pulse"
                >
                  <FilledPhone className="text-white fill-current" size={36} />
                </button>
                <span className="text-sm text-white/90">Accept</span>
              </div>
            </>
          ) : callState !== 'ENDED' && callState !== 'DECLINED' ? (
            <div className="w-full flex justify-center">
              <button
                onClick={handleEnd}
                className="w-[72px] h-[72px] bg-[#FF3B30] rounded-full flex items-center justify-center hover:bg-[#FF3B30]/80 transition-colors"
              >
                <FilledPhone className="text-white fill-current transform rotate-[135deg]" size={36} />
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

// Exact filled phone handset SVG matching iOS
function FilledPhone(props: any) {
  const { size = 24, ...rest } = props
  return (
    <svg
      {...rest}
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z" />
    </svg>
  )
}

export default App
