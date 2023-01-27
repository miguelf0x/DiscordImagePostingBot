NEGATIVE_PROMPT_4X = "((((ugly)))), "
NEGATIVE_PROMPT_3X = "(((duplicate))), (((mutation))), (((deformed))), (((bad proportions))), (((disfigured))), " \
                     "(((extra arms))), (((extra legs))), (((long neck))), (((worst quality))), "
NEGATIVE_PROMPT_2X = "((morbid)), ((mutilated)), ((poorly drawn hands)), ((bad anatomy)), ((extra limbs)), " \
                     "((out of frame)), ((missing arms)), ((missing legs)), "
NEGATIVE_PROMPT_1X = "(malformed limbs), (fused fingers), (too many fingers), (watermark), "
NEGATIVE_PROMPT_0X = "extra fingers, mutated hands, blurry, cloned face, gross proportions, jpeg artifacts, " \
                     "signature, username"

NEGATIVE_PROMPT_CONCAT = NEGATIVE_PROMPT_4X + NEGATIVE_PROMPT_3X + NEGATIVE_PROMPT_2X + NEGATIVE_PROMPT_1X + \
                         NEGATIVE_PROMPT_0X

PROMPT_TEMPLATE = {
    "prompt": "1girl, standing, blue_hair",
    "negative_prompt": NEGATIVE_PROMPT_CONCAT,
    "steps": 60,
    "width": 512,
    "height": 512,
    "cfg_scale": 5,
    "sampler_name": "Euler",
    "seed": -1,
    "enable_hr": False,
    "hr_scale": 2,
    "denoising_strength": 0.7,
    "hr_upscaler": "Latent",
    "hr_second_pass_steps": 0,
    "hr_resize_x": 0,
    "hr_resize_y": 0,
    "batch_size": 1
}
