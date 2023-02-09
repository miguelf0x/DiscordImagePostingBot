import asyncio
import os
import threading

import interactions

import main

COMMANDS = ["gen", "state", "refresh", "models", "find", "select", "help", "man"]

HELP_TEXT = (
    "`/gen` - picture generation\n"
    "`/state` - show current task ETA, step and completion %\n"
    "`/refresh` - refresh models in WebUI folder\n"
    "`/models` - list all models in WebUI folder\n"
    "`/find` - find model by hash\n"
    "`/select` - set model by index in /models or by hash"
    "`/help` - show this help message\n"
    "`/man [command]` - show command info"
)

HELP_COMMAND_USAGE = {

    "gen": "/gen (tags) [neg_tags] [width] [height] [sampler] [steps] [cfg_scale] [img_count]",
    "state": "/state",
    "refresh": "/refresh",
    "models": "/models",
    "find": "/find (hash)",
    "select": "/select (hash) or /select (index)",
    "help": "/help",
    "man": "/man (command)"

}

HELP_COMMAND_ARGS = {

    "gen": "(tags) - your prompt in plain language or booru tags separated by comma\n"
           "          Allowed input: text\n"
           "[neg_tags] - your negative prompt that is used for excluding unwanted generation results\n"
           "          Allowed input: text\n"
           "[width] - image width in pixels\n"
           "          Allowed input: integer in range 16 - 1536\n"
           "[height] - image height in pixels\n"
           "           Allowed input: integer in range 16 - 1536\n"
           "[sampler] - Stable Diffusion sampler. For more info refer to /tips command output\n"
           "            Allowed input: text, refer to /samplers command output\n"
           "[steps] - interference steps\n"
           "          Allowed input: integer in range 1 - 300\n"
           "[cfg_scale] - how strict is your prompt. Low value may lead to random color noise instead of image\n"
           "              Allowed input: float in range 1.0 - 20.0, step - 0.5\n"
           "[img_count] - count of image for parallel generation. Does seriously increase generating time\n"
           "              Allowed input: integer in range 1 - 8",

    "state": "None",
    "refresh": "None",
    "models": "None",

    "find": "(hash) - hash of searched model\n"
    "                 Allowed input: hash",
    
    "select": "(hash) - hash of required model\n"
              "         Allowed input: hash\n"
              "or\n"
              "(index) - index of required model in /models command output\n"
              "          Allowed input: integer in range of /models indexes",

    "help": "None",

    "man": "(command) - any command from /help output\n"
           "            Allowed input: text, refer to /help command output",

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


async def send_custom_embed(ctx, title, description, embed_type, ephemeral=False):
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

    await __waitable(lambda: ctx.send(embeds=embedding, ephemeral=ephemeral))


async def send_error_embed(ctx, action, error):
    print(f"[ERROR]: While {action}\n{error}")
    await send_custom_embed(ctx, "Failed!", f"{action} failed: {error}", "CRIT")


async def send_success_embed(ctx, description):
    await send_custom_embed(ctx, "Success!", description, "GOOD")


async def send_working_embed(ctx, description):
    await send_custom_embed(ctx, "Working!", description, 0x12B211)


async def send_info_embed(ctx, title, description):
    await send_custom_embed(ctx, title, description, "INFO")


async def send_help_embed(ctx):
    await send_custom_embed(ctx, "Available commands", HELP_TEXT, "INFO", True)


async def send_man_embed(ctx: interactions.CommandContext, command: str):

    embedding = interactions.Embed(
        title="Commands",
        color=0x5865F2,
    )

    if command in COMMANDS:
        embedding.add_field("Command name", command, inline=False)
        embedding.add_field("Usage", HELP_COMMAND_USAGE[command], inline=False)
        embedding.add_field("Arguments", HELP_COMMAND_ARGS[command], inline=False)

    else:
        embedding.add_field("Command not found", "For available commands list use /help", inline=False)

    await __waitable(lambda: ctx.send(embeds=embedding, ephemeral=True))


async def send_found_messages(channel: interactions.Channel, count):
    await __waitable(lambda: channel.send(f'Found {count} new picture(s). I will post them soon!'))


async def send_image(channel: interactions.Channel, file: str, description: str, resolution: str, model: str,
                     seed: str, gensettings: str, post_id: int, button_names: list):
    embedding = interactions.Embed()
    embedding.title = 'Generated image'

    embedding.description = description
    image = interactions.File(file)

    embedding.add_field("Post ID", f"#{post_id+1}", inline=True)
    embedding.add_field("Resolution", resolution, inline=True)
    embedding.add_field("Model", model, inline=True)
    embedding.add_field("Seed", seed, inline=False)
    embedding.add_field("Generation settings", gensettings, inline=False)

    embedding.set_footer("Likes: 0, Dislikes: 0, Purge: 0")

    best_button = interactions.Button(label=button_names[0], style=interactions.ButtonStyle.SUCCESS,
                                      custom_id="upvote")
    crsd_button = interactions.Button(label=button_names[1], style=interactions.ButtonStyle.SECONDARY,
                                      custom_id="downvote")
    rem_button = interactions.Button(label=button_names[2], style=interactions.ButtonStyle.DANGER,
                                     custom_id="remove")
    row = interactions.ActionRow.new(best_button, crsd_button, rem_button)

    embedding.set_image(url=f"attachment://{os.path.basename(file)}")

    await __waitable(lambda: channel.send(files=image, embeds=embedding, components=row))

    return 0
