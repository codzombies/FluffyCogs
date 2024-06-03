import asyncio
from typing import Dict, Union

import discord
from redbot.core import Config, bot, commands


class AutoDisconnect(commands.Cog):
    async def red_get_data_for_user(self, *, user_id):
        return {}  # No data to get

    async def red_delete_data_for_user(self, *, requester, user_id):
        pass  # No data to delete

    def __init__(self, bot: bot.Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2113674295, force_registration=True)
        self.config.register_guild(timeouts={})
        self.timeouts: Dict[int, Dict[int, int]] = {}  # guild_id -> {channel_id -> timeout}

    @commands.command(aliases=["autodisconnect"])
    @commands.guild_only()
    @commands.mod_or_permissions(manage_guild=True)
    async def afkdisconnect(self, ctx: commands.Context, channel: discord.VoiceChannel, time: Union[int, bool]):
        """
        Sets how long to wait before disconnecting a member in a specific channel, in seconds.

        Set to -1 to disable for the channel.
        """
        if isinstance(time, bool):
            time = 0 if time else -1
        if time < -1:
            raise commands.UserFeedbackCheckFailure(
                "Time must be 0 or greater, or -1 to disable the feature"
            )
        
        guild_id = ctx.guild.id
        channel_id = channel.id

        if guild_id not in self.timeouts:
            self.timeouts[guild_id] = await self.config.guild(ctx.guild).timeouts()

        self.timeouts[guild_id][channel_id] = time
        await self.config.guild(ctx.guild).timeouts.set(self.timeouts[guild_id])
        await ctx.tick()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        def check(m: discord.Member, b: discord.VoiceState, a: discord.VoiceState):
            if m != member:
                return False
            return a.channel != after.channel

        if not after.channel:
            return
        if await self.bot.cog_disabled_in_guild(self, member.guild):
            return

        guild_id = member.guild.id
        channel_id = after.channel.id

        if guild_id not in self.timeouts:
            self.timeouts[guild_id] = await self.config.guild(member.guild).timeouts()

        timeout = self.timeouts[guild_id].get(channel_id, -1)
        if timeout < 0:
            return
        if timeout > 0:
            try:
                await self.bot.wait_for("voice_state_update", check=check, timeout=timeout)
            except asyncio.TimeoutError:
                pass  # we want this to happen
            else:
                return  # the member moved on their own
        try:
            await member.move_to(None)
        except discord.HTTPException:
            return

# Add this to the main script to load the cog
def setup(bot: bot.Red):
    bot.add_cog(AutoDisconnect(bot))