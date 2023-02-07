import PromptTemplate


def check_sampler_validity(sampler: str):

    if sampler in PromptTemplate.SAMPLERS:
        return sampler
    else:
        return "Euler"


def get_prompt(batch_count: int, steps: int, width: int, height: int, tags: str, neg_tags: str, sampler: str,
               cfg_scale: float):
    prompt = dict(PromptTemplate.PROMPT_TEMPLATE)

    if batch_count != 0:
        prompt["batch_size"] = str(batch_count)
    if steps != 0:
        prompt["steps"] = str(steps)
    if width != 0:
        prompt["width"] = str(width)
    if height != 0:
        prompt["height"] = str(height)

    neg_tags = neg_tags.lower()
    match neg_tags:
        case "mega":
            prompt["negative_prompt"] = PromptTemplate.MEGA_NEGATIVE_PROMPT_CONCAT
        case "megaflat":
            prompt["negative_prompt"] = PromptTemplate.MEGAFLAT_NEGATIVE_PROMPT_CONCAT
        case "long":
            prompt["negative_prompt"] = PromptTemplate.LONG_NEGATIVE_PROMPT_CONCAT
        case "short":
            prompt["negative_prompt"] = PromptTemplate.TRIM_NEGATIVE_PROMPT_CONCAT
        case _:
            prompt["negative_prompt"] = neg_tags

    prompt["prompt"] = str(tags)
    prompt["sampler_name"] = check_sampler_validity(sampler)
    prompt["cfg_scale"] = round(float(cfg_scale), 1)

    return prompt
