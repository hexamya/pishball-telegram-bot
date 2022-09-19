from bot.database import *
from bot.utils.settings import *

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from functools import wraps

db = Database()

def record(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        update, context = args
        try:
            user = update.message.from_user
            chat = update.message.chat
        
            try:
                member = await context.bot.get_chat_member(CHANNEL, user.id)
            except:
                member = {'status': 'joined'}
            if member['status'] == 'left':
                return await update.message.reply_html(
                    text= f'❕ <b>برای استفاده از ربات باید ابتدا در چنل زیر عضو شده و سپس دستور مورد نظر خود را مجددا انتخاب کنید.</b>\n\n☑️ @{CHANNEL}',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('عضویت' , url=f'https://t.me/{CHANNEL[1:]}')]]))
                
            if ADMIN != user.id:
                data = {
                    'user_id': user.id,
                    'chat_id': chat.id,
                    'chat_title': chat.title if chat.title else 'private',
                    'username': user.name,
                    'name': user.full_name,
                    'message': update.message.text
                }
                
                db.set_user(user_id=user.id, name=user.full_name, username=user.name)
                if chat.type != 'private':
                    db.set_group(chat.id, chat.title)
    
                await context.bot.send_message(
                    chat_id=DATABASE,
                    text='\n'.join([f'<b>{k}:</b> {v}' for k,v in data.items()]),
                    parse_mode=ParseMode.HTML)
                    
        except:
            await context.bot.sendMessage(
                chat_id=DATABASE,
                text=f'<b>New Error!</b>',
                parse_mode=ParseMode.HTML)
        
        else:
            return await func(*args, **kwargs) 
        
    return wrapper
