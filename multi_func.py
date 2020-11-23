import discord
import constant


def get_role(guild, role_id):
    return discord.utils.get(guild.roles, id=role_id)


def role_check_admin(ctx_role):
    return constant.Administrator in [roles.id for roles in ctx_role.author.roles]


def role_check_mode(ctx_role):
    roles = [roles.id for roles in ctx_role.author.roles]
    return any([constant.Administrator in roles, constant.Moderator in roles])


def role_check_visit(ctx_role):
    roles = [roles.id for roles in ctx_role.author.roles]
    return any([constant.Administrator in roles, constant.Moderator in roles, constant.Visitor in roles])
