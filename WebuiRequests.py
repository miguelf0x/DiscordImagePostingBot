import requests
import os
import base64
import io
from PIL import Image, PngImagePlugin


def get_progress(ctx, webui_url):
    prog = requests.get(url=f'{webui_url}/sdapi/v1/progress')

    job_progress = prog.json().get("progress")
    job_eta = prog.json().get("eta_relative")
    job_state = prog.json().get("state")

    await ctx.send(f'Progress: {round(job_progress*100, 2)}%\n'
                   f'Job ETA: {round(job_eta)}s\n'
                   f''
                   f'Step: {job_state["sampling_step"]} of {job_state["sampling_steps"]}\n')


def generate(prompt, webui_url, post_directory):
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
        response2 = requests.post(url=f'{webui_url}/sdapi/v1/png-info', json=png_payload)

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

        post_directory_img = os.path.join(post_directory, f'{seed}-{sampler}-{steps}-{model_hash}.png')
        image.save(post_directory_img, pnginfo=pnginfo)
