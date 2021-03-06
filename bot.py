import json
import bmemcached
import discord.ext.commands.bot


with open('config.json') as config_file:
    config = json.load(config_file)


memcache = bmemcached.Client(config['memcache']['servers'].split(','),
                             config['memcache']['username'],
                             config['memcache']['password'])
discord_bot = discord.ext.commands.bot.Bot(command_prefix='!')


@discord_bot.command(aliases=['emote'])
async def set_emote(ctx, new_emote):
    old_emote = memcache.get('emote')
    await ctx.send(f'Old emote: {old_emote}')
    memcache.set('emote', new_emote)
    await ctx.send(f'Set emote to {new_emote}')


if __name__ == '__main__':
    discord_bot.run(config['discord_token'])
