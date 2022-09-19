from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def reply_keyboard(buttons):
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

teams = {
    'Arsenal': 'آرسنال',
    'Aston Villa': 'استون ویلا',
    'Bournemouth': 'بورنموث',
    'Brentford': 'برنتفورد',
    'Brighton': 'برایتون',
    'Chelsea': 'چلسی',
    'Crystal Palace': 'کریستال پالاس',
    'Everton': 'اورتون',
    'Fulham': 'فولام',
    'Leeds': 'لیدز یونایتد',
    'Leicester': 'لستر سیتی',
    'Liverpool': 'لیورپول',
    'Man City': 'منچستر سیتی',
    'Man Utd': 'منچستر یونایتد',
    'Newcastle': 'نیوکسل یونایتد', 
    "Nott'm Forest": 'ناتینگهام فارست',
    'Southampton': 'ساوتهمپتون',
    'Spurs': 'تاتنهام هاتسپر',
    'West Ham': 'وستهم یونایتد',
    'Wolves': 'ولورهمپتون'
}

def static_keyboard(name, buttons, data):
    keyboard = []
    for row in buttons:
        keyboard += [[InlineKeyboardButton(button, callback_data = (name, button,data)) for button in row]]
    
    return InlineKeyboardMarkup(keyboard)

KB = reply_keyboard([['پیش بینی', 'جدول'],['امتیاز','راهنما']])

def dynamic_keyboard(name, data):
    return InlineKeyboardMarkup.from_column(
        [InlineKeyboardButton(button, callback_data=(name, button, data)) for button in data]
        )

def moving_keyboard(key, page, pages):
    return InlineKeyboardMarkup.from_row(
        [InlineKeyboardButton('<<<', callback_data=('table', 'prev', page, pages)),InlineKeyboardButton('جایگاه من' if key!='me' else 'نفرات برتر', callback_data=('table', 'me' if key!='me' else 'tops', page, pages)),InlineKeyboardButton('>>>', callback_data=('table', 'next', page, pages))]
    )