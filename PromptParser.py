import SafeTypes
import UserInteraction
import WebuiRequests
import PromptTemplate
import threading


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


async def mass_gen(ctx, arg, webui_url, post_directory):
    trimmed_arg = arg.split(",", 1)

    count = SafeTypes.safe_cast(trimmed_arg[0], "int")
    if count == -253:
        await UserInteraction.send_oops_embed(ctx, "batch")
        return

    tags = SafeTypes.safe_cast(trimmed_arg[1], "str")

    image_gen(ctx, tags, webui_url, post_directory, batch_size=count)
