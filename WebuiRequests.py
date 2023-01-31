import requests
import os
import base64
import io
from PIL import Image, PngImagePlugin

import UserInteraction


async def user_interrupt(ctx, webui_url):
    try:
        requests.post(url=f'{webui_url}/sdapi/v1/interrupt')
    except Exception as e:
        await UserInteraction.send_error_embed(ctx, "Sending interrupt POST request", e)
        return

    await UserInteraction.send_success_embed(ctx, 'Image generating interrupted')


async def get_progress(ctx, webui_url):
    try:
        prog = requests.get(url=f'{webui_url}/sdapi/v1/progress')
    except Exception as e:
        await UserInteraction.send_error_embed(ctx, "Sending progress GET request", e)
        return

    job_progress = prog.json().get("progress")
    job_eta = prog.json().get("eta_relative")
    job_state = prog.json().get("state")

    embedding = UserInteraction.EMBED
    embedding.title = 'Current task state'
    embedding.description = (f'Progress: `{round(job_progress*100, 2)}%`\n'
                             f'Job ETA: `{round(job_eta)}s`\n'
                             f'Step: `{job_state["sampling_step"]} of '
                             f'{job_state["sampling_steps"]}`')

    await ctx.send(embeds=embedding)


def post_generate(ctx, prompt, webui_url, post_directory):
    try:
        response = requests.post(url=f'{webui_url}/sdapi/v1/txt2img', json=prompt)
    except Exception as e:
        UserInteraction.send_error_embed(ctx, "Sending txt2img POST request", e)
        return

    if response.status_code > 400:
        UserInteraction.send_error_embed(ctx, "Generating image", response.text)
        return 228

    r = response.json()

    os.makedirs(post_directory, exist_ok=True)

    for index, item in enumerate(r['images']):
        image = Image.open(io.BytesIO(base64.b64decode(item.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + item
        }
        response2 = requests.post(url=f'{webui_url}/sdapi/v1/png-info',
                                  json=png_payload)

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

        post_directory_img = os.path.join(post_directory,
                                          f'{seed}-{sampler}-{steps}-{model_hash}.png')
        image.save(post_directory_img, pnginfo=pnginfo)


async def post_refresh_ckpt(ctx, webui_url):
    try:
        response = requests.post(url=f'{webui_url}/sdapi/v1/refresh-checkpoints')
    except Exception as e:
        await UserInteraction.send_error_embed(ctx, "Sending refresh-checkpoints POST request", e)
        return

    if response.status_code > 400:
        await UserInteraction.send_error_embed(ctx, "Checkpoints refreshing", response.text)
        return 228
    else:
        await UserInteraction.send_success_embed(ctx, 'Checkpoints list refreshed')


async def get_sd_models(ctx, webui_url, show_list):
    try:
        models = requests.get(url=f'{webui_url}/sdapi/v1/sd-models')
    except Exception as e:
        await UserInteraction.send_error_embed(ctx, "Sending sd-models GET request", e)
        return

    models = models.json()
    embedding = UserInteraction.EMBED
    if show_list == "1":
        embedding.title = 'Available models list'
        models_msg = ""
        count = 0
        for count, value in enumerate(models):
            models_msg += f"[{count+1}] Checkpoint: `{value['model_name']}`, " \
                          f"Hash: `{value['hash']}`\n"
        embedding.description = f"Found {count} models:\n" + models_msg
        await ctx.send(embeds=embedding)
    return models


async def find_model_by_hash(ctx, webui_url, modelhash):
    try:
        models = requests.get(url=f'{webui_url}/sdapi/v1/sd-models')
    except Exception as e:
        await UserInteraction.send_error_embed(ctx, "Sending sd-models GET request", e)
        return

    models = models.json()

    for count, value in enumerate(models):
        if modelhash == value["hash"]:
            await UserInteraction.send_success_embed(ctx, f'Found model `{value["model_name"]}` '
                                                          f'with hash `{value["hash"]}`')
            return

    await UserInteraction.send_error_embed(ctx, f"Checkpoints search", f'No checkpoints '
                                                                       f'found with hash {modelhash}')


# TODO: NEED CACHING RESPONSE AFTER get_sd_models()
async def select_model_by_arg(ctx, webui_url, argument):
    resp = await get_sd_models(ctx, webui_url, 0)
    option_payload = {}
    model_title = ""

    if len(argument) > 2:
        for count, value in enumerate(resp):
            if value["hash"] == argument:
                model_title = value["title"]
                option_payload = {"sd_model_checkpoint": model_title}
    else:
        model_title = resp[int(argument)-1]["title"]
        option_payload = {"sd_model_checkpoint": model_title}

    try:
        await UserInteraction.send_success_embed(ctx, f'Checkpoint `{model_title}` will be set')
        post_result = requests.post(url=f'{webui_url}/sdapi/v1/options',
                                    json=option_payload)
    except Exception as e:
        await UserInteraction.send_error_embed(ctx, "Sending options POST request", e)
        return

    if post_result.status_code > 400:
        await UserInteraction.send_error_embed(ctx, 'Selecting model', post_result.text)
        return 228
    else:
        await UserInteraction.send_success_embed(ctx, f'Checkpoint `{model_title}` is now in use')
