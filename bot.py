import json
import typing

import bmemcached
import aiohttp
import discord.ext.commands.bot
from bs4 import BeautifulSoup


with open('config.json') as config_file:
    config = json.load(config_file)


memcache = bmemcached.Client(config['memcache']['servers'].split(','),
                             config['memcache']['username'],
                             config['memcache']['password'])
custom_help_command = discord.ext.commands.DefaultHelpCommand(sort_commands=False, no_category='Commands')
discord_bot = discord.ext.commands.bot.Bot(command_prefix='!', help_command=custom_help_command)


async def is_admin(ctx):
    if config['admin_role_id'] in [r.id for r in ctx.author.roles]:
        return True
    else:
        await ctx.send('You need the Admin role to use this command!')
        return False


@discord_bot.command(name='get-emote', aliases=['get'], brief='Get the current spam emote from API')
async def get_emote(ctx):
    current_emote = memcache.get('emote')
    await ctx.send(f'Current emote: {current_emote}')

    return current_emote


@discord_bot.command(name='set-emote', aliases=['set', 'emote'], brief='Set the current spam emote on API')
@discord.ext.commands.check(is_admin)
async def set_emote(ctx, new_emote: typing.Union[discord.Emoji, str]):
    if isinstance(new_emote, discord.Emoji):
        new_emote_str = new_emote.name
    else:
        new_emote_str = new_emote

    current_emote = await ctx.invoke(get_emote)
    if new_emote_str != current_emote:
        memcache.set('emote', new_emote_str)
        await ctx.send(f"<@{ctx.author.id}> set emote to {new_emote} <@&{config['ping_role_id']}>")


@discord_bot.command(name='api-link', aliases=['api'], brief='Get link to the API with the current spam emote')
async def api_link(ctx):
    await ctx.send('https://the-pog-market-team-api.herokuapp.com/emote.json')


@discord_bot.command(name='github-link', aliases=['github'], brief='Get link to our GitHub')
async def github_link(ctx):
    await ctx.send('https://github.com/ControlledStonks')


@discord_bot.command(name='stream-link', aliases=['stream'], brief='Get link to the official Twitch')
async def stream_link(ctx):
    await ctx.send('https://twitch.tv/ThePogMarket')


@discord_bot.command(name='discord-link', aliases=['discord'], brief='Get link to the official Discord')
async def discord_link(ctx):
    await ctx.send('https://discord.gg/hgaJvACRFz')


@discord_bot.command(name='rip-twitch-emotes', hidden=True)
async def rip_twitch_emotes(ctx):
    # get the index webpage
    url = 'https://www.streamscheme.com/resources/twitch-emotes-meaning-complete-list-monkas-pogchamp-omegalul-kappa/'
    await ctx.send(f'Downloading index page <{url}>')
    async with aiohttp.ClientSession(loop=ctx.bot.loop) as session:
        async with session.get(url) as response:
            html = await response.text()

    # parse the index webpage to get a dict of emotes names and image urls
    await ctx.send('Parsing index page')
    soup = BeautifulSoup(html, 'html.parser')
    twitch_emotes = {}
    for div in soup.find_all('figure', {'class': 'wp-block-image size-large'}):
        # print(div)
        emote_image_link = div.find_next('img').attrs['data-lazy-src'].removesuffix('.webp')
        emote_name = div.find_next('figcaption').find_next('a').string
        twitch_emotes[emote_name] = emote_image_link

    # add the emotes to the discord!
    await ctx.send('Adding emotes')
    existing_emotes = {e.name: e for e in ctx.guild.emojis}
    last_skipped = []

    async with aiohttp.ClientSession(loop=ctx.bot.loop) as session:
        for emote_name, emote_image_link in twitch_emotes.items():
            if emote_name in existing_emotes:
                last_skipped.append(str(existing_emotes[emote_name]))

            else:
                if last_skipped:
                    await ctx.send(f"Already exists: {''.join(last_skipped)}")
                    last_skipped = []

                # download the image
                async with session.get(emote_image_link) as response:
                    image_download = await response.read()
                if len(image_download) > 256000:
                    await ctx.send(f'Image file is too large ({len(image_download)} bytes): '
                                   f'{emote_name} <{emote_image_link}>')
                    continue

                try:
                    new_emote = await ctx.guild.create_custom_emoji(
                        name=emote_name, image=image_download,
                        reason='ControlledStonks Bot rip-twitch-emotes command'
                    )
                except discord.HTTPException as error:
                    if error.code == 30008:
                        return await ctx.send('Reached emote limit, exiting command.\n'
                                              f'{error}')
                    await ctx.send(f'Invalid emote name or url: {emote_name} <{emote_image_link}>\n'
                                   f'{error}')
                else:
                    await ctx.send(f'Added {new_emote}')

    if last_skipped:
        await ctx.send(f"Already exists: {''.join(last_skipped)}")
    await ctx.send('Done adding emotes!')


@discord_bot.event
async def on_ready():
    print('Bot started.')


if __name__ == '__main__':
    print('Bot starting..')
    discord_bot.run(config['discord_token'])
