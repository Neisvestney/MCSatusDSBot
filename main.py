import asyncio
import threading
import time
import os
from socket import gaierror, timeout

from discord import Message, NotFound, CategoryChannel, Colour
from mcstatus import MinecraftServer
import discord

import config

client = discord.Client()

# region UPDATE STATUS
WAIT_SECONDS = 5

servers = dict()


async def update_servers():
    servers.clear()
    for key in config.c['SERVERS']:
        servers[key] = {'obj': MinecraftServer.lookup(config.c['SERVERS'][key]), 'players': None, "online": None,
                        'message': await get_message(key)}

    print(f"Connected to {', '.join([servers[x]['obj'].host for x in servers])}")


async def get_message(mid):
    for guild in client.guilds:
        for channel in guild.text_channels:
            try:
                msg = await channel.fetch_message(mid)
            except NotFound:
                continue
            return msg


async def update_message(server, status=None):
    if server['online']:
        embed = discord.Embed(title=f"Стутус сервера {server['obj'].host}:{server['obj'].port}",
                              description=f"{status.description['text']} ({status.version.name})",
                              color=Colour(int('0c8043', 16)))
        embed.add_field(name="Онлайн", value=status.players.online)
        embed.add_field(name="Игроки", value=x if (x := ', '.join([status.players.sample[i].name for i in range(status.players.online)])) else 'Нет игроков')
    else:
        embed = discord.Embed(title=f"Стутус сервера {server['obj'].host}:{server['obj'].port}",
                              description='Сервер выключен', color=Colour(int('d50001', 16)))
        embed.add_field(name="Онлайн", value="0")

    await server['message'].edit(embed=embed, content='')


async def update_status():
    while True:
        for mid, server in servers.items():
            try:
                s = server['obj'].status()

                if not server['online']:
                    print(f"Server {server['obj'].host} online")
                    server['online'] = True
                    await update_message(server, s)

                if server['players'] is None or s.players.online != len(server['players']):
                    print(f"{s.version.name} ({s.description})")
                    print(f"Players: {[x.name for x in s.players.sample] if s.players.sample else 'None'}")
                    await update_message(server, s)
                if server['players'] is not None and s.players.online > len(server['players']):
                    print(f"New player {list(set([x.name for x in s.players.sample]) ^ (set(server['players'])))[0]}")

                server['players'] = [x.name for x in s.players.sample] if s.players.sample else []
            except (gaierror, ConnectionRefusedError, timeout, OSError):
                if server['online'] or server['online'] is None:
                    print(f"Server {server['obj'].host} offline")
                    await update_message(server)
                server['online'] = False
                server['players'] = []

        await asyncio.sleep(WAIT_SECONDS)


# region


# region BOT
print("Starting bot...")


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await update_servers()
    asyncio.create_task(update_status())


@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return

    if message.content.startswith('/mcstatus start'):
        args = message.content.split(' ')
        if len(args) == 3:
            m: Message = await message.channel.send('Starting lookup...')
            config.c['SERVERS'][str(m.id)] = args[2]
            config.save()
            await update_servers()
        else:
            await message.channel.send('Set server ip!')


client.run(config.c['SETTINGS']['DISCORD_TOKEN'])

# endregion
