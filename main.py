# Tikhomirov Mikhail, 2023
# github.com/miguelf0x


import asyncio
import logging
import os
import time

import interactions
from dotenv import load_dotenv

import ConfigHandler
import PromptParser
import UserInteraction
import WebuiRequests
import DBInteraction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")
logger.setLevel(level=logging.DEBUG)

load_dotenv()

bot = interactions.Client(token=os.environ['DISCORD_API_TOKEN'])
webui_url = ""

post_channel: interactions.Channel | None = None
best_channel: interactions.Channel | None = None
crsd_channel: interactions.Channel | None = None
err_channel: interactions.Channel | None = None

sd_models = None
tasks = []

db: DBInteraction.Database


def logged(func):
    def inner(ctx: interactions.CommandContext, *args, **kwags):
        logger.info(f"command {ctx.command.name}, channel = {ctx.channel_id},  args = {args}, kwargs = {kwags}")
        return func(ctx, *args, **kwags)


    inner.__name__ = func.__name__
    return inner


@bot.command()
@logged
async def help(ctx: interactions.CommandContext):
    """Show help message"""
    await UserInteraction.send_help_embed(ctx)


@bot.command()
@logged
async def state(ctx: interactions.CommandContext):
    """Check current task state"""
    try:
        description = await WebuiRequests.get_progress(webui_url)
        await UserInteraction.send_custom_embed(ctx, 'Current task state', description, "INFO")
    except Exception as e:
        await __handle_webui_exception(e, 'GET_STATUS')


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
            name="image_count",
            description="How many pictures to generate in parallel [1-8]",
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
            description="Image width (px) [32 - 1536]",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
        interactions.Option(
            name="height",
            description="Image height (px) [32 - 1536]",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
        interactions.Option(
            name="sampler",
            description="Sampler (usually \"Euler\", \"DPM2\" or \"PLMS\")",
            type=interactions.OptionType.STRING,
            required=False,
        ),
        interactions.Option(
            name="cfg_scale",
            description="Config scale adjusts how much result is close to prompt (bigger is more precise) [1.0 - 20.0]",
            type=interactions.OptionType.STRING,
            required=False,
        ),
        interactions.Option(
            name="neg_tags",
            description="Influences image generation by negating these tags [ your_custom_tags | long | short | mega ]",
            type=interactions.OptionType.STRING,
            required=False,
        ),
    ],
)
@logged
async def gen(ctx: interactions.CommandContext,
              tags: str,
              image_count: int = 0,
              steps: int = 0,
              width: int = 0,
              height: int = 0,
              sampler: str = "Euler",
              neg_tags: str = "short",
              cfg_scale: float = 6.0):
    """
    Generating image by your request
    """

    global post_channel
    global tasks

    if width > 1536 or height > 1536:
        await UserInteraction.send_error_embed(ctx, "Generating image", f'My GPU cannot handle this')
        return

    await UserInteraction.send_working_embed(ctx, f'Your request is registered!')

    prompt = PromptParser.get_prompt(image_count, steps, width, height, tags, neg_tags, sampler, cfg_scale)

    async def pad():
        try:
            logger.debug("Coroutine started, generating...")
            images = await WebuiRequests.post_generate(prompt=prompt, webui_url=webui_url,
                                                       post_directory=post_directory)

            logger.debug("Generated, sending..")
            for img in images:
                await send_generated_file(img, post_channel)

            logger.debug("Sent")

        except Exception as e:
            await __handle_webui_exception(e, "Generating image")

    # Hehe, I think this is asyncio bug - if no refrences to task is alive, task will be garbarage collected.
    # Let's create some dummy refrences? IDK
    tasks.append(asyncio.create_task(pad()))

    if len(tasks) > 15:
        logger.debug("Clearing tasks ^)")
        tasks = tasks[:10]


@bot.command()
@logged
async def test(ctx: interactions.CommandContext):
    """
    Generate test image [800x600, Steps=100, tags=1girl, red hair, long hair]
    """
    global tasks

    prompt = PromptParser.get_prompt(1, 100, 800, 600, "1girl, red hair, long hair", "short", "Euler", 7.0)

    await UserInteraction.send_working_embed(ctx, 'Your GPU is going to catch FIRE!')

    async def func():
        try:
            images = await WebuiRequests.post_generate(prompt=prompt, webui_url=webui_url,
                                                       post_directory=post_directory)

            for img in images:
                await send_generated_file(img, post_channel)

        except Exception as e:
            await __handle_webui_exception(e, "Generating image")

    logger.debug("Start generating coroutine")
    tasks.append(asyncio.create_task(func()))

    if len(tasks) > 15:
        tasks = tasks[:10]


@bot.command()
@logged
async def refresh(ctx: interactions.CommandContext):
    """Refresh models list"""
    try:
        await WebuiRequests.post_refresh_ckpt(webui_url)
        await get_sd_models_cached(refresh_models=True)
        await UserInteraction.send_success_embed(ctx, 'Checkpoints list refreshed')
    except Exception as e:
        await __handle_webui_exception(e, "Sending refresh-checkpoints POST request")


@bot.command()
@logged
async def models(ctx: interactions.CommandContext):
    """Show available models"""
    try:
        cached_models = await get_sd_models_cached()
        count = 0
        models_msg = ""
        for count, value in enumerate(cached_models):
            models_msg += f"[{count + 1}] Checkpoint: `{value['model_name']}`, " \
                          f"Hash: `{value['hash']}`\n"
        models_msg = f"Found {count + 1} models:\n" + models_msg
        await UserInteraction.send_custom_embed(ctx, 'Available models list', models_msg, "MESG")

    except Exception as e:
        await __handle_webui_exception(e, "Checking avalibe models")


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
@logged
async def find(ctx: interactions.CommandContext, modelhash: str):
    try:
        name = await WebuiRequests.find_model_by_hash(webui_url, modelhash)
        if name:
            await UserInteraction.send_success_embed(ctx, f'Found model `{name}` '
                                                          f'with hash `{modelhash}`')
        else:
            await UserInteraction.send_error_embed(ctx, f"Checkpoints search",
                                                   f'No checkpoints found with hash {modelhash}')

    except Exception as e:
        await __handle_webui_exception(e, "Selecting model")


@bot.command(
    name="select",
    description="Select model by hash or by /models index",
    options=[
        interactions.Option(
            name="model",
            description="Model hash or index from /models",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
@logged
async def select(ctx: interactions.CommandContext, model: str):
    try:
        avail_models = await get_sd_models_cached()
        select_by_index = -1
        try:
            select_by_index = int(model)
        except Exception:
            pass

        select_payload = None

        for ind, value in enumerate(avail_models):
            if value["hash"] == model or ind == (select_by_index - 1):
                select_payload = value["title"]
                break

        if select_payload is None:
            await UserInteraction.send_error_embed(ctx, "Selecting model", "Cant find model!")
            return

        await UserInteraction.send_working_embed(ctx, f'Trying to select model `{select_payload}` ')

        await WebuiRequests.select_model(webui_url, select_payload)

        await UserInteraction.send_success_embed(ctx, f'Model `{select_payload}` is now in use')
    except Exception as e:
        await __handle_webui_exception(e, 'Selecting model')


@bot.command(description="Skip current task")
@logged
async def skip(ctx: interactions.CommandContext):
    """Skip current task"""
    try:
        await WebuiRequests.user_interrupt(webui_url)
        await UserInteraction.send_success_embed(ctx, 'Image generating interrupted')
    except Exception as e:
        await __handle_webui_exception(e, "Interrupting request")


@bot.command(description="Get current active SD model")
@logged
async def current(ctx: interactions.CommandContext):
    try:
        get_data = await WebuiRequests.get_options(webui_url)
        model_name = get_data["sd_model_checkpoint"]
        await UserInteraction.send_info_embed(ctx, "Current SD model", model_name)
    except Exception as e:
        await __handle_webui_exception(e, "Checking current model")


@bot.component("upvote")
async def upvote(ctx: interactions.ComponentContext):
    await vote_counting(ctx, "up", best_threshold)


@bot.component("downvote")
async def downvote(ctx: interactions.ComponentContext):
    await vote_counting(ctx, "dn", crsd_threshold)


@bot.component("remove")
async def downvote(ctx: interactions.ComponentContext):
    await vote_counting(ctx, "rm", del_threshold)


async def vote_counting(ctx: interactions.ComponentContext, vote_type: str, threshold: int):
    embed = ctx.message.embeds[0]
    components = ctx.message.components
    votes = 0
    post_id = int(embed.fields[0].value.replace("#", ""))
    target_channel = ""
    image_score = []
    # Likes: 0, Dislikes: 0, Purge: 0

    match vote_type:
        case "up":
            await DBInteraction.create_db_record(db, post_id, ctx.user.id, 1)
            image_score = await DBInteraction.get_image_score(db, post_id)
            target_channel = best_channel
            votes = image_score[0]
        case "dn":
            await DBInteraction.create_db_record(db, post_id, ctx.user.id, -1)
            image_score = await DBInteraction.get_image_score(db, post_id)
            target_channel = crsd_channel
            votes = image_score[1]
        case "rm":
            await DBInteraction.create_db_record(db, post_id, ctx.user.id, -1000)
            image_score = await DBInteraction.get_image_score(db, post_id)
            votes = image_score[2]

    new_footer = "Likes: " + str(image_score[0]) + \
                 ", Dislikes: " + str(image_score[1]) + \
                 ", Purge: " + str(image_score[2])

    embed.set_footer(new_footer)
    message = await ctx.message.edit(embeds=embed, components=components)

    if votes == threshold:
        # await ctx.send("Your vote has been counted ;)", ephemeral=True)
        try:
            reply = await ctx.send(f"")
            await reply.delete()
        except Exception:
            pass
        if vote_type != "rm":
            new_message = await target_channel.send(embeds=message.embeds, components=message.components)
            message_link = new_message.url
            embed.add_field("Voting was moved", f"[Check it here]({message_link})")
            await message.edit(embeds=embed, components=None)
        else:
            await message.edit(f"Image #{post_id} was deleted by voting", embeds=None, components=None)
    else:
        # await ctx.send("Your vote has been counted ;)", ephemeral=True)
        try:
            reply = await ctx.send(f"")
            await reply.delete()
        except Exception:
            pass
        pass


@bot.event
async def on_ready():

    global post_channel
    global best_channel
    global crsd_channel
    global err_channel
    global db

    db = DBInteraction.Database(db_path=db_full_path)
    await db.connect()
    await DBInteraction.create_db_structure(db)

    post_channel = await interactions.get(bot, interactions.Channel, object_id=POST_CHANNEL_ID)
    best_channel = await interactions.get(bot, interactions.Channel, object_id=BEST_CHANNEL_ID)
    crsd_channel = await interactions.get(bot, interactions.Channel, object_id=CRSD_CHANNEL_ID)
    err_channel = await interactions.get(bot, interactions.Channel, object_id=ERR_CHANNEL_ID)

    await channel_poster(post_channel, post_files, post_directory)
    await channel_poster(best_channel, best_files, best_directory)
    await channel_poster(crsd_channel, crsd_files, crsd_directory)

    ui_state = False

    while True:
        await asyncio.sleep(check_interval)
        new_state = await WebuiRequests.get_check_online(webui_url)
        await check_state_change(ui_state, new_state)
        ui_state = new_state


async def __handle_webui_exception(e: Exception, action):
    global err_channel
    logger.exception(e)
    if e is WebuiRequests.ServerError:
        await send_offline_message()
    else:
        await UserInteraction.send_error_embed(err_channel, action, "Error processing request!")


async def get_sd_models_cached(refresh_models=False):
    global sd_models

    if sd_models is None or refresh_models:
        sd_models = await WebuiRequests.get_sd_models(webui_url)

    return sd_models


def get_files(source) -> set:
    """
    List all files in directory
    """
    files = set()
    os.makedirs(source, exist_ok=True)
    for file in os.listdir(source):
        fullpath = os.path.join(source, file)
        if os.path.isfile(fullpath):
            files.add(file)
    return files


async def send_generated_file(path: str, channel: interactions.Channel | None):
    """
    Send file by name to chanel
    """
    if channel is None:
        return

    name = os.path.basename(path).split('-')

    # Wanted image name format is {seed}-{sampler}-{steps}-{cfg_scale}{model_hash}-{width}-{height}.png
    # So we create checks for any other format
    model_name = "unknown"

    if len(name) >= 7:
        seed = name[0]
        sampler = name[1]
        steps = name[2]
        cfg_scale = name[3]
        modelhash = name[4]
        width = name[5]
        height = name[6].split('.')[0]

        if int(width) > int(height):
            width_aspect = int(width) / int(height)
            height_aspect = 1
        else:
            width_ratio = 1 / (int(width) / int(height))
            width_aspect = int(width) / int(height) * width_ratio
            height_aspect = 1 * width_ratio
            if divmod(height_aspect, 1.0)[1] == 0.0:
                height_aspect = int(height_aspect)
            else:
                height_aspect = round(height_aspect, 3)

        if divmod(width_aspect, 1.0)[1] == 0.0:
            width_aspect = int(width_aspect)
        else:
            width_aspect = round(height_aspect, 3)

    else:
        seed = 'unknown'
        sampler = 'unknown'
        steps = 'unknown'
        cfg_scale = 'unknown'
        modelhash = 'unknown'
        width = 'unknown'
        height = 'unknown'
        width_aspect = '?'
        height_aspect = '?'

    try:
        model_name = await WebuiRequests.find_model_by_hash(webui_url, modelhash)
    except Exception:
        pass

    image_description = ""
    resolution = f'{width}x{height} [{width_aspect}:{height_aspect}]'
    model = f'{model_name}'
    gensettings = f'{sampler}@{steps}, CFG scale: {cfg_scale}, Seed: {seed}'

    global db
    last_image_index = await DBInteraction.get_last_image_index(db)

    result = await UserInteraction.send_image(channel, path, image_description, resolution, model, gensettings,
                                              last_image_index)
    if result == 0:
        await DBInteraction.create_db_record(db, last_image_index+1, 0, 0)
    else:
        raise Exception


async def channel_poster(channel: interactions.Channel, files: set, directory: str):
    """
    Check all files in directory and send all files that not in `files` set to channel
    """
    current_files = get_files(directory)
    diffs = current_files - files

    if len(diffs) == 0:
        return

    if enable_img_announce == 1:
        await UserInteraction.send_found_messages(channel, len(diffs))
        time.sleep(announce_interval)

    for file_base_name in diffs:  # os.path
        file = os.path.join(directory, file_base_name)
        await send_generated_file(file, channel)
        files.add(file_base_name)


async def send_offline_message():
    await UserInteraction.send_custom_embed(err_channel,
                                            "WebUI is offline",
                                            f"Your prompts will NOT be executed",
                                            "CRIT")


async def send_online_message():
    await UserInteraction.send_custom_embed(err_channel,
                                            "WebUI is online",
                                            "Now your prompts will be executed",
                                            "GOOD")


async def check_state_change(last: bool, new: bool):
    global err_channel
    if last == new:
        return
    # if new : 
    #     await send_online_message()
    # else: 
    #     await send_offline_message()



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
    best_threshold = data["best_threshold"]
    crsd_threshold = data["crsd_threshold"]
    del_threshold = data["del_threshold"]
    db_full_path = data["db_full_path"]

    post_files = get_files(post_directory)
    best_files = get_files(best_directory)
    crsd_files = get_files(crsd_directory)

    # assign envvars and start bot
    POST_CHANNEL_ID = int(os.environ['POST_CHANNEL_ID'])
    BEST_CHANNEL_ID = int(os.environ['BEST_CHANNEL_ID'])
    CRSD_CHANNEL_ID = int(os.environ['CRSD_CHANNEL_ID'])
    ERR_CHANNEL_ID = int(os.environ['ERR_CHANNEL_ID'])

    bot.start()
