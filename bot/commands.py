from bot.database import *
from bot.plugins.predict import *
from bot.utils import *

from bot.records import *

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    )
from telegram.ext import CallbackContext
from telegram.constants import ParseMode

import re

db = Database()

@record
async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=START_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=KB,
        disable_web_page_preview=True)

@record
async def predict(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    predict = Predict(db, user_id)
    fixtures = predict.get_fixtures()
    return await update.message.reply_html(
        fixtures['texts'][0],
        reply_markup=InlineKeyboardMarkup(fixtures['buttons'][0]))

@record
async def table(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    predict = Predict(db, user_id)
    table = predict.get_table()
    return await update.message.reply_html(
        table['text'],
        reply_markup=moving_keyboard('tops', table['page'], table['pages']))


@record
async def points(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    predict = Predict(db, user_id)
    points = predict.get_points()
    return await update.message.reply_html(
        points,
        reply_markup=KB)
        
@record
async def update(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    if user_id == ADMIN:
        db.update_data()
        return await update.message.reply_html(
            'دیتابیس آپدیت شد.')
