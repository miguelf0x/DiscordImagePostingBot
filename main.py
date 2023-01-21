# Tikhomirov Mikhail, 2023
# github.com/miguelf0x

import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

CHANNEL_ID = 1061711182085488691
DELAY = 5

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


def get_files(source):
    files = set()
    for file in os.listdir(source):
        fullpath = os.path.join(source, file)
        if os.path.isfile(fullpath):
            files.add(file)

    return files


def get_new_files(before, after):
    return after - before


@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    while True:
        before = get_files(PATH)
        await asyncio.sleep(20)
        after = get_files(PATH)

        for x in list(get_new_files(before, after)):
            file = f'{PATH}\{x}'
            await channel.send(file=discord.File(file))
            await asyncio.sleep(10)


if __name__ == "__main__":
    load_dotenv()
    PATH = os.environ['PATH']
    bot.run(os.environ['DISCORD_API_KEY'])
