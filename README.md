
# Discord Image Posting Bot

This tiny bot is designed for posting newly added images in specified directory


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DISCORD_API_KEY`
`POST_CHANNEL_ID`
`BEST_CHANNEL_ID`
`CRSD_CHANNEL_ID`


## Configuration

Configuration file is located in project root (config.yaml). Currently available settings:
* `announce_interval` sets interval between new images announce and first post
* `send_interval` sets interval between posts
* `check_interval` sets interval between directory changes checking
* `post_directory` sets directory for generated images
* `best_directory` sets directory for best images
* `crsd_directory` sets directory for cursed images
* `webui_url` sets URL for webUI


## Authors

- [@miguelf0x](https://www.github.com/miguelf0x)

