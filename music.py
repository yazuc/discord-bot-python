# This example requires the 'message_content' privileged intent to function.

import asyncio
import os
import subprocess
import discord
import json
import yt_dlp as youtube_dl

from discord.ext import commands


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.playing = []

    async def play_youtube_url(self, ctx, url):
        """Plays audio directly from a YouTube URL using yt_dlp and FFmpeg."""
        vc = ctx.voice_client
        self.playing.append(url)
        print(self.queue)

        if vc is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                vc = ctx.voice_client
            else:
                await ctx.send("Tu precisa estar em um canal de voz........")
                return

        if vc.is_playing():            
            vc.stop()

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True
        }

        try:
            await ctx.send(f"Carregando sua música")

            # Extract info directly (no subprocess)
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                audio_url = info_dict['url']
                title = info_dict.get('title', 'desconhecido')

            ffmpeg_options = {
                'options': '-vn'
            }

            # Create and play source
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            vc.play(source, after=lambda e: print(f"[DEBUG] Player error: {e}") if e else None)

            await ctx.send(f"Tocando agora: **{title}**")

            # Espera o áudio terminar
            while vc.is_playing() or vc.is_paused():
                await asyncio.sleep(1)

            await ctx.send("Música terminou!")
            self.queue.pop(url)

        except Exception as e:
            await ctx.send(f"❌ Ocorreu um erro: {e}")
            print(f"[ERRO] {e}")

    # --------------------------------------------------------
    # COMANDO USANDO O MÉTODO
    # --------------------------------------------------------
    @commands.command()
    async def play(self, ctx, *, url):
        """Streams a YouTube URL directly (without downloading)."""
        print(self)
        if(len(self.playing) == 0):
            await self.play_youtube_url(ctx, url)
        else:
            self.queue.append(url)
        


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
    async def stream(self, ctx, *, query):
        """Streams audio from YouTube into Discord without saving files"""

        # Ensure bot is in a voice channel
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You must be in a voice channel to use this command!")
                return

        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()

        try:
            await ctx.send(f"⏳ Streaming **{query}**...")

            # Start yt-dlp subprocess
            ytdlp_proc = subprocess.Popen(
                ["./yt-dlp", "-f", "bestaudio", "-o", "-", "--quiet", query],
                stdout=subprocess.PIPE
            )

            # Pipe yt-dlp stdout into ffmpeg subprocess
            ffmpeg_proc = subprocess.Popen(
                ["ffmpeg", "-i", "pipe:0", "-f", "s16le", "-ar", "48000", "-ac", "2", "pipe:1"],
                stdin=ytdlp_proc.stdout,
                stdout=subprocess.PIPE
            )

            # Pass ffmpeg stdout to Discord
            source = discord.FFmpegPCMAudio(ffmpeg_proc.stdout, pipe=True)
            vc.play(source, after=lambda e: print(f"Player error: {e}") if e else None)

            await ctx.send(f"▶️ Now playing: **{query}**")

        except Exception as e:
            await ctx.send(f"❌ Failed to stream audio: {e}")
            print(e)


    # @commands.command()
    # async def play(self, ctx, *, query):
    #     """Plays a local file from filesystem or downloads from YouTube using yt-dlp"""
    #     if os.path.exists("custom-name.mp4"):  
    #         os.remove("custom-name.mp4")
    #     # Ensure bot is in voice channel
    #     if ctx.voice_client is None:
    #         if ctx.author.voice:
    #             await ctx.author.voice.channel.connect()
    #         else:
    #             await ctx.send("Tu precisa estar em um canal de voz........")
    #             return

    #     vc = ctx.voice_client
    #     if vc.is_playing():
    #         vc.stop()

    #     # Prepare the command for yt-dlp
    #     ytdlp_cmd = [
    #         "./yt-dlp",
    #         query,  
    #         "--cookies", "../cookies.txt",
    #         "--extractor-args", "youtube:player_skip=configs,js,ios;player_client=webpage,android,web",
    #         "--concurrent-fragments", "12",
    #         "--no-warnings",
    #         "--no-colors",
    #         "--quiet",
    #         "--no-mtime",
    #         "--no-post-overwrites",
    #         "--no-embed-subs",
    #         "-o", "custom-name.mp4"
    #     ]

    #     # Run yt-dlp in a subprocess
    #     try:
    #         await ctx.send(f"Baixando a música do betinha")
    #         process = await asyncio.create_subprocess_exec(
    #             *ytdlp_cmd,
    #             stdout=asyncio.subprocess.PIPE,
    #             stderr=asyncio.subprocess.PIPE
    #         )

    #         stdout, stderr = await process.communicate()
    #         if process.returncode != 0:
    #             await ctx.send(f"❌ Failed to download: {stderr.decode().strip()}")
    #             print(stderr.decode())
    #             return

    #     except Exception as e:
    #         await ctx.send(f"❌ Error running yt-dlp: {e}")
    #         print(e)
    #         return

    #     # Play the downloaded file
    #     try:
    #         source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("custom-name.mp4"))
    #         vc.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
    #         await ctx.send(f"Tocando essa merda ai.")
    #     except Exception as e:
    #         await ctx.send(f"❌ Failed to play audio: {e}")
    #         print(e)

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