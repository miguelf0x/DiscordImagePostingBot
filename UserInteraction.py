import discord

HELP_TEXT = "`$g`, `$gen`, `$generate` - text to image picture generation\n" \
            "`$prog`, `$state`, `$progress` - show current task ETA, step and completion %\n" \
            "`$h`, `$help`, `$commands` - show this help message\n" \
            "`$refresh_ckpt`, `$ref`, `$refresh` - refresh checkoints in WebUI folder\n" \
            "`$show_ckpt`, `$models`, `$list_models` - list all checkpoints in WebUI folder\n" \
            "`$find_ckpt`, `$find`, `$find_model` - find checkpoint by hash\n" \
            "`$set_ckpt`, `$set`, `$set_model` - set checkpoint by index or hash"


EMBED = discord.Embed(
        title='Title',
        description='Description',
    )


def main_help_embed():
    embedding = discord.Embed(
        title='Available commands',
        description=HELP_TEXT,
    )
    return embedding
