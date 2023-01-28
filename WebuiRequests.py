import requests
import os
import base64
import io
from PIL import Image, PngImagePlugin

import UserInteraction


async def get_progress(ctx, webui_url):
    prog = requests.get(url=f'{webui_url}/sdapi/v1/progress')

    job_progress = prog.json().get("progress")
    job_eta = prog.json().get("eta_relative")
    job_state = prog.json().get("state")

    embedding = UserInteraction.EMBED
    embedding.title = 'Current task state'
    embedding.description = (f'Progress: `{round(job_progress*100, 2)}%`\n'
                             f'Job ETA: `{round(job_eta)}s`\n'
                             f'Step: `{job_state["sampling_step"]} of '
                             f'{job_state["sampling_steps"]}`')
    await ctx.send(embed=embedding)


def post_generate(prompt, webui_url, post_directory):
    response = requests.post(url=f'{webui_url}/sdapi/v1/txt2img', json=prompt)

    if response.status_code > 400:
        print("git gud")
        print(response.text)
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
    response = requests.post(url=f'{webui_url}/sdapi/v1/refresh-checkpoints')
    embedding = UserInteraction.EMBED
    if response.status_code > 400:
        print("git gud")
        print(response.text)
        embedding.title = 'Failed!'
        embedding.description = f'Refresh failed with: {response.text}.'
        await ctx.send(embed=embedding)
        return 228
    else:
        embedding.title = 'Success!'
        embedding.description = 'Checkpoints list refreshed'
        await ctx.send(embed=embedding)


async def get_sd_models(ctx, webui_url, show_list):
    models = requests.get(url=f'{webui_url}/sdapi/v1/sd-models')
    models = models.json()
    embedding = UserInteraction.EMBED
    if show_list == "1":
        embedding.title = 'Available models list'
        models_msg = ""
        counter = 0
        print(models)
        for i in models:
            counter += 1
            models_msg += f"[{counter}] Checkpoint: `{i['model_name']}`, " \
                          f"Hash: `{i['hash']}`\n"
        embedding.description = f"Found {counter} models:\n" + models_msg
        await ctx.send(embed=embedding)
    return models


async def find_model_by_hash(ctx, webui_url, modelhash):
    models = requests.get(url=f'{webui_url}/sdapi/v1/sd-models')
    models = models.json()
    embedding = UserInteraction.EMBED
    for i in models:
        if modelhash == i["hash"]:
            embedding.title = 'Success!'
            embedding.description = f'Found model `{i["model_name"]}` ' \
                                    f'with hash `{i["hash"]}`'
            await ctx.send(embed=embedding)
            return

    embedding.title = 'Failed!'
    embedding.description = f'No checkpoints found with hash {modelhash}.'
    await ctx.send(embed=embedding)


# TODO: NEED CACHING RESPONSE AFTER get_sd_models()
async def select_model_by_arg(ctx, webui_url, argument):
    resp = await get_sd_models(ctx, webui_url, 0)
    option_payload = {}
    model_title = ""
    embedding = UserInteraction.EMBED
    if len(argument) > 2:
        for i in resp:
            if i["hash"] == argument:
                model_title = i["title"]
                option_payload = {"sd_model_checkpoint": model_title}
    else:
        model_title = resp[int(argument)-1]["title"]
        option_payload = {"sd_model_checkpoint": model_title}

    post_result = requests.post(url=f'{webui_url}/sdapi/v1/options',
                                json=option_payload)
    if post_result.status_code > 400:
        print("git gud")
        print(post_result.text)
        embedding.title = 'Failed!'
        embedding.description = f'Selecting model failed with: ' \
                                f'{post_result.text}.'
        await ctx.send(embed=embedding)
        return 228
    else:
        embedding.title = 'Success!'
        embedding.description = f'Model `{model_title}` has been selected.'
        await ctx.send(embed=embedding)
