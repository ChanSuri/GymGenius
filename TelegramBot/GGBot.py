import time
import telepot
from pprint import pprint
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup,InlineKeyboardMarkup, InlineKeyboardButton



def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)
        
    if msg['text'] == '/knowus':
        bot.sendMessage(chat_id, 'Hiiiiiiiiii')
    elif msg['text'] == '/gymsituation':
        # mark_up = ReplyKeyboardMarkup(keyboard=[['Occupancy'],['Tempurature'],['Free machine'],['Forecast']], one_time_keyboard=True)
        # bot.sendMessage(chat_id, text='What would you like to know?', reply_markup=mark_up)
    # elif msg['text'] == 'Occupancy':
    #     bot.sendMessage(chat_id, 'OHHH sry...Idk how many ppl there yet') 
    # elif msg['text'] == 'Tempurature':
    #     bot.sendMessage(chat_id, 'Ofc comfortable!')
    # elif msg['text'] == 'Free machine':
    #     bot.sendMessage(chat_id, 'Just take it from others directly!')
    # elif msg['text'] == 'Forecast':
    #     bot.sendMessage(chat_id, 'Don\'t worry bcs our GYM is so big!')
    
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Occupancy', callback_data='Occupancy')],
                    [InlineKeyboardButton(text='Tempurature', callback_data='Tempurature')],
                    [InlineKeyboardButton(text='Free machine', callback_data='Free machine')],
                    [InlineKeyboardButton(text='Forecast', callback_data='Forecast')],
                ])
        bot.sendMessage(chat_id, 'What would you like to know?', reply_markup=keyboard)


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if query_data  == 'Occupancy':
        bot.answerCallbackQuery(query_id, text='Kickkkkk!')
    bot.answerCallbackQuery(query_id, text='where is it'+query_data)


TOKEN = '6961607644:AAFCNHwGsNI67k5m53VjFY48b5O9DlCNgZg'

bot = telepot.Bot(TOKEN)
MessageLoop(bot, {'chat': on_chat_message,'callback_query': on_callback_query}).run_as_thread()
print ('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)