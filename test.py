import asyncio
import os
import subprocess
import discord
import json
import sys
import yt_dlp as youtube_dl
from discord.ext import commands
from subprocess import call
if sys.version_info.major == 3:
    from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
else:
    from urllib import urlencode
    from urlparse import urlparse, urlunparse, parse_qs


print("hi")

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

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    url = "https://youtu.be/cY-AiueP4tU?si=u2mpiRjfrneiuuiG"
    #url = "cY-AiueP4tU"
    u = urlparse(url)
    query = parse_qs(u.query, keep_blank_values=True)
    query.pop('list', None)
    query.pop('start_radio', None)
    #url = urlunparse(u._replace(query=urlencode(query, True)))
    if u.hostname == "youtu.be":
        url = u.path.split("/")[1]
    info_dict = ydl.extract_info(f"ytsearch1:{url}", download=False)
    print(info_dict)