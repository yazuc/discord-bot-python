# This example requires the 'message_content' intent.

import discord, json

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

f = open("./appconfig.json")
o = json.loads(f.read())

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(o['DISCORD_BOT_ID'])
