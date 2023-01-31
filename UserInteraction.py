import interactions


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


def main_help_embed():
    embedding = interactions.Embed(
        title='Available commands',
        description=HELP_TEXT["default"],
    )
    return embedding


async def send_error_embed(ctx, action, error):
    print(f"[ERROR]: While {action}\n{error}")
    embedding = interactions.Embed(
        title='Failed!',
        description=f"{action} failed: {error}"
    )
    await ctx.send(embeds=embedding)


async def send_success_embed(ctx, description):
    embedding = interactions.Embed(
        title='Success!',
        description=str(description)
    )
    await ctx.send(embeds=embedding)


async def send_oops_embed(ctx, command):
    embedding = interactions.Embed(
        title='Oops!',
        description=(f'Command argument is missing or wrong!\n'
                     f'Correct usage is:\n{HELP_TEXT[command]}')
    )
    await ctx.send(embeds=embedding)
