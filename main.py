import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import uuid

from dotenv import load_dotenv
from os import environ as env

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ADDTASK = 1

async def start(update : Update, context: ContextTypes.DEFAULT_TYPE):
    keyb = [
        [InlineKeyboardButton("Добавить задачу", callback_data="add_task")]
    ]

    if not context.user_data.get("buttons"):
        context.user_data["buttons"] = keyb

    mark = InlineKeyboardMarkup(context.user_data["buttons"])
    msg = await update.message.reply_text("Дароу, я кароч сохраняю твои дела и все в целом", reply_markup=mark)
    context.user_data["msg_id"] = msg.id

async def add_task(update : Update, context : ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id, message_id=context.user_data["msg_id"])
    await context.bot.edit_message_text("Напиши новую задачу", chat_id=update.effective_chat.id, message_id=context.user_data["msg_id"])
    return ADDTASK

async def get_nae(update : Update, context : ContextTypes.DEFAULT_TYPE):
    context.user_data["buttons"].append([InlineKeyboardButton(update.message.text, callback_data=str(uuid.uuid4()))])

    msg = await update.message.reply_text("Ваши задачи:", reply_markup=InlineKeyboardMarkup(context.user_data["buttons"]))
    context.user_data["msg_id"] = msg.id
    return ConversationHandler.END

async def remove_task(update : Update, context : ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    needed_id = -1
    for i in range(len(context.user_data["buttons"])):
        if context.user_data["buttons"][i][0].callback_data == query.data:
            needed_id = i
    
    context.user_data["buttons"].pop(needed_id)
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data["msg_id"], text="Ваши задачи:", reply_markup=InlineKeyboardMarkup(context.user_data["buttons"]))

if __name__ == "__main__":
    app = ApplicationBuilder().token(env["TOKEN"]).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_task, pattern="^" + "add_task" + "$")],
        states={
            ADDTASK : [MessageHandler(filters.ALL, get_nae)]
        },
        fallbacks=[]
    ))

    app.add_handler(CallbackQueryHandler(remove_task))

    app.run_polling()