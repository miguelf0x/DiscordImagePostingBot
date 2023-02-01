import asyncio
import os
import threading
import interactions
import time
HELP_TEXT = {
    "default": "`/gen` - picture generation\n"
               "`/state` - show current task ETA, step and completion %\n"
               "`/help` - show this help message\n"
               "`/refresh` - refresh models in WebUI folder\n"
               "`/models` - list all models in WebUI folder\n"
               "`/find` - find model by hash\n"
               "`/select` - set model by index or hash",

    "generate": "$g `steps`, `width`, `height`, `tag_1`, `tag_2`, `tag_n`\n"
                "$g `steps`, `tag_1`, `tag_2`, `tag_n`\n"
                "$g `tag_1`, `tag_2`, `tag_n`",
    
    "batch": "$b `count`, `steps`, `width`, `height`, `tag_1`, `tag_2`, `tag_n`\n"
             "$b `count`, `steps`, `tag_1`, `tag_2`, `tag_n`\n"
             "$b `count`, `tag_1`, `tag_2`, `tag_n`",

    "find_ckpt": "$find `hash`",

    "set_ckpt": "$set `hash`\n"
                "$set `index`"

}


EMBED = interactions.Embed(
        title='Title',
        description='Description',
    )

sleep_timer = 1
sleep_lock = threading.Lock()

async def __waitable(func):
    await asyncio.sleep(sleep_timer)
    return await func()

async def send_custom_embed(ctx, title, description, embed_type):
    match embed_type:
        case "INFO":
            color = interactions.Color.blurple()
        case "WARN":
            color = interactions.Color.yellow()
        case "CRIT":
            color = interactions.Color.red()
        case "GOOD":
            color = interactions.Color.green()
        case "MESG":
            color = interactions.Color.black()
        case _:
            color = interactions.Color.fuchsia()

    embedding = interactions.Embed(
        title=title,
        color=color,
        description=description
    )
    await __waitable(lambda: ctx.send(embeds=embedding))

async def send_error_embed(ctx, action, error):
    print(f"[ERROR]: While {action}\n{error}")
    await send_custom_embed(ctx, "Failed!", f"{action} failed: {error}", "CRIT")

async def send_success_embed(ctx, description):
    await send_custom_embed(ctx, "Success!", description, "GOOD")

async def send_working_embed(ctx, description):
    await send_custom_embed(ctx, "Working!", description, 0x12B211)

async def send_info_embed(ctx, title, description):
    await send_custom_embed(ctx, title, description, "INFO")


async def send_oops_embed(ctx, command):
    description = (f'Command argument is missing or wrong!\n'
                   f'Correct usage is:\n{HELP_TEXT[command]}')
    await send_custom_embed(ctx, "Oops!", description, "WARN")

async def send_help_embed(ctx):
    await send_custom_embed(ctx, "Available commands", HELP_TEXT["default"], "INFO")


async def send_found_messages(channel:interactions.Channel, count):
    await __waitable(lambda: channel.send(f'Found {count} new picture(s). I will post them soon!'))

async def send_image(channel:interactions.Channel,  file:str, description:str):
    embedding = interactions.Embed()
    embedding.title = 'Generated image'
   
    embedding.description = (description)
    image = interactions.File(file)
    # b1 = interactions.Button(label="ouu my", style=interactions.ButtonStyle.DANGER, custom_id="2")
    # b2 = interactions.Button(label="no, dude", style=interactions.ButtonStyle.PRIMARY, custom_id="234")

    # row = interactions.ActionRow.new(b1, b2)
    
    embedding.set_image(url=f"attachment://{os.path.basename(file)}")

    await __waitable(lambda: channel.send(files=image,  embeds=embedding))