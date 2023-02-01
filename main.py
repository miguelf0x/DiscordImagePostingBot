# Tikhomirov Mikhail, 2023
# github.com/miguelf0x


import asyncio
import os
import threading
import time

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
post_channel = None
best_channel = None
crsd_channel = None
err_channel = None


async def __handle_webui_exception(e:Exception, ctx: interactions.CommandContext, action):
    if e is WebuiRequests.ServerError:
        await UserInteraction.send_error_embed(ctx, action, e)
    else:
        await UserInteraction.send_error_embed(ctx, action, "Error processing request!")
    print(e)


@bot.command()
async def help(ctx: interactions.CommandContext):
    """Show help message"""
    await UserInteraction.send_help_embed(ctx)

@bot.command()
async def state(ctx: interactions.CommandContext):
    """Check current task state"""
    try:
        description = await WebuiRequests.get_progress(webui_url)
        await UserInteraction.send_custom_embed(ctx, 'Current task state', description, "INFO")
    except Exception as e:
        await __handle_webui_exception(e, ctx, 'GET_STATUS')
    
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
async def gen(ctx: interactions.CommandContext, tags: str, image_count: int = 0, steps: int = 0,
              width: int = 0, height: int = 0):
    
    prompt = PromptParser.get_prompt(image_count, steps, width, height, tags)
    
    asyncio.create_task(ctx.send("Start generating!"))
    
    async def func():
        try:
            print(f"Generating {tags}")
            images = await WebuiRequests.post_generate(prompt=prompt, webui_url=webui_url, post_directory=post_directory)
            
            print(f"Generated")
            for img in images:
                await send_generated_file(img, post_channel)

            print(f"Sent")

        except Exception as e:
            await __handle_webui_exception(e, ctx, "GEN_IMG")
            
    print(f"Execute task")
    asyncio.create_task(func())
    print(f"End")


@bot.command()
async def test(ctx: interactions.CommandContext):
    """
    Generate test image [512x512, Steps=100, tags=1girl, blue hair, bobcut, portrait, blush] \n
    LETS BURN YOUR GPU UAAAAAARGH
    """
    prompt = PromptParser.get_prompt(1, 100, 512, 512, "1girl, blue hair, bobcut, portrait, blush")
    
    await ctx.send("Start generating!")

    async def generator():
        try:
            images = await WebuiRequests.post_generate(prompt=prompt, webui_url=webui_url, post_directory=post_directory)
            
            for img in images:
                await send_generated_file(img, post_channel)

        except Exception as e:
            await __handle_webui_exception(e, ctx, "Generating image")

    asyncio.create_task(generator())


@bot.command()
async def refresh(ctx: interactions.CommandContext):
    """Refresh models list"""
    try:
        WebuiRequests.post_refresh_ckpt(webui_url)
        await UserInteraction.send_success_embed(ctx, 'Checkpoints list refreshed')
    except Exception as e:
        await __handle_webui_exception(e, ctx, "Sending refresh-checkpoints POST request")


@bot.command()
async def models(ctx: interactions.CommandContext):
    """Show available models"""
    print(f"Models")
    try:
        models = await WebuiRequests.get_sd_models(webui_url)
        count = 0
        models_msg = ""
        for count, value in enumerate(models):
            models_msg += f"[{count+1}] Checkpoint: `{value['model_name']}`, " \
                      f"Hash: `{value['hash']}`\n"
        models_msg = f"Found {count+1} models:\n" + models_msg
        await UserInteraction.send_custom_embed(ctx, 'Available models list', models_msg, "MESG")
    except Exception as e:
        await __handle_webui_exception(e, ctx, "Checking avalibe models")
    


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
    try:
        name = await WebuiRequests.find_model_by_hash(webui_url, modelhash)
        if name:
            await UserInteraction.send_success_embed(ctx, f'Found model `{name}` '
                                                          f'with hash `{modelhash}`')
        else:        
            await UserInteraction.send_error_embed(ctx, f"Checkpoints search", f'No checkpoints '
                                                                               f'found with hash {modelhash}')

    except Exception as e:
        await __handle_webui_exception(e, ctx, "Selecting model")
    


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
    try:
        setting = WebuiRequests.find_model_by_hash(webui_url, model)
        WebuiRequests.select_model_by_hash(setting)
        await UserInteraction.send_success_embed(ctx, f'Checkpoint `{setting}` is now in use')
    except Exception as e:
        await __handle_webui_exception(e, ctx, 'Selecting model')


@bot.command()
async def skip(ctx: interactions.CommandContext):
    """Skip current task"""
    try:
        await WebuiRequests.user_interrupt(ctx, webui_url)
        await UserInteraction.send_success_embed(ctx, 'Image generating interrupted')
    except Exception as e:
        await __handle_webui_exception(e, ctx, "Interrupting request")


def get_files(source) -> set:
    files = set()
    for file in os.listdir(source):
        fullpath = os.path.join(source, file)
        if os.path.isfile(fullpath):
            files.add(file)
    return files

async def send_generated_file (path:str, channel:interactions.Channel):
    
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

async def send_offline_message(error_channel):
     await UserInteraction.send_custom_embed(error_channel,
                                                "WebUI is offline",
                                                f"Your prompts will NOT be executed",
                                                "CRIT")

async def send_online_message(error_channel):
    await UserInteraction.send_custom_embed(error_channel,
                                                    "WebUI is online",
                                                    "Now your prompts will be executed",
                                                    "GOOD")


async def check_state_change(error_channel:interactions.Channel, last:bool, new:bool):
    if last == new : return
    # if new : 
    #     await send_online_message(error_channel)
    # else: 
    #     await send_offline_message(error_channel)

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

    async def check_thread():
        state = False
        while True:
            await asyncio.sleep(check_interval)
            new_state = await WebuiRequests.get_check_online(webui_url)
            await check_state_change(err_channel, state, new_state)
            state = new_state
                
    asyncio.create_task(check_thread())

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
