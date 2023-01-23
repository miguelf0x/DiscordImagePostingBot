# Tikhomirov Mikhail, 2023
# github.com/miguelf0x

import asyncio
import os
import discord
import yaml
import logging
import requests
import io
import base64
from PIL import Image, PngImagePlugin
from discord.ext import commands
from dotenv import load_dotenv


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

NEGATIVE_PROMPT_4X = "((((ugly)))), "
NEGATIVE_PROMPT_3X = "(((duplicate))), (((mutation))), (((deformed))), (((bad proportions))), (((disfigured))), " \
                     "(((extra arms))), (((extra legs))), (((long neck))), (((worst quality))), "
NEGATIVE_PROMPT_2X = "((morbid)), ((mutilated)), ((poorly drawn hands)), ((bad anatomy)), ((extra limbs)), " \
                     "((out of frame)), ((missing arms)), ((missing legs)), "
NEGATIVE_PROMPT_1X = "(malformed limbs), (fused fingers), (too many fingers), (watermark), "
NEGATIVE_PROMPT_0X = "extra fingers, mutated hands, blurry, cloned face, gross proportions, jpeg artifacts, " \
                     "signature, username"

FINAL_NEGATIVE_PROMPT = NEGATIVE_PROMPT_4X + NEGATIVE_PROMPT_3X + NEGATIVE_PROMPT_2X + NEGATIVE_PROMPT_1X + \
                        NEGATIVE_PROMPT_0X

PROMPT_TEMPLATE = {
        "prompt": "1girl, standing, blue_hair",
        "negative_prompt": FINAL_NEGATIVE_PROMPT,
        "steps": 40,
        "width": 512,
        "height": 512,
        "cfg_scale": 4,
        "sampler_name": "Euler",
        "seed": -1,
        "enable_hr": False,
        "hr_scale": 2,
        "denoising_strength": 0.7,
        "hr_upscaler": "Latent",
        "hr_second_pass_steps": 0,
        "hr_resize_x": 0,
        "hr_resize_y": 0,
        "batch_size": 1
    }


class TracedValue:
    def __init__(self, value):
        self.prev_value = None
        self.cur_value = value

    def set(self, value):
        if self.cur_value != value:
            self.prev_value = self.cur_value
            self.cur_value = value
            return 1
        else:
            return 0

    def get(self):
        return self.cur_value

    def get_diff(self):
        return self.cur_value - self.prev_value


@bot.command()
async def gen(ctx, *, arg):
    prompt = dict(PROMPT_TEMPLATE)
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

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))

        if prompt["seed"] == -1:
            seed = "R"
        else:
            seed = prompt["seed"]

        post_directory_img = os.path.join(post_directory, f'{index}-{seed}-{prompt["sampler_name"]}-'
                                                          f'{prompt["steps"]}.png')
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
    shit_channel = bot.get_channel(int(SHIT_CHANNEL_ID))
    post_files = TracedValue(get_files(post_directory))
    best_files = TracedValue(get_files(best_directory))
    shit_files = TracedValue(get_files(shit_directory))

    while True:
        await channel_poster(post_channel, post_files, post_directory)
        await channel_poster(best_channel, best_files, best_directory)
        await channel_poster(shit_channel, shit_files, shit_directory)


if __name__ == "__main__":

    # load .env
    load_dotenv()

    # create new config and load it
    post_directory = None
    while post_directory is None:
        try:
            with open('config.yaml') as f:
                try:
                    data = yaml.load(f, Loader=yaml.FullLoader)
                    announce_interval = data["announce_interval"]
                    check_interval = data["check_interval"]
                    send_interval = data["send_interval"]
                    post_directory = data["post_directory"]
                    best_directory = data["best_directory"]
                    shit_directory = data["shit_directory"]
                    webui_url = data["webui_url"]

                except yaml.YAMLError as exception:
                    print(exception)

        except FileNotFoundError as exception:
            print(exception)
            default_config = {'post_directory': 'Z:/Neural/RawPictures/islabot',
                              'best_directory': 'Z:/Neural/SortedPictures/Best',
                              'shit_directory': 'Z:/Neural/SortedPictures/Shit',
                              'check_interval': 20,
                              'send_interval': 10,
                              'announce_interval': 3,
                              'webui_url': 'http://127.0.0.1:7860'
            }
            with open('config.yaml', 'w') as f:
                data = yaml.dump(default_config, f)

    # assign envvars and start bot
    POST_CHANNEL_ID = os.environ['POST_CHANNEL_ID']
    BEST_CHANNEL_ID = os.environ['BEST_CHANNEL_ID']
    SHIT_CHANNEL_ID = os.environ['SHIT_CHANNEL_ID']
    bot.run(os.environ['DISCORD_API_KEY'])
