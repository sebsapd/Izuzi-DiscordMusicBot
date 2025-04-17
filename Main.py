import discord
from discord.ext import commands
import yt_dlp
import os
import DCtoken
import sys
import shutil
import asyncio

# Defining the bot class for servers
class ServerBot:
    def __init__(self, id, queue = None, audio_title = None, queue_index = 0, voice_client = None):
        if queue is None: queue = []
        if audio_title is None: audio_title = []

        self.id = id
        self.queue = queue
        self.audio_title = audio_title
        self.queue_index = queue_index
        self.voice_client = voice_client
        self.loop_mode = "none"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = '.u ', intents = intents)

servers_path = "servers"
server_bots = {}

# If a servers folder exists, delete it and recreate it (to clear previously downloaded files)
if os.path.isdir(servers_path): shutil.rmtree(servers_path)
os.makedirs(servers_path, exist_ok = True)

# Creating a path for the folder named after the server ID
def id_path(ctx: commands.Context):
    id = str(ctx.guild.id)
    path = os.path.join("servers", id)
    return str(path)

# Function that retrieves the values of "queue" and "queue_index" for the current server
def queue_and_index(ctx):
    queue = server_bots[ctx.guild.id].queue
    queue_index = server_bots[ctx.guild.id].queue_index
    return queue, queue_index

# Downloading an audio file and its title using yt-dlp
async def download_audio(ctx, url):
    queue, _ = queue_and_index(ctx)
    
    file_name = f"{len(queue)}.mp3" if queue is not None else "0.mp3"
    output_path = os.path.join(id_path(ctx), file_name)

    ydl_opts = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": output_path,
        "quiet": True,
    }

    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info.get("title", "Nieznany utwór")

    loop = asyncio.get_event_loop()
    audio_title = await loop.run_in_executor(None, _extract)
    
    return output_path, audio_title

# Function responsible for playing a track
def play_audio(ctx):
    queue, queue_index = queue_and_index(ctx)

    if not ctx.voice_client or not queue: return
    
    try:
        audio_title = server_bots[ctx.guild.id].audio_title[queue_index]
        ctx.voice_client.play(
            discord.FFmpegOpusAudio(queue[queue_index]),
            after = lambda e: ctx.bot.loop.create_task(play_again_if_not_none(ctx, audio_title)))
        ctx.bot.loop.create_task(send_title(ctx, audio_title))
    except:
        print("End of queue")

# Function responsible for playing the next track in the queue if it's not empty
async def play_again_if_not_none(ctx, audio_title):
    queue, _ = queue_and_index(ctx)
    server_bot = server_bots[ctx.guild.id]

    if not queue:
        return
    
    # Enabling loop for a single track
    if server_bot.loop_mode == "one":
        play_audio(ctx)
    
    # Enabling loop for all tracks
    elif server_bot.loop_mode == "all":
        if server_bot.queue_index + 1 >= len(queue):
            server_bot.queue_index = 0
        else:
            server_bot.queue_index += 1
        play_audio(ctx)

    # Disabling loop.
    elif server_bot.loop_mode == "none":
        if server_bot.queue_index + 1 < len(queue):
            server_bot.queue_index += 1
            play_audio(ctx)
        else:
            return

# Creating a bot based on the class, dedicated to the current server
async def create_voice_channel_bot(ctx):
    voice_client = await ctx.message.author.voice.channel.connect()
    server_bots[ctx.guild.id] = server_bot = ServerBot(ctx.guild.id, None, None, 0, voice_client)
    os.makedirs(id_path(ctx), exist_ok=True) # Creating a folder for the current server's queue

async def send_title(ctx, audio_title):
    await ctx.send(f"🎵 Playing: **{audio_title}**")

# Command responsible for playing the track
@bot.command()
async def play (ctx, url):

    if not ctx.author.voice:
        await ctx.send("⚠️ You must be in a voice channel!")
        return

    # If there is an author on the channel and no bot is present, the bot joins the channel
    if ctx.message.author.voice.channel and not ctx.voice_client:
        if ctx.guild.id not in server_bots: # Checking if the server bot instance exists
            await create_voice_channel_bot(ctx)

    # If the bot is on a different channel than the author, move it to the same one
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    # Download the audio and song title, and save them to the lists
    ready_audio, audio_title = await download_audio(ctx, url)
    server_bots[ctx.guild.id].audio_title.append(audio_title)
    server_bots[ctx.guild.id].queue.append(ready_audio)

    if not ctx.voice_client.is_playing(): play_audio(ctx)        

# Command responsible for skipping tracks forward and backward
@bot.command()
async def skip (ctx, skip_number = "1"):
    if ctx.guild.id in server_bots:
        queue, queue_index = queue_and_index(ctx)
        queue_index += 1 

        try:
            skip_number = int(skip_number) # to check if the user has entered a number

        except ValueError:
            await ctx.send(":pray: You must give me a number!")
            return

        if not ctx.voice_client or not queue: await ctx.send("⚠️ The queue is empty!")
        
        if (queue_index + skip_number) < 0:
            server_bots[ctx.guild.id].queue_index = 0
            ctx.voice_client.stop()
            await ctx.send("⚠️ There aren't enough songs in the queue; switching to the first song!")

        elif (queue_index + skip_number) < len(queue):
            server_bots[ctx.guild.id].queue_index += (skip_number - 1)
            ctx.voice_client.stop()

            if skip_number == 1: await ctx.send(":track_next: Skipped 1 song!")
            else: await ctx.send(f":track_next: Skipped {skip_number} songs!")

        elif (queue_index + skip_number) == len(queue):
            ctx.voice_client.stop()
            await ctx.send(":track_next: Skipped 1 song!")

        elif (queue_index + skip_number) > len(queue):
            server_bots[ctx.guild.id].queue_index = len(queue)
            ctx.voice_client.stop()
            await ctx.send("⚠️ There aren't that many songs in the queue!")
    else: await ctx.send("⚠️ Izuzi is not connected to the voice channel!")

# Command responsible for clearing the queue and the folder storing the songs
@bot.command()
async def clear (ctx):
    if ctx.guild.id in server_bots:
        queue, _ = queue_and_index(ctx)

        # Clearing the queue
        if ctx.guild.id in server_bots and queue:
                server_bots[ctx.guild.id].queue.clear()
                server_bots[ctx.guild.id].audio_title.clear()
                server_bots[ctx.guild.id].queue_index = 0

                # Clearing the folder that stores the songs
                for file in os.listdir(servers_path):
                    item_path = os.path.join(servers_path, file)
                    if os.path.isfile(item_path): os.remove(item_path)

                ctx.voice_client.stop()
                await ctx.send("🗑️ The queue has been cleared!")
        else:
            await ctx.send("⚠️ The queue has been cleared!")
    else: await ctx.send("⚠️ Izuzi is not connected to the voice channel!")

@bot.command()
async def pause (ctx):
    if ctx.guild.id in server_bots:
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused!")
    else: await ctx.send("⚠️ Izuzi is not connected to the voice channel!")
 
@bot.command()
async def resume (ctx):
    if ctx.guild.id in server_bots:
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed!")
    else: await ctx.send("⚠️ Izuzi is not connected to the voice channel!")

# Command displaying the entire current queue
@bot.command()
async def queue (ctx):
    if ctx.guild.id in server_bots:
        if ctx.guild.queue:
            x = 1
            que_list = ""
            await ctx.send(":scroll: Queue:")
            for item in server_bots[ctx.guild.id].audio_title:
                que_list = que_list + str(x) + ". " + item + "\n"
                x += 1
            await ctx.send(que_list)
        else: await ctx.send("⚠️ There is no queue!")
    else: await ctx.send("⚠️ Izuzi is not connected to the voice channel!")

# Command that enables looping of songs
@bot.command()
async def loop (ctx, mode):
    if ctx.guild.id in server_bots:
        if mode not in ("none", "one", "all"):
            await ctx.send("⚠️ Use: none, one or all")
            return
        
        server_bots[ctx.guild.id].loop_mode = mode

        if mode == "one":  await ctx.send("🔁 looped one song.")
        elif mode == "all":  await ctx.send("🔁 looped all songs.")
        elif mode == "none": await ctx.send("🔁 Loop disabled.")

    else: await ctx.send("⚠️ Izuzi is not connected to the voice channel!")

# Command that should be used to shut down the bot
# It also deletes the server's folder storing the files.
@bot.command()
async def end (ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    await asyncio.sleep(1)

    await ctx.send("👋 Shutting down Izuzi...")

    if os.path.isdir(servers_path): shutil.rmtree(servers_path)
            
    await bot.close()
    sys.exit()

bot.run(DCtoken.token)