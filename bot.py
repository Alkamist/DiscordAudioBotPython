import asyncio
import discord
import pyaudio

from discord.ext import commands

pa = pyaudio.PyAudio()

class MicSource(discord.PCMAudio):
    def __init__(self):
        self.chunk_size = 1024
        self.stream = pa.open(format=pyaudio.paInt24,
                              channels=2,
                              rate=44100,
                              input=True,
                              frames_per_buffer=self.chunk_size)

    def is_opus(self):
        return False

    def read(self):
        return self.stream.read(self.chunk_size)

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
    async def monitor(self, ctx):
        """Enables voice monitoring."""

        ctx.voice_client.play(MicSource(), after=lambda e: print(f'Player error: {e}') if e else None)

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

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
bot.run('token')