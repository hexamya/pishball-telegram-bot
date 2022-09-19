from bot.database import *
from bot.utils.settings import *

from telegram import (
    Update,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup
    )
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    )
from telegram.constants import ParseMode

db = Database()

#####################################################################
###################### BROADCAST CONVERSATION #######################
SEND_TYPE_MESSAGE, SEND_SUBS_MESSAGE, SEND_MESSAGE = range(3)

async def type_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    if user.id != ADMIN:
        return ConversationHandler.END
    await update.message.reply_text(
        text='نوع ارسال پیام را انتخاب کنید:',
        reply_markup=ReplyKeyboardMarkup([['فرواردی'],['ناشناس']],
            resize_keyboard=True,
            one_time_keyboard=True),
    )
    return SEND_TYPE_MESSAGE

async def subs_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    user_data['type'] = update.message.text

    await update.message.reply_text(
        text='دریافت کنندگان پیام را انتخاب کنید:',
        reply_markup=ReplyKeyboardMarkup([['همه'],['کاربران'],['گروه‌ها']],
        resize_keyboard=True,
        one_time_keyboard=True),
    )
    return SEND_SUBS_MESSAGE
    
async def receive_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    user_data['subs'] = update.message.text

    groups = db.get_all_groups()['groups']
    users = db.get_all_users()['users']

    if user_data['subs'] == 'همه':
        LIST = list(groups.keys()) + list(users.keys())
    elif user_data['subs'] == 'کاربران':
        LIST = list(users.keys())
    elif user_data['subs'] == 'گروه‌ها':
        LIST = list(groups.keys())

    user_data['list'] = LIST
    await update.message.reply_text(
        text='خیلی خوب، پیام مورد نظر را ارسال کنید.',
        reply_markup=ReplyKeyboardRemove())
    return SEND_MESSAGE
        
async def send_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = context.user_data
    LIST = user_data['list']
    TYPE = user_data['type']

    s = e = 0
    if TYPE == 'فرواردی':
        for i in LIST:
            try:
                await context.bot.forward_message(
                    chat_id=i,
                    from_chat_id=update.effective_message.chat_id,
                    message_id=update.effective_message.message_id)
                s+=1
            except:
                e+=1
    else:
        for i in LIST:
            try:
                await context.bot.copy_message(
                    chat_id=i,
                    from_chat_id=update.effective_message.chat_id,
                    message_id=update.effective_message.message_id)
                s+=1
            except:
                e+=1
    context.user_data.clear()
    await update.message.reply_html(text=f'انجام شد!\n<b>موفق:</b> {s}\n<b>ناموفق:</b> {e}')
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text(
        'کنکله.',
        reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END

con_broadcast_handler = ConversationHandler(
    entry_points=[CommandHandler('sendbroadcast', type_message)],
    states={
        SEND_TYPE_MESSAGE: [CommandHandler('sendbroadcast', type_message), MessageHandler(filters.Regex('^ناشناس$') | filters.Regex('^فرواردی$'), subs_message)],
        SEND_SUBS_MESSAGE: [CommandHandler('sendbroadcast', type_message), MessageHandler(filters.Regex('(^کاربران$|^گروه‌ها$|^همه$)'), receive_message)],
        SEND_MESSAGE: [CommandHandler('sendbroadcast', type_message), MessageHandler(~ filters.Regex('/cancel'), send_message)]
    },
    fallbacks=[CommandHandler('cancel', cancel)])