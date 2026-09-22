from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.pipeline import run_safe


def run_admin_bot(pipeline) -> None:
    token = pipeline.settings.telegram_bot_token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")
    allowed = set(pipeline.settings.admin_user_ids)

    async def guard(update: Update) -> bool:
        user = update.effective_user
        if not user or user.id not in allowed:
            if update.message:
                await update.message.reply_text("اجازه ندارید.")
            return False
        return True

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await guard(update):
            await update.message.reply_text("ربات تقویم اقتصادی Dolfin Traders آماده است.")

    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await guard(update):
            await update.message.reply_text(f"provider={pipeline.settings.api_provider}")

    async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        target, paths, events = pipeline.generate("tomorrow")
        await update.message.reply_text(f"preview {target} events={len(events)} file={paths[0].name}")

    async def send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await guard(update):
            return
        msg = pipeline.publish("tomorrow", force=True)
        await update.message.reply_text(f"sent: {msg}")

    async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await guard(update):
            run_safe(pipeline, "tomorrow", preview=False, force=True)
            await update.message.reply_text("tomorrow published")

    async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await guard(update):
            run_safe(pipeline, "today", preview=False, force=True)
            await update.message.reply_text("today published")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("today", today))
    pipeline.logger.info("Admin bot polling")
    app.run_polling()
