# Tikhomirov Mikhail, 2023
# github.com/miguelf0x

import asyncio
import base64
import io
import logging
import os

import discord
import requests
import yaml
from PIL import Image, PngImagePlugin
from discord.ext import commands
from dotenv import load_dotenv

import PromptTemplate
import TracedValue

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.command()
async def gen(ctx, *, arg):
    prompt = dict(PromptTemplate.PROMPT_TEMPLATE)
    prompt["prompt"] = arg

    logging.info(f"start task ")
    response = requests.post(url=f'{webui_url}/sdapi/v1/txt2img', json=prompt)

    if response.status_code > 400:
        logging.error(response.text)
        return

    r = response.json()

    os.makedirs(post_directory, exist_ok=True)

    for index, item in enumerate(r['images']):
        image = Image.open(io.BytesIO(base64.b64decode(item.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + item
        }
        response2 = requests.post(url=f'{webui_url}/sdapi/v1/png-info', json=png_payload)

        info = response2.json().get("info")
        info = info.split("\n")[2].split(',')
        result = {}

        for x in info:
            x = x.split(': ')
            x[0] = x[0].replace(" ", "")
            result[x[0]] = x[1]

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))

        seed = result["Seed"]
        sampler = result["Sampler"]
        steps = result["Steps"]
        model_hash = result["Modelhash"]

        post_directory_img = os.path.join(post_directory, f'{seed}-{sampler}-{steps}-{model_hash}.png')
        logging.info(f"save new img to {post_directory_img}")
        image.save(post_directory_img, pnginfo=pnginfo)

    await ctx.send("Yekekek")


def get_files(source):
    files = set()
    for file in os.listdir(source):
        fullpath = os.path.join(source, file)
        if os.path.isfile(fullpath):
            files.add(file)
    return files


def load_config(config_dir):

    try:
        with open(os.path.join(config_dir, 'config.yaml')) as f:
            try:
                conf = yaml.load(f, Loader=yaml.FullLoader)
                return conf

            except yaml.YAMLError as exception:
                print(exception)

    except FileNotFoundError as exception:
        print(exception)
        try:
            with open(os.path.join(config_dir, 'default-config.yaml')) as f:
                try:
                    conf = yaml.load(f, Loader=yaml.FullLoader)
                    print("config.yaml cannot be read, loaded settings from default-config.yaml")
                    return conf

                except yaml.YAMLError as exception:
                    print(exception)

        except FileNotFoundError as exception:
            print(exception)


async def channel_poster(channel, files, directory):
    await asyncio.sleep(check_interval)
    if files.set(get_files(directory)) == 1:
        diff = files.get_diff()
        difflen = len(diff)

        if difflen != 0:
            await channel.send(f'Found {difflen} new picture(s). I will post them soon!')
            await asyncio.sleep(announce_interval)

            for x in diff:
                file = f'{directory}/{x}'

                img = Image.open(file)
                width, height = img.size
                img.close()
                name = x.split('-')

                # Wanted image name format is seed-sampler-steps-model_hash
                # So we create checks for any other format

                if len(name) > 1:

                    try:
                        if len(name[2]) > 19:
                            sampler = 'unknown'
                        else:
                            sampler = name[2]
                    except IndexError as sampler_index_exception:
                        print(sampler_index_exception)
                        sampler = 'unknown'

                    try:
                        if len(name[4]) > 8:
                            modelhash = 'unknown'
                        else:
                            modelhash = name[4]
                    except IndexError as index_exception:
                        print(index_exception)
                        modelhash = 'unknown'

                    steps = name[3]
                    seed = name[1]

                else:

                    modelhash = 'unknown'
                    sampler = 'unknown'
                    steps = 'unknown'
                    seed = 'unknown'

                await channel.send(f'Model hash: {modelhash}, Sampler: {sampler}, Steps: {steps}, '
                                   f'Seed: {seed}\nResolution: {width}x{height} [AR: {round(width / height, 3)}]',
                                   file=discord.File(file))

                await asyncio.sleep(send_interval)


@bot.event
async def on_ready():
    post_channel = bot.get_channel(int(POST_CHANNEL_ID))
    best_channel = bot.get_channel(int(BEST_CHANNEL_ID))
    crsd_channel = bot.get_channel(int(CRSD_CHANNEL_ID))
    post_files = TracedValue.TracedValue(get_files(post_directory))
    best_files = TracedValue.TracedValue(get_files(best_directory))
    crsd_files = TracedValue.TracedValue(get_files(crsd_directory))

    while True:
        await channel_poster(post_channel, post_files, post_directory)
        await channel_poster(best_channel, best_files, best_directory)
        await channel_poster(crsd_channel, crsd_files, crsd_directory)


if __name__ == "__main__":

    # load .env
    load_dotenv()

    # load config files from 'config' directory
    data = load_config('config')
    announce_interval = data["announce_interval"]
    check_interval = data["check_interval"]
    send_interval = data["send_interval"]
    post_directory = data["post_directory"]
    best_directory = data["best_directory"]
    crsd_directory = data["crsd_directory"]
    webui_url = data["webui_url"]

    # assign envvars and start bot
    POST_CHANNEL_ID = os.environ['POST_CHANNEL_ID']
    BEST_CHANNEL_ID = os.environ['BEST_CHANNEL_ID']
    CRSD_CHANNEL_ID = os.environ['CRSD_CHANNEL_ID']

    bot.run(os.environ['DISCORD_API_KEY'])
