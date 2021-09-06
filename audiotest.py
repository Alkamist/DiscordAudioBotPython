import numpy as np
import librosa
import pyaudio
import wave
import sys

def pcm_to_float(sig, dtype='float64'):
    sig = np.asarray(sig).transpose()
    if sig.dtype.kind not in 'iu':
        raise TypeError("'sig' must be an array of integers")
    dtype = np.dtype(dtype)
    if dtype.kind != 'f':
        raise TypeError("'dtype' must be a floating point type")

    i = np.iinfo(sig.dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig.astype(dtype) - offset) / abs_max

def float_to_pcm(sig, dtype='int16'):
    sig = np.asarray(sig).transpose()
    if sig.dtype.kind != 'f':
        raise TypeError("'sig' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind not in 'iu':
        raise TypeError("'dtype' must be an integer type")

    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)

def pcm24_to_32(data, channels=1, normalize=True):
    if len(data) % 3 != 0:
        raise ValueError('Size of data must be a multiple of 3 bytes')

    out = np.zeros(len(data) // 3, dtype='<i4')
    out.shape = -1, channels
    temp = out.view('uint8').reshape(-1, 4)
    if normalize:
        # write to last 3 columns, leave LSB at zero
        columns = slice(1, None)
    else:
        # write to first 3 columns, leave MSB at zero
        columns = slice(None, -1)
    temp[:, columns] = np.frombuffer(data, dtype='uint8').reshape(-1, 3)
    return out.transpose()

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
                data_pcm = pcm24_to_32(self.byte_buffer[0:size], channels=2)
                data = pcm_to_float(data_pcm)
                self.byte_buffer = self.byte_buffer[size:]
                return data

    def _callback(self, in_data, frame_count, time_info, flag):
        self.byte_buffer += in_data
        return None, pyaudio.paContinue

stream = MicStream()
stream.start()

print("* recording")

audio = []

samples_per_chunk = 3840
channel_count = 2
bytes_per_sample = 3

bytes_per_read = samples_per_chunk * channel_count * bytes_per_sample

for i in range(0, 50):
    data = stream.read(bytes_per_read)
    audio.append(data)

print("* done recording")

stream.stop()

audio = np.concatenate(audio).transpose()
audio = librosa.resample(audio, 44100, 96000, res_type='kaiser_fast')
frames = float_to_pcm(audio)

wf = wave.open('output.wav', 'wb')
wf.setnchannels(channel_count)
wf.setsampwidth(2)
wf.setframerate(96000)
wf.writeframes(b''.join(frames))
wf.close()