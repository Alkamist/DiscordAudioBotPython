import asyncio
import discord
import pyaudio
import librosa
import numpy as np

from discord.ext import commands
from micstream import MicStream

class MicSource(discord.PCMAudio):
    def __init__(self):
        self.stream = MicStream()

    def is_opus(self):
        return False

    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.stop()

    def read(self):
        return self.stream.read()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mic_source = MicSource()

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def monitor(self, ctx):
        """Enables voice monitoring."""

        self.mic_source.start()
        ctx.voice_client.play(self.mic_source, after=lambda e: print(f'Player error: {e}') if e else None)

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        self.mic_source.stop()
        await ctx.voice_client.disconnect()

    @monitor.before_invoke
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
                   description='An audio utility bot.')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

bot.add_cog(Music(bot))

with open('token.txt') as f:
    token = f.read()

bot.run(token)