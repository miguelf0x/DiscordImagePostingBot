# Tikhomirov Mikhail, 2023
# github.com/miguelf0x


import asyncio
import os

from PIL import Image

from dotenv import load_dotenv

import PromptParser
import TracedValue
import WebuiRequests
import UserInteraction
import ConfigHandler
import interactions

load_dotenv()

bot = interactions.Client(token=os.environ['DISCORD_API_TOKEN'])
webui_url = ""


@bot.command()
async def help(ctx: interactions.CommandContext):
    """Show help message"""
    await UserInteraction.send_help_embed(ctx)


@bot.command()
async def state(ctx: interactions.CommandContext):
    """Check current task state"""
    await WebuiRequests.get_progress(ctx, webui_url)


@bot.command(
    name="gen",
    description="Generate image using txt2img",
    options=[
        interactions.Option(
            name="tags",
            description="Image tags divided with comma",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="batch_count",
            description="How many pictures generate in parallel [1-8]",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
        interactions.Option(
            name="steps",
            description="Interference steps count [0-200]",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
        interactions.Option(
            name="width",
            description="Image width (px)",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
        interactions.Option(
            name="height",
            description="Image height (px)",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
    ],
)
async def gen(ctx: interactions.CommandContext, tags: str, batch_count: int = 0, steps: int = 0,
              width: int = 0, height: int = 0):
    if online == 0:
        await UserInteraction.send_success_embed(ctx, "Your request is registered")
        PromptParser.image_gen(ctx, webui_url, post_directory, batch_count, steps, width, height, tags)
    else:
        await UserInteraction.send_error_embed(ctx, "Receiveing request", "WebUI offline")


@bot.command()
async def refresh(ctx: interactions.CommandContext):
    """Refresh models list"""
    await WebuiRequests.post_refresh_ckpt(ctx, webui_url)


@bot.command()
async def models(ctx: interactions.CommandContext):
    """Show available models"""
    await WebuiRequests.get_sd_models(ctx, webui_url, "1")


@bot.command(
    name="find",
    description="Search model by hash",
    options=[
        interactions.Option(
            name="modelhash",
            description="Searched model hash",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def find(ctx: interactions.CommandContext, modelhash: str):
    await WebuiRequests.find_model_by_hash(ctx, webui_url, modelhash)


@bot.command(
    name="select",
    description="Select model by hash or by /models id",
    options=[
        interactions.Option(
            name="model",
            description="Model hash or id from /models",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def select(ctx: interactions.CommandContext, model: str):
    await WebuiRequests.select_model_by_arg(ctx, webui_url, model)


@bot.command()
async def skip(ctx: interactions.CommandContext):
    """Skip current task"""
    await WebuiRequests.user_interrupt(ctx, webui_url)


def get_files(source):
    files = set()
    for file in os.listdir(source):
        fullpath = os.path.join(source, file)
        if os.path.isfile(fullpath):
            files.add(file)
    return files


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

                embedding = interactions.Embed()
                embedding.title = 'Generated image'
                embedding.description = (f'Model hash: `{modelhash}`, Sampler: `{sampler}`\n'
                                         f'Steps: `{steps}`, Seed: `{seed}`\n'
                                         f'Resolution: `{width}x{height} '
                                         f'[AR: {round(width / height, 3)}]`')
                image = interactions.File(file)
                embedding.set_image(url=f"attachment://{x}")

                await channel.send(files=image, embeds=embedding)
                await asyncio.sleep(send_interval)


async def check_state(error_channel):

    errorfile = '.temp/.error'
    offlinefile = '.temp/.offline'

    global online

    if os.path.exists(errorfile):
        with open(errorfile) as f:
            error = str(f.readline()).split(": ")
            await UserInteraction.send_error_embed(error_channel, error[0], error[1])
        os.remove(errorfile)

    offline = await WebuiRequests.get_check_online(webui_url)

    if offline is not False:
        if not os.path.exists(offlinefile):
            online = -1
            await UserInteraction.send_custom_embed(error_channel,
                                                    "WebUI is offline",
                                                    "Your prompts will NOT be executed",
                                                    "CRIT")
            with open(offlinefile, 'w') as f:
                f.write(offline[0] + str(offline[1]))
    elif os.path.exists(offlinefile):
        os.remove(offlinefile)
        online = 0
        await UserInteraction.send_custom_embed(error_channel,
                                                "WebUI is online",
                                                "Now your prompts will be executed",
                                                "GOOD")


@bot.event
async def on_ready():
    post_channel = await interactions.get(bot, interactions.Channel, object_id=POST_CHANNEL_ID)
    best_channel = await interactions.get(bot, interactions.Channel, object_id=BEST_CHANNEL_ID)
    crsd_channel = await interactions.get(bot, interactions.Channel, object_id=CRSD_CHANNEL_ID)
    err_channel = await interactions.get(bot, interactions.Channel, object_id=ERR_CHANNEL_ID)
    post_files = TracedValue.TracedValue(get_files(post_directory))
    best_files = TracedValue.TracedValue(get_files(best_directory))
    crsd_files = TracedValue.TracedValue(get_files(crsd_directory))

    while True:
        await check_state(err_channel)
        await channel_poster(post_channel, post_files, post_directory)
        await channel_poster(best_channel, best_files, best_directory)
        await channel_poster(crsd_channel, crsd_files, crsd_directory)


if __name__ == "__main__":
    # load .env
    load_dotenv()

    # load config files from 'config' directory
    data = ConfigHandler.load_config('config')
    announce_interval = data["announce_interval"]
    check_interval = data["check_interval"]
    send_interval = data["send_interval"]
    post_directory = data["post_directory"]
    best_directory = data["best_directory"]
    crsd_directory = data["crsd_directory"]
    webui_url = data["webui_url"]
    enable_img_announce = data["enable_image_announce"]

    # assign envvars and start bot
    POST_CHANNEL_ID = int(os.environ['POST_CHANNEL_ID'])
    BEST_CHANNEL_ID = int(os.environ['BEST_CHANNEL_ID'])
    CRSD_CHANNEL_ID = int(os.environ['CRSD_CHANNEL_ID'])
    ERR_CHANNEL_ID = int(os.environ['ERR_CHANNEL_ID'])
    online = None

    bot.start()
