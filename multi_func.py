import discord
import constant as cs


def get_role(guild, role_id):
    return discord.utils.get(guild.roles, id=role_id)


def role_check_admin(ctx_role):
    return cs.Administrator in [roles.id for roles in ctx_role.author.roles]


def role_check_mode(ctx_role):
    roles = [roles.id for roles in ctx_role.author.roles]
    return any([cs.Administrator in roles, cs.Moderator in roles])


def role_check_visit(ctx_role):
    roles = [roles.id for roles in ctx_role.author.roles]
    return any([cs.Administrator in roles, cs.Moderator in roles, cs.Visitor in roles])
