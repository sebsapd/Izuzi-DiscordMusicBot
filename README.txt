# Izuzi Discord Music Bot

Izuzi is a Discord music bot that allows you to play, skip, pause, and loop tracks directly in your voice channel.
The bot uses yt-dlp to download audio files from YouTube and other streaming platforms.

## Features
- Play music directly from YouTube.
- Skip or pause tracks.
- Loop a single track or the entire queue.
- View the current song queue.
- Clear the queue and stored songs.
  
## Installation
1. Clone or download the repository:
    https://github.com/sebsapd/IzuziDiscordMusicBot

2. Install dependencies:
    You can open CMD in the IzuziDiscordMusicBot folder and then use the command:
    
    pip install -r requirements.txt

    Next, you need to download ffmpeg from the following link: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
    Then, go into the downloaded archive and from the 'bin' folder, move ffmpeg.exe, ffplay.exe and ffprobe.exe to the IzuziDiscordMusicBot folder.

3. Create a `DCtoken.py` file containing your Discord bot token:
    If you want to use this code on your Discord bot, you need to log in to your account on the Discord Developer site.
    Then, create an application, go to the "Bot" section, and you will find your token there.
    But remember, for security purposes, tokens can only be viewed once when created.
    The next step will be to paste your token into the DCtoken.py file.

## Commands:
- `.u play <url>`: Play a song from the given URL.
- `.u skip <number>`: Skip to the next track or skip a specific number of tracks.
- `.u pause`: Pause the current song.
- `.u resume`: Resume the current song.
- `.u queue`: Show the current song queue.
- `.u loop <mode>`: Loop a song or the entire queue. Modes: `none`, `one`, `all`.
- `.u clear`: Clear the queue and stored songs.
- `.u end`: Stop the bot and delete the server's stored files.

## Requirements
- Python 3.8 or later.
- `yt-dlp` for downloading audio from YouTube.
- `discord.py` for interacting with the Discord API.

## License
MIT License