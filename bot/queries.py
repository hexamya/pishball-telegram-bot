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

async def invalid_queries(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer(text='دکمه‌های این پیام دیگه فعال نیستن! لطفا دوباره دستور رو ارسال کن.', show_alert=True)

async def queries(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        data = query.data
        msg = query.message
        user_id = query.from_user.id

        if msg.chat.type == 'private':
            pass
        elif msg.reply_to_message.from_user.id == user_id:
            pass
        else:
            return await query.answer(
                text='شما به پنل دیگران دسترسی ندارید!\nبرای استفاده از این قابلیت، خودتان دستور را ارسال کنید.',
                show_alert=True)

        name = data[0]

        if name=='move':
            key, active_event = data[1:]
            predict = Predict(db, user_id)
            if key == 'this':
                pass
            elif key == 'next':
                active_event += 1
            elif key == 'prev':
                active_event -= 1
            active_event = 1 if active_event==39 else 38 if active_event==0 else active_event
            fixtures = predict.get_fixtures(active_event=active_event)
            await query.answer()
            await query.edit_message_text(
                text=fixtures['texts'][0],
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(fixtures['buttons'][0]))
        elif name=='predict':
            predict = Predict(db, user_id)
            fixture_id, team_h, team_a, fixture, submit = data[1:]
            fixture = predict.get_fixture(fixture_id, team_h, team_a, fixture, submit)
            answer = fixture['answer']
            if answer:
                await query.answer(
                    text=answer,
                    show_alert=True)
            else:
                await query.answer()
            await query.edit_message_text(
                text=fixture['fixture']['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(fixture['buttons']))
        elif name=='table':
            predict = Predict(db, user_id)
            key, page, pages = data[1:4]
            if key == 'next':
                page += 1
            elif key == 'prev':
                page -= 1
            elif key == 'tops':
                page = 0
            elif key == 'me':
                page = 'me'
            page = 0 if page==pages else pages-1 if page==-1 else page
            table = predict.get_table(page)
            await query.answer()
            await query.edit_message_text(
                text=table['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=moving_keyboard(key, table['page'], table['pages']))
        elif name=='fixture_table':
            predict = Predict(db, user_id)
            page, data = data[1:]
            table = predict.get_fixture_table(data, page)
            await query.answer()
            await query.edit_message_text(
                text=table['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(table['buttons']))
        elif name=='event_table':
            predict = Predict(db, user_id)
            page, data = data[1:]
            table = predict.get_event_table(data, page)
            await query.answer()
            await query.edit_message_text(
                text=table['text'],
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(table['buttons']))
    except:
        await query.answer(
            text='زیاد از دکمه‌ها استفاده کردی. لطفا چند ثانیه‌ای صبر کن!',
            show_alert=True)