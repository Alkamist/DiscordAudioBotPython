import pyaudio
import wave
import sys

class MicStream(object):
    def __init__(self):
        self.p = None
        self.pyaudio_stream = None
        self.byte_buffer = bytes()

    def is_active(self):
        return self.pyaudio_stream.is_active()

    def start(self):
        self.p = pyaudio.PyAudio()
        self.pyaudio_stream = self.p.open(
            format=pyaudio.paInt24,
            channels=2,
            rate=44100,
            input=True,
            output=False,
            stream_callback=self._callback,
            frames_per_buffer=1024,
        )

    def stop(self):
        self.pyaudio_stream.close()
        self.p.terminate()

    def read(self, size):
        while True:
            if self.byte_buffer != None and len(self.byte_buffer) >= size:
                data = self.byte_buffer[0:size]
                self.byte_buffer = self.byte_buffer[size:]
                return data

    def _callback(self, in_data, frame_count, time_info, flag):
        self.byte_buffer += in_data
        return None, pyaudio.paContinue

stream = MicStream()
stream.start()

print("* recording")

frames = []

samples_per_chunk = 3840
channel_count = 2
bytes_per_sample = 3

bytes_per_read = samples_per_chunk * channel_count * bytes_per_sample

for i in range(0, 20):
    data = stream.read(bytes_per_read)
    frames.append(data)

print("* done recording")

stream.stop()

wf = wave.open('output.wav', 'wb')
wf.setnchannels(channel_count)
wf.setsampwidth(bytes_per_sample)
wf.setframerate(44100)
wf.writeframes(b''.join(frames))
wf.close()