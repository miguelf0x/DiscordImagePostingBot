# Tikhomirov Mikhail, 2023
# github.com/miguelf0x

import asyncio
import os
import discord
import yaml
from PIL import Image
from discord.ext import commands
from dotenv import load_dotenv


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


class TracedValue:
    def __init__(self, value):
        self.prev_value = None
        self.cur_value = value

    def get(self):
        return self.cur_value

    def force_set(self, value):
        self.cur_value = value

    def set(self, value):
        if self.cur_value != value:
            self.prev_value = self.cur_value
            self.cur_value = value
            return 1
        else:
            return 0

    def get_diff(self):
        return self.cur_value - self.prev_value


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
    files = TracedValue(get_files(directory))

    while True:

        await asyncio.sleep(check_interval)
        if files.set(get_files(directory)) == 1:
            diff = files.get_diff()
            difflen = len(diff)

            if difflen != 0:
                await channel.send(f'My master has added {difflen} picture(s) to favourites. I will post them soon!')
                await asyncio.sleep(send_interval)

                for x in diff:
                    file = f'{directory}/{x}'

                    img = Image.open(file)
                    width, height = img.size
                    img.close()
                    name = x.split('-')

                    if len(name[4]) > 8:
                        modelhash = 'unknown'
                    else:
                        modelhash = name[4]

                    await channel.send(f'Model hash: {modelhash}, Sampler: {name[2]}, Steps: {name[3]}, Seed: {name[1]}\n'
                                       f'Resolution: {width}x{height} [AR: {round(width/height, 3)}]',
                                       file=discord.File(file))

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
    f.close()

    # start bot
    CHANNEL_ID = os.environ['CHANNEL_ID']
    bot.run(os.environ['DISCORD_API_KEY'])

