import yt_dlp

def search_youtube(query):
    ydl_opts = {"format": "bestaudio/best", "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
    return result['webpage_url']

url = search_youtube("Gangstar Torture Dance FULL SONG JoJo")
print(url)