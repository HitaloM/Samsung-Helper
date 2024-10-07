# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import datetime
import html
import io
import os
import sys
import traceback
from collections.abc import Callable
from signal import SIGINT

import humanize
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, CallbackQuery, InaccessibleMessage, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from meval import meval

from sambot.filters.users import IsSudo
from sambot.utils.callback_data import StartCallback
from sambot.utils.devices import sync_devices
from sambot.utils.notify import sync_firmwares
from sambot.utils.systools import ShellExceptionError, parse_commits, shell_run

router = Router(name="doas")

# Only sudo users can use these commands
router.message.filter(IsSudo())
router.callback_query.filter(IsSudo())


@router.message(Command(commands=["reboot", "restart"]))
async def reboot(message: Message):
    await message.reply("Rebooting...")
    os.execv(sys.executable, [sys.executable, "-m", "sambot"])


@router.message(Command("shutdown"))
async def shutdown_message(message: Message):
    await message.reply("Turning off...")
    os.kill(os.getpid(), SIGINT)


@router.message(Command(commands=["update", "upgrade"]))
async def bot_update(message: Message):
    sent = await message.reply("Checking for updates...")

    try:
        await shell_run("git fetch origin")
        stdout = await shell_run("git log HEAD..origin/main")
        if not stdout:
            await sent.edit_text("There is nothing to update.")
            return
    except ShellExceptionError as error:
        await sent.edit_text(f"<code>{html.escape(str(error))}</code>")
        return

    commits = parse_commits(stdout)
    changelog = "<b>Changelog</b>:\n"
    for c_hash, commit in commits.items():
        changelog += f"  - [<code>{c_hash[:7]}</code>] {html.escape(commit["title"])}\n"
    changelog += f"\n<b>New commits count</b>: <code>{len(commits)}</code>."

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🆕 Update", callback_data=StartCallback(menu="update"))
    await sent.edit_text(changelog, reply_markup=keyboard.as_markup())


@router.callback_query(StartCallback.filter(F.menu == "update"))
async def upgrade_callback(callback: CallbackQuery):
    message = callback.message
    if not message:
        return

    if isinstance(message, InaccessibleMessage):
        return

    await message.edit_reply_markup()
    sent = await message.reply("Upgrading...")

    commands = [
        "git reset --hard origin/main",
        "rye sync --update-all",
    ]

    stdout = ""
    for command in commands:
        try:
            stdout += await shell_run(command)
        except ShellExceptionError as error:
            await sent.edit_text(f"<code>{html.escape(str(error))}</code>")
            return

    await sent.reply("Uploading logs...")
    document = io.BytesIO(stdout.encode())
    document.name = "update_log.txt"
    document = BufferedInputFile(document.getvalue(), filename=document.name)
    await sent.reply_document(document=document)

    await sent.reply("Restarting...")
    os.execv(sys.executable, [sys.executable, "-m", "sambot"])


@router.message(Command(commands=["shell", "sh"]))
async def bot_shell(message: Message, command: CommandObject):
    code = str(command.args)
    sent = await message.reply("Running...")

    try:
        stdout = await shell_run(command=code)
    except ShellExceptionError as error:
        await sent.edit_text(f"<code>{html.escape(str(error))}</code>")
        return

    output = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"
    if stdout:
        if len(stdout) > (4096 - len(output)):
            document = io.BytesIO(stdout.encode())
            document.name = "output.txt"
            document = BufferedInputFile(document.getvalue(), filename=document.name)
            await message.reply_document(document=document)
        else:
            output += f"<b>Output\n&gt;</b> <code>{html.escape(stdout)}</code>"

    await sent.edit_text(output)


@router.message(Command(commands=["eval", "ev"]))
async def evaluate(message: Message, command: CommandObject):
    query = command.args
    sent = await message.reply("Evaluating...")

    try:
        stdout = await meval(query, globals(), **locals())
    except BaseException:
        exc = sys.exc_info()
        exc = "".join(
            traceback.format_exception(exc[0], exc[1], exc[2].tb_next.tb_next.tb_next)  # type: ignore[misc]
        )
        error_txt = "<b>Failed to execute the expression:\n&gt;</b> <code>{eval}</code>"
        error_txt += f"\n\n<b>Error:\n&gt;</b> <code>{exc}</code>"
        await sent.edit_text(
            error_txt.format(eval=query, exc=html.escape(exc)),
            disable_web_page_preview=True,
        )
        return

    output_message = f"<b>Expression:\n&gt;</b> <code>{html.escape(str(query))}</code>"

    if stdout:
        lines = str(stdout).splitlines()
        output = "".join(f"<code>{html.escape(line)}</code>\n" for line in lines)

        if len(output) > 0:
            if len(output) > (4096 - len(output_message)):
                document = io.BytesIO(
                    (output.replace("<code>", "").replace("</code>", "")).encode()
                )
                document.name = "output.txt"
                document = BufferedInputFile(document.getvalue(), filename=document.name)
                await message.reply_document(document=document)
            else:
                output_message += f"\n\n<b>Result:\n&gt;</b> <code>{output}</code>"

    await sent.edit_text(output_message)


@router.message(Command("ping"))
async def ping(message: Message):
    start = datetime.datetime.now(tz=datetime.UTC)
    sent = await message.reply("<b>Pong!</b>")
    delta = (datetime.datetime.now(tz=datetime.UTC) - start).total_seconds() * 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{delta:.2f}ms</code>")


async def measure_and_edit(message: Message, task_name: str, task_func: Callable) -> None:
    start_time = datetime.datetime.now(tz=datetime.UTC)
    sent = await message.reply(f"Syncing {task_name}...")
    await task_func()
    delta = (datetime.datetime.now(tz=datetime.UTC) - start_time).total_seconds()
    human_readable_delta = humanize.precisedelta(datetime.timedelta(seconds=delta))
    await sent.edit_text(f"Synced {task_name} in <code>{human_readable_delta}</code>.")


@router.message(Command("syncfirmware"))
async def sync_f(message: Message):
    await measure_and_edit(message, "firmwares", sync_firmwares)


@router.message(Command("syncdevices"))
async def sync_d(message: Message):
    await measure_and_edit(message, "devices", sync_devices)
