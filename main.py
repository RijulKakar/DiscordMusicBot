import os
import discord
from discord.ext import commands
import wavelink
from dotenv import load_dotenv

load_dotenv();
TOKEN = os.getenv('DISCORD_TOKEN')


# Instantiating discord client
client = commands.Bot(command_prefix = '!', intents = discord.Intents.all())


# CustomPlayer class that solves queue issues, extends the wavelink player class
class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()


# Setting up wavelink (connection between lavalink and discord)
@client.event
async def on_ready():
    client.loop.create_task(connect_nodes())

# Helper function for above
async def connect_nodes():
    await client.wait_until_ready()
    await wavelink.NodePool.create_node(
        bot = client,
        host = '0.0.0.0',
        port = 2333,
        password = 'youshallnotpass'
    )

# Checking if node is ready and setting up queue
@client.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node: <{node.identifier}> is ready! Poggers') # Prints node id

@client.event
async def on_wavelink_track_end(player: CustomPlayer, track: wavelink.Track, reason):
    if (not player.queue.is_empty): # Checks for empty queue
        next_track = player.queue.get() # Sets next track to next in q
        await player.play(next_track) # plays next track


# COMMANDS
# Join command: joins a voice channel
@client.command(aliases = ["connect", "j"], help = "Joins the user's current vc")
async def join(ctx):
    voice_client = ctx.voice_client
    try: # Trying to connect to vc
        channel = ctx.author.voice.channel
    except AttributeError: # Fails so lets user know
        return await ctx.send("Join a voice channel dumbo")

    if (not voice_client): # Joins a vc
        await ctx.send("Joining **{}**".format(channel))
        await ctx.author.voice.channel.connect(cls = CustomPlayer()) # Passes in custom player class so commands are useable
    else: # Doesn't join bc already in vc
        await ctx.send("Bot already in **{}** bruh".format(channel))

# Leave command: leavs a voice channel
@client.command(aliases = ["stop", "l", "disconnect"], help = "Stops the current track, and leaves the vc")
async def leave(ctx):
    voice_client = ctx.voice_client
    if (voice_client): # Leaves if connected
        await voice_client.disconnect()
    else: # Prints message if not connected
        await ctx.send("Not connected to vc my man... **{}** kinda dumb frfr no cap".format(ctx.author.name))

# Play command: plays a song or whatever
@client.command(aliases = ["p"], help = "Plays or queues a track depending on the input given")
async def play(ctx, *, search: wavelink.YouTubeTrack):
    # Join functionality
    voice_client = ctx.voice_client
    if (not voice_client): # If not in vc, basically just run the join command with custom player class passed in
        custom_player = CustomPlayer()
        voice_client: CustomPlayer = await ctx.author.voice.channel.connect(cls = custom_player)

    # Actual play/queue functionality here
    if (voice_client.is_playing()):
        voice_client.queue.put(item = search) # Queues item here, then send message saying it did that
        
        # Creating embed
        embed = discord.Embed(
            title = search.title,
            url = search.uri,
            # author = ctx.author,
            description = f"Queued {search.title} in {voice_client.channel}"
        )
        embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar))

        # Sending embeded message
        await ctx.send(embed = embed)

    else:
        await voice_client.play(search)

        # Creating embed
        embed = discord.Embed(
            title = voice_client.source.title,
            url = voice_client.source.uri,
            # author = ctx.author,
            description = f"Playing {voice_client.source.title} in {voice_client.channel}"
        )
        embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar))

        # Sending embeded message
        await ctx.send(embed = embed)

# Skip command: skips current song to next song in queue
@client.command(aliases = ["s"], help = "Skips the current track")
async def skip(ctx):
    voice_client = ctx.voice_client
    if (voice_client): # Checking if connected to vc
        if (not voice_client.is_playing()):
            return await ctx.send("Nothing playing ??? ")
        if (voice_client.queue.is_empty):
            return await voice_client.stop()

        await voice_client.seek(voice_client.track.length * 1000) # Seeks forward a lot, essentially skips the track
        if (voice_client.is_paused()):
            await voice_client.resume()
    
    else:
        await ctx.send("Bot isn't connected to a vc my person")

@client.command(aliases = ["pu"], help = "Pauses the current track")
async def pause(ctx):
    voice_client = ctx.voice_client
    if (voice_client):
        # Checks if something is playing and isn't paused already
        if (voice_client.is_playing() and not voice_client.is_paused()):
            await voice_client.pause()
            await ctx.send("Pausing track")
        else:
            await ctx.send("Nothing is playing... awkward...")

    else:
        await ctx.send("Bot isn't connected to vc, cmon now, you know better")

@client.command(aliases = ["r"], help = "Resumes the current track")
async def resume(ctx):
    voice_client = ctx.voice_client
    if (voice_client):
        if (voice_client.is_paused()):
            await voice_client.resume()
            await ctx.send("Resuming track")
        else:
            await ctx.send("Whatchu tryna resume, nothing is paused cuh")

    else:
        await ctx.send("Bot ain't connected to vc brother")

# Queue command: shows the current items in queue
@client.command(help = "Currently not working")
async def queue(ctx, player: CustomPlayer, track: wavelink.Track, reason):
    await ctx.send(player.queue) 


# Main error handler for play command
@play.error
async def play_error(ctx, error):
    if (isinstance(error, commands.BadArgument)):
        await ctx.send("Sorry dawg, couldn't find the track you were looking for")
    else:
        await ctx.send("Not connected to vc my man")




# Running the client
client.run(TOKEN)