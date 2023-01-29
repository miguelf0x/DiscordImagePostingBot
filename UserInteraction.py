import discord


HELP_TEXT = {
    "default": "`$g`, `$gen`, `$generate` - "
               "text to image picture generation\n"
               "`$prog`, `$state`, `$progress` - "
               "show current task ETA, step and completion %\n"
               "`$h`, `$help`, `$commands` - "
               "show this help message\n"
               "`$refresh_ckpt`, `$ref`, `$refresh` - "
               "refresh checkoints in WebUI folder\n"
               "`$show_ckpt`, `$models`, `$list_models` - "
               "list all checkpoints in WebUI folder\n"
               "`$find_ckpt`, `$find`, `$find_model` - "
               "find checkpoint by hash\n"
               "`$set_ckpt`, `$set`, `$set_model` - "
               "set checkpoint by index or hash",

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


EMBED = discord.Embed(
        title='Title',
        description='Description',
    )


def main_help_embed():
    embedding = discord.Embed(
        title='Available commands',
        description=HELP_TEXT["default"],
    )
    return embedding


async def send_error_embed(ctx, action, error):
    print(f"[ERROR]: While {action}\n{error}")
    embedding = discord.Embed(
        title='Failed!',
        description=f"{action} failed: {error}"
    )
    await ctx.send(embed=embedding)


async def send_success_embed(ctx, description):
    embedding = discord.Embed(
        title='Success!',
        description=str(description)
    )
    await ctx.send(embed=embedding)


async def send_oops_embed(ctx, command):
    embedding = discord.Embed(
        title='Oops!',
        description=(f'Command argument is missing or wrong!\n'
                     f'Correct usage is:\n{HELP_TEXT[command]}')
    )
    await ctx.send(embed=embedding)
