# Tikhomirov Mikhail, 2023
# github.com/miguelf0x

import asyncio
import os
import discord
import yaml
from discord.ext import commands
from dotenv import load_dotenv

CHANNEL_ID = 1061711182085488691

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
        before = get_files(directory)
        await asyncio.sleep(check_interval)
        after = get_files(directory)

        for x in list(get_new_files(before, after)):
            file = f'{directory}/{x}'
            await channel.send(file=discord.File(file))
            await asyncio.sleep(send_interval)


if __name__ == "__main__":

    # load envvars
    load_dotenv()

    # load config
    with open('config.yaml') as f:
        try:
            data = yaml.load(f, Loader=yaml.FullLoader)
            directory, check_interval, send_interval = data['directory'], data['check_interval'], data['send_interval']
        except yaml.YAMLError as exception:
            print(exception)

    # start bot
    bot.run(os.environ['DISCORD_API_KEY'])
