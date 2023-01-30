LONG_NEGATIVE_PROMPT_4X = "((((ugly)))), "
LONG_NEGATIVE_PROMPT_3X = "(((duplicate))), (((mutation))), (((deformed))), (((bad proportions))), (((disfigured))), " \
                          "(((extra arms))), (((extra legs))), (((long neck))), (((worst quality))), "
LONG_NEGATIVE_PROMPT_2X = "((morbid)), ((mutilated)), ((poorly drawn hands)), ((bad anatomy)), ((extra limbs)), " \
                          "((out of frame)), ((missing arms)), ((missing legs)), "
LONG_NEGATIVE_PROMPT_1X = "(malformed limbs), (fused fingers), (too many fingers), (watermark), "
LONG_NEGATIVE_PROMPT_0X = "extra fingers, mutated hands, blurry, cloned face, gross proportions, jpeg artifacts, " \
                          "signature, username"

LONG_NEGATIVE_PROMPT_CONCAT = LONG_NEGATIVE_PROMPT_4X + LONG_NEGATIVE_PROMPT_3X + LONG_NEGATIVE_PROMPT_2X + \
                              LONG_NEGATIVE_PROMPT_1X + LONG_NEGATIVE_PROMPT_0X

TRIM_NEGATIVE_PROMPT_4X = "((((ugly)))), ((((gross)))), "
TRIM_NEGATIVE_PROMPT_3X = "(((mutation))), (((deformed))), (((bad proportions))), (((disfigured))), " \
                          "(((extra arms))), (((extra legs))),"
TRIM_NEGATIVE_PROMPT_2X = "((morbid)), ((mutilated)), ((poorly drawn hands)), ((bad anatomy)), ((extra limbs)), " \
                          "((out of frame)), ((missing arms)), ((missing legs)),"
TRIM_NEGATIVE_PROMPT_1X = "(malformed), (fused fingers), (too many fingers), (watermark),"
TRIM_NEGATIVE_PROMPT_0X = "extra fingers, blurry, cloned face, artifacts, signature, username"

TRIM_NEGATIVE_PROMPT_CONCAT = TRIM_NEGATIVE_PROMPT_4X + TRIM_NEGATIVE_PROMPT_3X + TRIM_NEGATIVE_PROMPT_2X + \
                              TRIM_NEGATIVE_PROMPT_1X + TRIM_NEGATIVE_PROMPT_0X

PROMPT_TEMPLATE = {
    "prompt": "1girl, standing, blue_hair",
    "negative_prompt": TRIM_NEGATIVE_PROMPT_CONCAT,
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
