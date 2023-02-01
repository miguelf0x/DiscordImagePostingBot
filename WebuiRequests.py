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
        if self.code == -1:
            return "Error: Not connected to webui"
        else: 
            return f"Error: webui http code {self.code}, {self.text}"

async def  __decorated_requests(req_lambda) -> requests.Response:
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

async def post_generate(prompt, webui_url, post_directory) -> list[str]:
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

async def get_sd_models(webui_url):
    models =  await __decorated_requests(lambda: requests.get(url=f'{webui_url}/sdapi/v1/sd-models'))
    models = models.json()
    return models

async def find_model_by_hash(webui_url, modelhash) -> typing.Union[str, None]:
    models = await __decorated_requests(lambda: requests.get(url=f'{webui_url}/sdapi/v1/sd-models'))
    models = models.json()
    
    for value in models:
        if modelhash == value["hash"]:
            return value["model_name"]

    return None

async def select_model(webui_url, model):
   option_payload = {"sd_model_checkpoint": model}
   await __decorated_requests(lambda: requests.post(url=f'{webui_url}/sdapi/v1/options', json=option_payload))

async def get_options(webui_url):
    req_data = await __decorated_requests(lambda: requests.get(url=f'{webui_url}/sdapi/v1/options'))
    js_data = req_data.json()
    return js_data
