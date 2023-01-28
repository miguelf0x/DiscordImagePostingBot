import SafeTypes
import WebuiRequests
import PromptTemplate
import threading


def single_gen(ctx, arg, webui_url, post_directory):

    if arg != "":

        prompt = dict(PromptTemplate.PROMPT_TEMPLATE)
        trimmed = arg.split(",", 3)

        steps = SafeTypes.safe_cast(trimmed[0], "int")
        width = SafeTypes.safe_cast(trimmed[1], "int")
        height = SafeTypes.safe_cast(trimmed[2], "int")

        if steps > 0 and width > 0 and height > 0:
            prompt["steps"] = str(steps)
            prompt["width"] = str(width)
            prompt["height"] = str(height)
            prompt["prompt"] = str(trimmed[3])
        elif steps > 0:
            prompt["prompt"] = str(trimmed[1]) + str(trimmed[2]) + str(trimmed[3])
            prompt["steps"] = str(steps)
        else:
            prompt["steps"] = arg

        gen_thread = threading.Thread(target=WebuiRequests.post_generate,
                                      args=(ctx, prompt, webui_url, post_directory))
        gen_thread.start()

    else:
        return -255


def multiple_gen(ctx, arg, webui_url, post_directory):

    if arg != "":

        trimmed_arg = arg.split(",", 1)

        count = SafeTypes.safe_cast(trimmed_arg[0], "int")
        tags = SafeTypes.safe_cast(trimmed_arg[1], "str")

        for i in range(0, count):

            if tags != "":

                prompt = dict(PromptTemplate.PROMPT_TEMPLATE)
                trimmed = tags.split(",", 3)

                steps = SafeTypes.safe_cast(trimmed[0], "int")
                width = SafeTypes.safe_cast(trimmed[1], "int")
                height = SafeTypes.safe_cast(trimmed[2], "int")

                if steps > 0 and width > 0 and height > 0:
                    prompt["steps"] = str(steps)
                    prompt["width"] = str(width)
                    prompt["height"] = str(height)
                    prompt["prompt"] = str(trimmed[3])
                elif steps > 0:
                    prompt["prompt"] = str(trimmed[1]) + str(trimmed[2]) + str(trimmed[3])
                    prompt["steps"] = str(steps)
                else:
                    prompt["steps"] = arg

                gen_thread = threading.Thread(target=WebuiRequests.post_generate,
                                              args=(ctx, prompt, webui_url, post_directory))
                gen_thread.start()

            else:
                return -255

    else:
        return -255
