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
        self.queue = asyncio.Queue()
        self.playing = False


    async def play_youtube_url(self, ctx, url):
        """Plays audio directly from a YouTube URL using yt_dlp and FFmpeg."""
        vc = ctx.voice_client       

        self.playing = True
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
            'noplaylist': True,
            'cookiefile': './cookies.txt',  # caminho para cookies
            'extractor_args': {
                'youtube': {
                    'player_skip': ['configs', 'js', 'ios'],
                    'player_client': ['webpage', 'android', 'web']
                }
            },
            'concurrent_fragment_downloads': 12,
            'no_warnings': True,
            'nocheckcertificate': True,
            'outtmpl': 'custom-name.mp4',  # só usado se for baixar (você está streamando)
            'overwrites': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'source_address': '0.0.0.0',  # evita problemas de rede no Raspberry
        }

        try:
            await ctx.send(f"Carregando sua música")

            # Extract info directly (no subprocess)
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(f"ytsearch1:{url}", download=False)
                first_result = info_dict['entries'][0]
                audio_url = first_result['url']
                title = first_result.get('title', 'desconhecido')

            ffmpeg_options = {
                'before_options': (
                    '-reconnect 1 '
                    '-reconnect_streamed 1 '
                    '-reconnect_delay_max 5 '
                    '-nostdin'
                ),
                'options': '-vn'
            }

            # Create and play source
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            vc.play(source, after=lambda e: print(f"[DEBUG] Player error: {e}") if e else None)

            await ctx.send(f"Tocando agora: **{title}**")

            # Espera o áudio terminar
            while vc.is_playing() or vc.is_paused():
                # self.playing = False           
                await asyncio.sleep(1)

            if(not self.queue.empty()):
                print("vai tocar a otra musica")
                await self.play_youtube_url(ctx, await self.queue.get())

            
            await ctx.send("Música terminou!")
            # self.queue.pop(url)

        except Exception as e:
            print(f"[ERRO] {e}")

    # --------------------------------------------------------
    # COMANDO USANDO O MÉTODO
    # --------------------------------------------------------
    @commands.command()
    async def play(self, ctx, *, url):
        """Streams a YouTube URL directly (without downloading)."""       
        print(self.playing)
        if not self.playing:
            await self.play_youtube_url(ctx, url)
        else:
            await self.queue.put(url)
            print(self.queue)

    @commands.command()
    async def q(self, ctx, *, url):
        await self.queue.put(url)
        await ctx.send("Música adicionada a fila.")
        print(self.queue)

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
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
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

    print(f'gay sex as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    f = open("./appconfig.json")
    o = json.loads(f.read())
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(o['DISCORD_BOT_ID'])


asyncio.run(main())