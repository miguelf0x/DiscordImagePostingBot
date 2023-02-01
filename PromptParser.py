import PromptTemplate


def get_prompt(batch_count: int, steps: int, width: int, height: int, tags: str):
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
    return prompt
