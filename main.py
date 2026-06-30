import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import uuid
import db
import asyncio

from dotenv import load_dotenv
from os import environ as env

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ADDTASK = 1
cdb = db.DB(env["POSTGRES_USER"], env["POSTGRES_PASSWORD"], env["POSTGRES_DB"])


async def get_keyboard(userid : int):
    zzs = await cdb.get_list_of_tasks(userid)
    keys = []
    for titl, cdat in zzs:
        keys.append([InlineKeyboardButton(text=titl, callback_data=cdat)])
    keys.append([InlineKeyboardButton(text="Добавить задачу", callback_data="add_task")])
    return keys

async def start(update : Update, context: ContextTypes.DEFAULT_TYPE):
    if not await cdb.check_user(update.effective_user.id):
        await cdb.add_user(update.effective_user.id)

    mark = InlineKeyboardMarkup(await get_keyboard(update.effective_user.id))
    msg = await update.message.reply_text("Дароу, я кароч сохраняю твои дела и все в целом", reply_markup=mark)
    # context.user_data["msg_id"] = msg.id
    await cdb.update_msg_id(update.effective_user.id, str(msg.message_id))

async def add_task(update : Update, context : ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id, message_id=await cdb.get_msg_id(update.effective_user.id))
    await context.bot.edit_message_text("Напиши новую задачу", chat_id=update.effective_chat.id, message_id=await cdb.get_msg_id(update.effective_user.id))
    return ADDTASK

async def get_nae(update : Update, context : ContextTypes.DEFAULT_TYPE):
    # context.user_data["buttons"].append([InlineKeyboardButton(update.message.text, callback_data=str(uuid.uuid4()))])
    await cdb.add_task_for_user(update.effective_user.id, update.message.text, str(uuid.uuid4()))

    msg = await update.message.reply_text("Ваши задачи:", reply_markup=InlineKeyboardMarkup(await get_keyboard(update.effective_user.id)))
    # context.user_data["msg_id"] = msg.id
    await cdb.update_msg_id(update.effective_user.id, str(msg.message_id))
    return ConversationHandler.END

async def remove_task(update : Update, context : ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # needed_id = -1
    # for i in range(len(context.user_data["buttons"])):
    #     if context.user_data["buttons"][i][0].callback_data == query.data:
    #         needed_id = i
    
    # context.user_data["buttons"].pop(needed_id)

    await cdb.delete_task(query.data)
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=await cdb.get_msg_id(update.effective_user.id), text="Ваши задачи:", reply_markup=InlineKeyboardMarkup(await get_keyboard(update.effective_user.id)))

async def on_startup(application):
    await cdb.init_db()


if __name__ == "__main__":
    app = ApplicationBuilder().token(env["TOKEN"]).post_init(on_startup).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_task, pattern="^" + "add_task" + "$")],
        states={
            ADDTASK : [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nae)]
        },
        fallbacks=[]
    ))

    app.add_handler(CallbackQueryHandler(remove_task))
    app.run_polling()