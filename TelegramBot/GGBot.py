import time
import telepot
import json
from MyMQTT import *
from pprint import pprint
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup,InlineKeyboardMarkup, InlineKeyboardButton
TOKEN = '6961607644:AAFCNHwGsNI67k5m53VjFY48b5O9DlCNgZg'

class Telegrambot():

    def __init__(self, conf):
        try:
            self.conf = json.load(open(conf))
        except:
            print("Configuration file not found")
            exit()
        self.token = self.conf["token"]
        self.bot = telepot.Bot(self.token)
        self.serviceId = self.conf["serviceId"]
        self.client = MyMQTT(self.serviceId, self.conf["broker"], int(self.conf["port"]), self)
        self.webServerAddr = self.conf["webServerAddress"]
        self.Topic = self.conf["Topic"]
        self.status = None
        
    def start(self):
        self.client.start()
        # subscribe to topic according to available device
        self.client.mySubscribe(self.Topic)
        MessageLoop(self.bot,{'chat': self.on_chat_message,'callback_query': self.on_callback_query}).run_as_thread()
        
    def stop(self):
        self.workingStatus = False
        self.client.stop()
        # unregister device
        # self.Reg.delete("service", self.serviceId)
        
    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)
        
        message=msg['text']    
        if message == '/knowus':
            self.bot.sendMessage(chat_id, 'Hiiiiiiiiii')
        elif message == '/gymsituation':
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
            self.bot.sendMessage(chat_id, 'What would you like to know?', reply_markup=keyboard)
        self.bot.sendMessage(chat_id,text="You sent:\n"+message)
            
    def check_auth(self,chat_id):
        try:
            if self.chat_auth[str(chat_id)]==True:
                return True
            else:
                return False
        except:
            return False
                   
    #Actuation via MQTT
    def notify(self, topic, msg):
        msg = json.loads(msg)
        info = "ALERT!!Too crowded!!!"
        print(msg)


    def on_callback_query(self,msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data  == 'Occupancy':
            self.bot.answerCallbackQuery(query_id, text='Kickkkkk!')
        self.bot.answerCallbackQuery(query_id, text='where is it'+query_data)

    
if __name__ == "__main__":
    configFile = input("Enter the location of configuration file: ")
    if len(configFile) == 0:
        configFile = "TelegramBot/configuration.json"

    telegrambot = Telegrambot(configFile)
    telegrambot.start()
    

    print('waiting ...')

# Keep the program running.
    while (True):
        if input() == 'q':
            break

    telegrambot.stop()