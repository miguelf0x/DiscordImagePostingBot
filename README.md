# Discord Image Posting Bot

<a href="https://codeclimate.com/github/miguelf0x/DiscordImagePostingBot/maintainability"><img src="https://api.codeclimate.com/v1/badges/1351c9d4bc079e3137e0/maintainability" /></a>

This tiny bot is designed for posting newly added images in specified directory

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DISCORD_API_TOKEN`
`POST_CHANNEL_ID`
`BEST_CHANNEL_ID`
`CRSD_CHANNEL_ID`
`ERR_CHANNEL_ID`
`GUILD_ID`
`APPLICATION_ID`

## Configuration

Configuration files (config.yaml, default-config.yaml) are located in config directory. 
Currently available settings are:
* `announce_interval` sets interval between "n new images found" announce and first post
* `send_interval` sets interval between posts
* `check_interval` sets interval between directory changes checking
* `post_directory` sets directory for generated images
* `best_directory` sets directory for best images
* `crsd_directory` sets directory for cursed images
* `webui_url` sets URL for webUI
* `enable_image_announce` enables message "x new images found"

## Commands

Currently available commands are:

* `/gen (tags) [steps] [width] [height] [batch_count]` - generate image(s) using txt2img by tags
* `/state` - show current task ETA, step and completion
* `/help` - show help message
* `/refresh` - refresh models list
* `/models` - show available models
* `/find (hash)` - find model by hash
* `/select (model)` - set model by index in `/models` output or by hash

## Authors

- [@miguelf0x](https://www.github.com/miguelf0x)
