import PromptTemplate


def check_sampler_validity(sampler: str):

    if sampler in PromptTemplate.SAMPLERS:
        return sampler
    else:
        return "Euler"


def get_prompt(batch_count: int, steps: int, width: int, height: int, tags: str, sampler: str):
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
    prompt["sampler_name"] = check_sampler_validity(sampler)

    return prompt
