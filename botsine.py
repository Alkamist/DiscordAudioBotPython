import asyncio
import discord

from discord.ext import commands

import numpy as np
from math import *

def pcm_to_float(sig, dtype='float32'):
    sig = np.asarray(sig)
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
    sig = np.asarray(sig)
    if sig.dtype.kind != 'f':
        raise TypeError("'sig' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind not in 'iu':
        raise TypeError("'dtype' must be an integer type")

    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)

class SineStream():
    def __init__(self, frequency, sample_rate, time):
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.time = time
        self.phase = 0.0

    def _read_stereo_amplitudes(self):
        num_channels = 2
        block_size = int(self.time * self.sample_rate)
        values = [0] * block_size * num_channels
        for n in range(block_size):
            amp = sin(2.0 * pi * self.phase)
            location = n * num_channels
            values[location] = amp
            values[location + 1] = amp
            self.phase += self.frequency / self.sample_rate
            if self.phase > 1.0:
                self.phase -= 1.0
        return values

    def read(self):
        amps = self._read_stereo_amplitudes()
        return float_to_pcm(amps).tobytes()

class SineSource(discord.PCMAudio):
    def __init__(self, frequency):
        self.stream = SineStream(frequency, 48000.0, 0.02)

    def is_opus(self):
        return False

    def read(self):
        return self.stream.read()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def sinwave(self, ctx):
        """Plays a sine wave"""

        ctx.voice_client.play(SineSource(440.0), after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing sine wave.')

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @sinwave.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='Relatively simple music bot example')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

bot.add_cog(Music(bot))
bot.run('token')