from telegram.ext import (
    Application,
    PicklePersistence,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    InvalidCallbackData, 
    )
import logging

from bot.commands import *
from bot.queries import *
from bot.conversations import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    """Run the bot."""
    # persistence = PicklePersistence(filename="databot", store_callback_data=True)
    application = (
        Application.builder()
        .token(TOKEN)
        .arbitrary_callback_data(True)
        .build()
        # .persistence(persistence)
        )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Regex('^پیش بینی$'), predict))
    application.add_handler(MessageHandler(filters.Regex('^جدول$'), table))
    application.add_handler(MessageHandler(filters.Regex('^امتیاز$'), points))
    application.add_handler(MessageHandler(filters.Regex('^راهنما$'), start))
    application.add_handler(MessageHandler(filters.Regex('^آپدیت$'), update))
    application.add_handler(con_broadcast_handler)
    
    application.add_handler(CallbackQueryHandler(
        queries,
        pattern = tuple))
    application.add_handler(CallbackQueryHandler(
        invalid_queries,
        pattern= InvalidCallbackData))
    
    application.run_polling()
    
main()