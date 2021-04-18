import discord
from discord.ext import commands
import constant as cs
from multi_func import get_role

AmongUs_playing = False


# ゲーム中のミュート処理
async def run_amongusstart(bot, ctx):
    global AmongUs_playing
    if ctx.channel.id != cs.Among_room and ctx.channel.id != cs.Test_room:
        await ctx.delete()
        return await ctx.send(f'{ctx.author.mention} このチャンネルでは実行できません', delete_after=5)
    elif AmongUs_playing:
        return await ctx.send(f'{ctx.author.mention} 既に実行済みです', delete_after=5)

    AmongUs_playing = True
    emoji = ["🔇", "🔊", "✅"]
    embed = discord.Embed(title="Among Us VC のサーバーミュート操作",
                          description="リアクションをタップすると実行されます", color=0x0000CD)
    embed.set_thumbnail(url='https://i.imgur.com/rsN0YMC.png')
    embed.add_field(name=emoji[0], value="全員をミュート", inline=False)
    embed.add_field(name=emoji[1], value="全員のミュートを解除", inline=False)
    embed.add_field(name=emoji[2], value="ミュート操作コマンドを終了", inline=False)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction(emoji[0])
    await msg.add_reaction(emoji[1])
    await msg.add_reaction(emoji[2])

    def reaction_check(check_reaction, check_user):
        # 参加者ではないメンバー、指定されていないリアクションについては無視
        if cs.AmongUs not in [roles.id for roles in guild.get_member(check_user.id).roles] or check_user.bot:
            return False
        elif str(check_reaction.emoji) not in emoji:
            return False
        return True

    guild = bot.get_guild(ctx.guild.id)
    among_vc = bot.get_channel(cs.Among_vc)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=1000, check=reaction_check)
        except asyncio.exceptions.TimeoutError:
            for member in among_vc.members:
                if member.voice.mute:
                    await member.edit(mute=False)
            await ctx.send("一定時間反応が無かったのでコマンド実行を終了しました", delete_after=30)
            break
        # 全員ミュートする
        if str(reaction.emoji) == emoji[0]:
            for member in among_vc.members:
                if member.voice.mute:
                    await member.edit(mute=False)
            AmongUs_playing = True
        # 全員ミュート解除する
        elif str(reaction.emoji) == emoji[1]:
            for member in among_vc.members:
                if not member.voice.mute:
                    await member.edit(mute=True)
            AmongUs_playing = False
        # 全員のミュート解除 & 終了
        elif str(reaction.emoji) == emoji[2]:
            for member in among_vc.members:
                if member.voice.mute:
                    await member.edit(mute=False)
            await ctx.send("コマンド実行を終了しました", delete_after=10)
            break
        await msg.remove_reaction(str(reaction.emoji), user)

    await msg.delete()
    AmongUs_playing = False
    return


class Among_command(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(cs.AmongUs)
    async def aus(self, ctx):
        await run_amongusstart(self.bot, ctx)

    @commands.command()
    @commands.has_role(cs.AmongUs)
    async def amongusstart(self, ctx):
        await run_amongusstart(self.bot, ctx)

    @commands.Cog.listener(name='on_voice_state_update')
    @commands.guild_only()
    @commands.has_role(cs.Visitor)
    async def on_voice_state_update(self, member, before, after):
        global AmongUs_playing
        # プレイ中でない時は実行しない
        if not AmongUs_playing:
            return

        try:
            # AmongUsボイスチャンネルに入ってきたユーザーをミュート
            if after.channel.id == cs.Among_vc and before.channel != after.channel:
                if not member.voice.mute:
                    await member.edit(mute=True)
            # AmongUsボイスチャンネルから抜けたユーザーをミュート解除
            elif before.channel.id == cs.Among_vc and before.channel != after.channel:
                if member.voice.mute:
                    await member.edit(mute=False)
        except AttributeError:
            pass


def setup(bot):
    return bot.add_cog(Among_command(bot))
