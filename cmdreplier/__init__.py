from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core.bot import Red
    from redbot.core.commands import Context

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def new_send(__sender, /, *args, **kwargs):
    ctx: Context = __sender.__self__
    if "reference" not in kwargs:
        message = ctx.message
        try:
            resolved = message.reference.resolved
            failsafe_ref = resolved.to_reference(fail_if_not_exists=False)
        except AttributeError:
            pass
        else:
            kwargs["reference"] = failsafe_ref
            kwargs["mention_author"] = resolved.author in message.mentions
    return await __sender(*args, **kwargs)


async def before_hook(ctx: Context):
    if ctx.message.reference:
        ctx.send = partial(new_send, ctx.send)


def setup(bot: Red):
    bot.before_invoke(before_hook)


def teardown(bot: Red):
    bot.remove_before_invoke_hook(before_hook)
