from discord.ext import commands
import constant as cs
from multi_func import get_role


async def run(guild, ctx, role_name):
    if role_name in ["participant", "p"]:
        rm_role = get_role(guild, cs.Participant)
        cs.Joiner = []
    elif role_name in ["winner", "w"]:
        rm_role = get_role(guild, cs.Winner)
    elif role_name in ["loser", "l"]:
        rm_role = get_role(guild, cs.Loser)
    elif role_name in ["zyanken", "z"]:
        rm_role = get_role(guild, cs.Zyanken)
    else:
        return await ctx.send(f"{ctx.author.mention} RoleNameを入力してください\n"
                              ">>> **_ReSet RoleName**\nRoleName = Participant / Winner / Loser / Zyanken")

    for member in rm_role.members:
        await member.remove_roles(rm_role)
    await ctx.send(f"ロール {rm_role.mention} をリセットしました")


class RoleReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def rs(self, ctx, role_name=""):
        await run(self.bot.get_guild(cs.Server), ctx, role_name)

    @commands.command()
    @commands.has_any_role(cs.Administrator, cs.Moderator)
    async def reset(self, ctx, role_name=""):
        await run(self.bot.get_guild(cs.Server), ctx, role_name)


def setup(bot):
    return bot.add_cog(RoleReset(bot))
