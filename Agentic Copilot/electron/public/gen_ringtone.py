import wave, struct, math

sample_rate = 44100
duration = 4.0 # seconds
# UK/Europe style ringing: 400Hz + 450Hz
freq1, freq2 = 400.0, 450.0

obj = wave.open('ringtone.wav', 'w')
obj.setnchannels(1)
obj.setsampwidth(2)
obj.setframerate(sample_rate)

for i in range(int(sample_rate * duration)):
    t = float(i) / sample_rate
    # Ring pattern: 0.4s on, 0.2s off, 0.4s on, 2.0s off
    cycle_time = t % 3.0
    if (0.0 <= cycle_time < 0.4) or (0.6 <= cycle_time < 1.0):
        # Play tone
        val = math.sin(2.0 * math.pi * freq1 * t) + math.sin(2.0 * math.pi * freq2 * t)
        val = val * 0.5 * 32767.0
    else:
        val = 0.0
    data = struct.pack('<h', int(val))
    obj.writeframesraw(data)

obj.close()
