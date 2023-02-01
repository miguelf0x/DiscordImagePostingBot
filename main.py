# Tikhomirov Mikhail, 2023
# github.com/miguelf0x


import asyncio
import os
import threading
import time
import logging
from dotenv import load_dotenv

import PromptParser
import TracedValue
import WebuiRequests
import UserInteraction
import ConfigHandler
import interactions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")
logger.setLevel(level=logging.DEBUG)

load_dotenv()

bot = interactions.Client(token=os.environ['DISCORD_API_TOKEN'])
webui_url = ""

post_channel:interactions.Channel|None = None
best_channel:interactions.Channel|None = None
crsd_channel:interactions.Channel|None = None
err_channel :interactions.Channel|None = None

sd_models = None
tasks = []

def logged(func):
    def inner(ctx:interactions.CommandContext, *args, **kwags):
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
    logger.debug("/state command")
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
@logged
async def gen(ctx: interactions.CommandContext, 
              tags: str, 
              image_count: int = 0, 
              steps: int = 0,
              width: int = 0, 
              height: int = 0):
    """
    Processing /gen request
    """

    global post_channel
    global tasks
    
    if (width > 1500 or height > 1500):
        await UserInteraction.send_error_embed(ctx, "Generating image", f'Sorry, but dont crash my GPU')
        return

    await UserInteraction.send_working_embed(ctx, f'Your request is registered!')

    prompt = PromptParser.get_prompt(image_count, steps, width, height, tags)
   
    async def pad():
        try:
            logger.debug("Coroutine started, generating...")
            images = await WebuiRequests.post_generate(prompt=prompt, webui_url=webui_url, post_directory=post_directory)
            
            logger.debug("Generated, sending..")
            for img in images:
                await send_generated_file(img, post_channel)

            logger.debug("Sent")

        except Exception as e:
            await __handle_webui_exception(e, "Generating image")

    # Hehe, i think this is asyncio bug - if no refrences to task is alive, task will be garbarage collected. Lets create some dummy refrences? idk
    tasks.append(asyncio.create_task(pad()))

    
    if len(tasks) > 15:
        logger.debug("Clearing tasks ^)")
        tasks = tasks[:10]
   
@bot.command()
@logged
async def test(ctx: interactions.CommandContext):
    """
    Generate test image [512x512, Steps=100, tags=1girl, blue hair, bobcut, portrait, blush] \n
    LETS BURN YOUR GPU UAAAAAARGH
    """
    global tasks

    prompt = PromptParser.get_prompt(1, 100, 512, 512, "1girl, blue hair, bobcut, portrait, blush")

    await UserInteraction.send_success_embed(ctx, f'Your GPU is going to FIRE!')

    async def func():
        try:
            images = await WebuiRequests.post_generate(prompt=prompt, webui_url=webui_url, post_directory=post_directory)
            
            for img in images:
                await send_generated_file(img, post_channel)

        except Exception as e:
            await __handle_webui_exception(e,  "Generating image")

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
        await get_sd_models_cached(refresh=True)
        await UserInteraction.send_success_embed(ctx, 'Checkpoints list refreshed')
    except Exception as e:
        await __handle_webui_exception(e, "Sending refresh-checkpoints POST request")

@bot.command()
@logged
async def models(ctx: interactions.CommandContext):
    """Show available models"""
    logger.info("/models")
    try:
        models = await get_sd_models_cached()
        count = 0
        models_msg = ""
        for count, value in enumerate(models):
            models_msg += f"[{count+1}] Checkpoint: `{value['model_name']}`, " \
                      f"Hash: `{value['hash']}`\n"
        models_msg = f"Found {count+1} models:\n" + models_msg
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
            await UserInteraction.send_error_embed(ctx, f"Checkpoints search", f'No checkpoints '
                                                                               f'found with hash {modelhash}')

    except Exception as e:
        await __handle_webui_exception(e, "Selecting model")
    
@bot.command(
    name="select",
    description="Select model by hash or by /models id(haha not works yet)",
    options=[
        interactions.Option(
            name="model",
            description="Model hash or id from /models",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
@logged
async def select(ctx: interactions.CommandContext, model: str):
    try:
        models = await get_sd_models_cached()
        select_by_index = -1
        try:
            select_by_index = int(model)
        except Exception as e:
            pass
        
        select_payload = None

        for ind, value in enumerate(models):
            if value["hash"] == model or ind == select_by_index:
                select_payload = value["title"]
                break

        if select_payload == None:
            await UserInteraction.send_error_embed(ctx, "Selecting model", "Cant find model!")
            return
        
        await UserInteraction.send_working_embed(ctx, f'Trying to select checkpoint `{select_payload}` ')    
        
        await WebuiRequests.select_model(webui_url, select_payload)

        await UserInteraction.send_success_embed(ctx, f'Checkpoint `{select_payload}` is now in use')
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
async def current_model(ctx:interactions.CommandContext):
    try:
        data = await WebuiRequests.get_options(webui_url)
        model_name = data["sd_model_checkpoint"]
        await UserInteraction.send_info_embed(ctx, "Current SD model", model_name)
    except Exception as e:
        await __handle_webui_exception(e, "Checking current model")


@bot.event
async def on_ready():
    global post_channel
    global best_channel
    global crsd_channel
    global err_channel

    post_channel = await interactions.get(bot, interactions.Channel, object_id=POST_CHANNEL_ID)
    best_channel = await interactions.get(bot, interactions.Channel, object_id=BEST_CHANNEL_ID)
    crsd_channel = await interactions.get(bot, interactions.Channel, object_id=CRSD_CHANNEL_ID)
    err_channel = await interactions.get(bot, interactions.Channel, object_id=ERR_CHANNEL_ID)
    
    await channel_poster(post_channel, post_files, post_directory)
    await channel_poster(best_channel, best_files, best_directory)
    await channel_poster(crsd_channel, crsd_files, crsd_directory)

    state = False
    while True:
        await asyncio.sleep(check_interval)
        new_state = await WebuiRequests.get_check_online(webui_url)
        await check_state_change(state, new_state)
        state = new_state
                
async def __handle_webui_exception(e:Exception, action):
    global err_channel
    logger.error(e)
    if e is WebuiRequests.ServerError:
        await send_offline_message()
    else:
        await UserInteraction.send_error_embed(err_channel, action, "Error processing request!")


async def get_sd_models_cached(refresh = False):
    global sd_models

    if sd_models == None or refresh:
        sd_models = await WebuiRequests.get_sd_models(webui_url)

    return sd_models

def get_files(source) -> set:
    """
    List all files in directory
    """
    files = set()
    for file in os.listdir(source):
        fullpath = os.path.join(source, file)
        if os.path.isfile(fullpath):
            files.add(file)
    return files

async def send_generated_file (path:str, channel:interactions.Channel|None):
    """
    Send file by name to chanel
    """
    if channel == None: return

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
        aspect = round(int(width) / int(height), 4)
    else:
        seed = 'unknown'
        sampler = 'unknown'
        steps = 'unknown'
        cfg_scale = 'unknown'
        modelhash = 'unknown'
        width = 'unknown'
        height = 'unknown'
        aspect = 'unknown'
    
    try:
        model_name = await WebuiRequests.find_model_by_hash(webui_url, modelhash)
    except Exception as e:
        pass

    await UserInteraction.send_image(channel, path, 
                                f'Model: `{model_name}`\nHash `{modelhash}`, Sampler: `{sampler}`\n'
                                f'Steps: `{steps}`, CFG: `{cfg_scale}`, Seed: `{seed}`\n'
                                f'Resolution: `{width}x{height} [AR: {aspect}]`')

async def channel_poster(channel:interactions.Channel, files:set, directory:str):
    """
    Check all files in directory and send all files that not in `files` set to channel
    """
    current_files = get_files(directory)
    diffs = current_files - files
    
    if (len(diffs) == 0): return

    if enable_img_announce == 1:
        await UserInteraction.send_found_messages(channel, len(diffs))
        time.sleep(announce_interval)

    for file_base_name in diffs: #os.path
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

async def check_state_change(last:bool, new:bool):
    global err_channel
    if last == new : return
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

    post_files = get_files(post_directory)
    best_files = get_files(best_directory)
    crsd_files = get_files(crsd_directory)

    # assign envvars and start bot
    POST_CHANNEL_ID = int(os.environ['POST_CHANNEL_ID'])
    BEST_CHANNEL_ID = int(os.environ['BEST_CHANNEL_ID'])
    CRSD_CHANNEL_ID = int(os.environ['CRSD_CHANNEL_ID'])
    ERR_CHANNEL_ID = int(os.environ['ERR_CHANNEL_ID'])

    bot.start()
