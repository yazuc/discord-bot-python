# This example requires the 'message_content' privileged intent to function.

import asyncio

import discord
import json
import yt_dlp as youtube_dl

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, options='-vn'), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        print(f"[DEBUG] join chamado. channel={channel}")
        print(f"[DEBUG] ctx.author.voice = {ctx.author.voice}")

        if channel is None:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                print(f"[DEBUG] Nenhum canal especificado, usando {channel.name}")
            else:
                await ctx.send("Você precisa estar em um canal de voz ou informar o nome do canal!")
                print("[DEBUG] Autor não está em canal de voz.")
                return

        try:
            if ctx.voice_client is not None:
                print(f"[DEBUG] Bot já conectado, movendo para {channel.name}")
                await ctx.voice_client.move_to(channel)
            else:
                print(f"[DEBUG] Tentando conectar em {channel.name}")
                await channel.connect()
            await ctx.send(f"Conectado em: **{channel.name}** 🎶")
            print(f"[DEBUG] Conectado com sucesso em {channel.name}")
        except Exception as e:
            print(f"[ERRO] Falha ao conectar: {e}")
            await ctx.send(f"❌ Erro ao tentar entrar em **{channel.name}**: {e}")


    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {query}')

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def custom(self, ctx):
        """Plays a local file named custom-name.mp4 from current folder"""

        file_name = "custom-name.mp4"  # file must exist in same folder as script

        # Ensure the bot is in a voice channel
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You must be in a voice channel to use this command!")
                return

        vc = ctx.voice_client

        # Stop current playback if any
        if vc.is_playing():
            vc.stop()

        try:
            # Create audio source from local file
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(file_name))
            vc.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
            await ctx.send(f"▶️ Now playing: **{file_name}**")
        except Exception as e:
            await ctx.send(f"❌ Failed to play {file_name}: {e}")
            print(f"[ERROR] {e}")


    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send('Not connected to a voice channel.')

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f'Changed volume to {volume}%')

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                raise commands.CommandError('Author not connected to a voice channel.')
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    description='Relatively simple music bot example',
    intents=intents,
)


@bot.event
async def on_ready():
    # Tell the type checker that User is filled up at this point
    assert bot.user is not None

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    f = open("./appconfig.json")
    o = json.loads(f.read())
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(o['DISCORD_BOT_ID'])


asyncio.run(main())