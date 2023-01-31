import threading

import PromptTemplate
import SafeTypes
import UserInteraction
import WebuiRequests


def image_gen(ctx, webui_url, post_directory, batch_count, steps, width, height, tags):

    prompt = dict(PromptTemplate.PROMPT_TEMPLATE)

    if batch_count != 0:
        prompt["batch_size"] = str(batch_count)
    if steps != 0:
        prompt["steps"] = str(steps)
    if width != 0:
        prompt["width"] = str(width)
    if height != 0:
        prompt["height"] = str(height)

    prompt["prompt"] = str(tags)

    gen_thread = threading.Thread(target=WebuiRequests.post_generate,
                                  args=(ctx, prompt, webui_url, post_directory))
    gen_thread.start()
