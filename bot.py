import json
import bmemcached
import discord.ext.commands.bot


with open('config.json') as config_file:
    config = json.load(config_file)


memcache = bmemcached.Client(config['memcache']['servers'].split(','),
                             config['memcache']['username'],
                             config['memcache']['password'])
custom_help_command = discord.ext.commands.DefaultHelpCommand(sort_commands=False, no_category='Commands')
discord_bot = discord.ext.commands.bot.Bot(command_prefix='!', help_command=custom_help_command)


@discord_bot.command(name='get-emote', aliases=['get'], brief='Get the current spam emote from API')
async def get_emote(ctx):
    old_emote = memcache.get('emote')
    await ctx.send(f'Current emote: {old_emote}')


@discord_bot.command(name='set-emote', aliases=['set', 'emote'], brief='Set the current spam emote on API')
async def set_emote(ctx, new_emote):
    await ctx.invoke(get_emote)
    memcache.set('emote', new_emote)
    await ctx.send(f'Set emote to {new_emote}')


@discord_bot.command(name='api-link', aliases=['api'], brief='Get link to the API with the current spam emote')
async def api_link(ctx):
    await ctx.send('https://the-pog-market-team-api.herokuapp.com/emote.json')


@discord_bot.command(name='github-link', aliases=['github'], brief='Get link to our GitHub')
async def github_link(ctx):
    await ctx.send('https://github.com/ThePogMarketTeam')


@discord_bot.event
async def on_ready():
    print('Bot started.')


if __name__ == '__main__':
    print('Bot starting..')
    discord_bot.run(config['discord_token'])
