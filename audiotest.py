import wave
import sys
from micstream import MicStream

stream = MicStream()
stream.start()

print("* recording")

audio = bytes()

for i in range(0, 5):
    data = stream.read()
    audio += data

print("* done recording")

stream.stop()

wf = wave.open('output.wav', 'wb')
wf.setnchannels(2)
wf.setsampwidth(2)
wf.setframerate(48000)
wf.writeframes(audio)
wf.close()