import base64
import io
import os
import typing

import requests_async as requests
from PIL import Image, PngImagePlugin


class ServerError (Exception): 
    __slots__ = ("code", "text")

    def __init__(self, code:int, text:str) -> None:
        super().__init__()
        self.code = code
        self.text = text

    def __str__(self) -> str:
        return f"Error: webui http code {self.code}, {self.text}"

async def  __decorated_requests(req_lambda):
    try:
        res = await req_lambda()
    except Exception as e:
        if e is requests.exceptions.ConnectionError:
            raise ServerError(-1, "Webui is down")
        raise e

    if res.status_code >= 400:
        raise ServerError(res.status_code, f"Webiu reported an error: {res.text}")
    
    return res

async def user_interrupt(webui_url):
    await __decorated_requests(lambda : requests.post(url=f'{webui_url}/sdapi/v1/interrupt'))

async def get_check_online(webui_url):
    try:
        await __decorated_requests(lambda: requests.head(url=f'{webui_url}/'))
    except Exception as e:
        return False
    return True

async def get_progress(webui_url):
    prog = await __decorated_requests(lambda : requests.get(url=f'{webui_url}/sdapi/v1/progress'))
    prog = prog.json()

    job_progress = prog.get("progress")
    job_eta = prog.get("eta_relative")
    job_state = prog.get("state")

    description = (f'Progress: `{round(job_progress*100, 2)}%`\n'
                   f'Job ETA: `{round(job_eta)}s`\n'
                   f'Step: `{job_state["sampling_step"]} of '
                   f'{job_state["sampling_steps"]}`')
    
    return description


async def post_generate(prompt, webui_url, post_directory):
    response = await __decorated_requests(lambda : requests.post(url=f'{webui_url}/sdapi/v1/txt2img', json=prompt))
    files = []
    r = response.json()

    os.makedirs(post_directory, exist_ok=True)

    for index, item in enumerate(r['images']):
        image = Image.open(io.BytesIO(base64.b64decode(item.split(",", 1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + item
        }

        response2 = await __decorated_requests(lambda :  requests.post(url=f'{webui_url}/sdapi/v1/png-info',
                                  json=png_payload))

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
        cfg_scale = result["CFGscale"]
        model_hash = result["Modelhash"]
        res = str(result["Size"]).split("x")

        post_directory_img = os.path.join(post_directory,
                                          f'{seed}-{sampler}-{steps}-{cfg_scale}-{model_hash}-{res[0]}-{res[1]}.png')
        image.save(post_directory_img, pnginfo=pnginfo)
        files.append(post_directory_img)
    return files


async def post_refresh_ckpt( webui_url):
    await __decorated_requests(lambda: requests.post(url=f'{webui_url}/sdapi/v1/refresh-checkpoints'))


    # if response.status_code > 400:
    #     await UserInteraction.send_error_embed(ctx, "Checkpoints refreshing", response.text)
    #     return 228
    # else:
    #     await UserInteraction.send_success_embed(ctx, 'Checkpoints list refreshed')


async def get_sd_models(webui_url):
    models =  await __decorated_requests(lambda: requests.get(url=f'{webui_url}/sdapi/v1/sd-models'))
    models = models.json()
        # count = 0
        # for count, value in enumerate(models):
        #     models_msg += f"[{count+1}] Checkpoint: `{value['model_name']}`, " \
        #                   f"Hash: `{value['hash']}`\n"
        # models_msg = f"Found {count+1} models:\n" + models_msg
        # await UserInteraction.__send_custom_embed(ctx, 'Available models list', models_msg, "MESG")
    return models


async def find_model_by_hash(webui_url, modelhash) -> typing.Union[str, None]:
    models = await __decorated_requests(lambda: requests.get(url=f'{webui_url}/sdapi/v1/sd-models'))
    models = models.json()
    
    for value in models:
        if modelhash == value["hash"]:
            return value["model_name"]

    return None


# TODO: NEED CACHING RESPONSE AFTER get_sd_models()
async def select_model_by_arg(webui_url, argument):
    resp = await get_sd_models(webui_url)

    option_payload = {}
    model_title = ""

    if len(argument) > 2:
        for value in resp:
            if value["hash"] == argument:
                model_title = value["title"]
                option_payload = {"sd_model_checkpoint": model_title}
    else:
        model_title = resp[int(argument)-1]["title"]
        option_payload = {"sd_model_checkpoint": model_title}
    
    await __decorated_requests(lambda: requests.post(url=f'{webui_url}/sdapi/v1/options', json=option_payload))


async def select_model_by_hash(webui_url, model_title):
    option_payload = {"sd_model_checkpoint": model_title}
    await __decorated_requests(lambda: requests.post(url=f'{webui_url}/sdapi/v1/options', json=option_payload))
    # try:
    #     await UserInteraction.send_success_embed(ctx, f'Checkpoint `{model_title}` will be set')
    #     post_result = requests.post(url=f'{webui_url}/sdapi/v1/options',
    #                                 json=option_payload)
    # except Exception as e:
    #     await UserInteraction.send_error_embed(ctx, "Sending options POST request", e)
    #     return

    # if post_result.status_code > 400:
    #     await UserInteraction.send_error_embed(ctx, 'Selecting model', post_result.text)
    #     return 228
    # else:
    #     await UserInteraction.send_success_embed(ctx, f'Checkpoint `{model_title}` is now in use')
