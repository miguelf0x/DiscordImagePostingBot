# Tikhomirov Mikhail, 2023
# github.com/miguelf0x

import asyncio
import os
import threading

import discord
import yaml
from PIL import Image
from discord.ext import commands
from dotenv import load_dotenv

import PromptTemplate
import TracedValue
import WebuiRequests
import SafeTypes

bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())


@commands.command(aliases=['h', 'help', 'commands'])
async def man(ctx):
    await ctx.send("Currently available commands list:\n"
                   "$g (req), $gen (req), $generate (req) - generate image by (req) tags\n"
                   "$prog, $state, $progress - show current task ETA, step and completion %\n"
                   "$h, $help, $commands - show this help message")


@commands.command(aliases=['prog', 'state'])
async def progress(ctx):
    await WebuiRequests.get_progress(ctx, webui_url)


@commands.command(aliases=['g', 'generate'])
async def gen(ctx, *, arg):
    prompt = dict(PromptTemplate.PROMPT_TEMPLATE)
    trimmed = arg.split(",", 3)

    steps = SafeTypes.safe_cast(trimmed[0], "int")
    width = SafeTypes.safe_cast(trimmed[1], "int")
    height = SafeTypes.safe_cast(trimmed[2], "int")

    if steps > 0 and width > 0 and height > 0:
        prompt["steps"] = str(steps)
        prompt["width"] = str(width)
        prompt["height"] = str(height)
        prompt["prompt"] = str(trimmed[3])
    elif steps > 0:
        prompt["prompt"] = str(trimmed[1])+str(trimmed[2])+str(trimmed[3])
        prompt["steps"] = str(steps)
    else:
        prompt["steps"] = arg


    gen_thread = threading.Thread(target=WebuiRequests.post_generate, args=(prompt, webui_url, post_directory))
    gen_thread.start()


@commands.command(aliases=['ref', 'refresh'])
async def refresh_ckpt(ctx):
    await WebuiRequests.post_refresh_ckpt(ctx, webui_url)


@commands.command(aliases=['models', 'list_models'])
async def show_ckpt(ctx):
    await WebuiRequests.get_sd_models(ctx, webui_url, "1")



@commands.command(aliases=['find_model', 'find'])
async def find_ckpt(ctx, arg):
    await WebuiRequests.find_model_by_hash(ctx, webui_url, arg)


@commands.command(aliases=['set_model', 'set'])
async def set_ckpt(ctx, arg):
    await WebuiRequests.select_model_by_arg(ctx, webui_url, arg)


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

            if enable_img_announce == 1:
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

                    seed = name[0]
                    sampler = name[1]
                    steps = name[2]
                    modelhash = name[3].split('.')[0]

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
    enable_img_announce = data["enable_image_announce"]

    # assign envvars and start bot
    POST_CHANNEL_ID = os.environ['POST_CHANNEL_ID']
    BEST_CHANNEL_ID = os.environ['BEST_CHANNEL_ID']
    CRSD_CHANNEL_ID = os.environ['CRSD_CHANNEL_ID']

    bot.remove_command("help")

    # noinspection PyTypeChecker
    bot.add_command(man)

    # noinspection PyTypeChecker
    bot.add_command(progress)

    # noinspection PyTypeChecker
    bot.add_command(gen)

    # noinspection PyTypeChecker
    bot.add_command(refresh_ckpt)

    # noinspection PyTypeChecker
    bot.add_command(show_ckpt)

    # noinspection PyTypeChecker
    bot.add_command(find_ckpt)

    # noinspection PyTypeChecker
    bot.add_command(set_ckpt)

    bot.run(os.environ['DISCORD_API_KEY'])
