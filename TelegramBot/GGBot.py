import requests
import telepot
import json
import datetime
import time
from MyMQTT import *
from pprint import pprint
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup,InlineKeyboardMarkup, InlineKeyboardButton
from registration_functions import register_service
import cherrypy
import threading


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
        self.__message={'service': self.serviceId,'n':'','value':'', 'timestamp':'','unit':"status"}

        self.switchTopic = self.conf["switchTopic"] 
        self.availTopic = self.conf["availTopic"]
        self.crowdTopic = self.conf["crowdTopic"]
        self.overtempTopic = self.conf["overtempTopic"]
        
        self.machines = self.conf["machines"]
        self.availbilaity = self.conf["machineAvailable"]
        self.occupancy = self.conf["occupancy"]
        
        self.user_states = {}
        self.status = None
        self.suggestion = []
        self.chat_auth = {}
        self.chatIDs=[]
        self.switchMode = "None"
        
        self.possibleSwitch =[]
        self.zones = self.conf["zones"]
        for zone in self.zones:
            temp = [zone]
            self.possibleSwitch.append(temp)
        self.possibleSwitch.append(["ALL"])
        self.possibleSwitch.append(["All AC"])
        self.possibleSwitch.append(["Entrance"])
        self.possibleSwitch.append(["All Machines"])
        self.possibleSwitch.append(["Machines"])
        
        
    def start(self):
        self.client.start()
        self.client.mySubscribe(self.crowdTopic) #occupancy alert
        # subscribe to topic according to available device...not sure to subscribe
        #self.client.mySubscribe(self.availTopic)
        MessageLoop(self.bot,{'chat': self.on_chat_message,'callback_query': self.on_callback_query}).run_as_thread()
        
    def stop(self):
        self.workingStatus = False
        self.client.stop()
    
    
    #example
    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)
        self.chatIDs.append(chat_id)
        message = msg['text']
        if chat_id in self.user_states and self.user_states[chat_id] == 'awaiting_suggestion':
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("TelegramBot/suggestions.txt", "a") as file:
                file.write(f"{current_time} | {chat_id} | {message}\n")
            self.bot.sendMessage(chat_id, "Your suggestion is saved! Thank you.")
            self.user_states[chat_id] = None
        elif message ==  "/start":
            self.bot.sendMessage(chat_id, 'Welcome to GymGenius! You can start your incredible experience here!')
        elif message == '/knowus':
            self.bot.sendMessage(chat_id, 'The IoT application Gym Genius is intended to optimize gym management, improve customer satisfaction, and guarantee optimal utilization of resources. It employs automated mechanisms, a variety of sensors, and a Telegram bot to facilitate user interaction.')
        elif message == "/suggestion": #write as client
            self.bot.sendMessage(chat_id, 'Please enter your suggestion:')
            self.user_states[chat_id] = 'awaiting_suggestion'
        elif message == "/login":
            self.initial_message(chat_id)
        elif message == "/client":
            self.user_message(chat_id)
        elif message == "/administrator":
            self.chat_auth[str(chat_id)]=False
            self.bot.sendMessage(chat_id, 'Please enter the password')
        elif message == "/suggestions": #check as admin
            if self.check_auth(chat_id)==True:
                self.admin_suggestion(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "/envdata":
            if self.check_auth(chat_id)==True:
                self.admin_see_data(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "/operate":
            if self.check_auth(chat_id)==True:
                self.admin_operate(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "/switchon":
            if self.check_auth(chat_id)==True:
                self.switchMode ="on"
                self.admin_switch_zone(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "/switchoff":
            if self.check_auth(chat_id)==True:
                self.switchMode="off"
                self.admin_switch_zone(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "/Logout":
            if self.check_auth(chat_id)==True:
                del self.chat_auth[str(chat_id)]
            else:
                self.bot.sendMessage(chat_id, "You haven't logged in!")
        elif message in list(map(str, range(16, 27))):
            self.publish(target="AC",switchTo="on:"+message)
            self.bot.sendMessage(chat_id, f"AC switched on and set {message} °C")
        else:
            if self.switchMode == "on" or self.switchMode=="off":
                if self.check_auth(chat_id) ==True:
                    for switch in self.possibleSwitch:
                        if switch[0] == message:
                            self.admin_switch(chat_id,message,self.switchMode)
                            self.switchMode ="None"
                            self.bot.sendMessage(chat_id, "Command sent successfully!")
                            mark_up = ReplyKeyboardMarkup(keyboard=[['/operate'], ['/envdata'],['/suggestions'],['/Logout']],one_time_keyboard=True)
                            self.bot.sendMessage(chat_id, text='What would you like to do next?', reply_markup=mark_up)
                            return
                    self.bot.sendMessage(chat_id, 'Please enter the correct command!')
                else:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
                    self.chat_auth[str(chat_id)]==False
            else:
                try:
                    if self.chat_auth[str(chat_id)]==False:
                        if message == "admin":
                            self.chat_auth[str(chat_id)]=True
                            self.admin_message(chat_id)
                        else:
                            self.bot.sendMessage(chat_id, 'Password error! Please re-type password!')
                    else:
                        self.bot.sendMessage(chat_id, 'Please enter the correct command!')
                except:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login !")
                    
            
    def initial_message(self,chat_id):
        # design as reply keyboard
        mark_up = ReplyKeyboardMarkup(keyboard=[['/client'], ['/administrator']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Welcome our gym genius!', reply_markup=mark_up)
        
    def user_message(self, chat_id):
        self.bot.sendMessage(chat_id,
                        parse_mode='Markdown',
                        text='*What do you want to know about the Gym?*'
                        )
        self.bot.sendMessage(chat_id,
                        parse_mode='Markdown',
                        text="[See data]("+self.webServerAddr+")"
                        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='Occupancy', callback_data='occupancy')],
                        [InlineKeyboardButton(text='Availability', callback_data='availability')],
                        [InlineKeyboardButton(text='Forecast', callback_data='forecast')],
                    ])
        self.bot.sendMessage(chat_id, '*What would you like to know?*', reply_markup=keyboard)

    def check_auth(self,chat_id):
        try:
            if self.chat_auth[str(chat_id)]==True:
                return True
            else:
                return False
        except:
            return False
        
    def admin_message(self,chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=[['/operate'],['/envdata'],['/suggestions']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Login success!', reply_markup=mark_up)

    def admin_suggestion(self,chat_id):
        with open("TelegramBot/suggestions.txt", "r") as file:
            for line in file:
                self.bot.sendMessage(chat_id, text=line.strip())

    def admin_see_data(self,chat_id):
        self.bot.keyboardRow = 2
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='See data', url=self.webServerAddr)]
        ])
        self.bot.sendMessage(chat_id, 'What would you like to see?', reply_markup=keyboard)
        mark_up = ReplyKeyboardMarkup(keyboard=[['/operate'], ['/envdata'],['/suggestions']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='What else would you like to do?', reply_markup=mark_up)
       
    def admin_operate(self, chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=[['/switchon'], ['/switchoff']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Please select your operation...', reply_markup=mark_up)
        
    def admin_switch_zone(self,chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=self.possibleSwitch, one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Please select the zone or the devices you want to switch...', reply_markup=mark_up)
    
    def publish(self,target, switchTo):
        if switchTo not in ["on", "off"]:
            data = switchTo.split(':')  
            switchTo = data[0] 
            temp = data[1]
            msg = {"target":target,"switchTo":switchTo,"value":temp,"timestamp":str(datetime.datetime.now())}
        else: 
            msg = {"target":target,"switchTo":switchTo,"timestamp":str(datetime.datetime.now())}
        self.client.myPublish(self.switchTopic, msg)
        print("Published: " + json.dumps(msg))
        
    def admin_switch(self,chat_id,message,switchMode):
        if message == "ALL":
            self.publish(target="ALL",switchTo=switchMode)
        elif message == "All AC":
            if switchMode == "on":
                temp = list(map(str, range(16, 27)))
                mark_up = ReplyKeyboardMarkup(keyboard=[temp],one_time_keyboard=True)
                self.bot.sendMessage(chat_id, text='Please select your operation...', reply_markup=mark_up)
                time.sleep(5)
            else:
                self.publish(target="AC",switchTo=switchMode)
        elif message == "All machines":
            self.publish(target="machines",switchTo=switchMode)
        elif message == "Entrance":
            self.publish(target="entrance",switchTo=switchMode)
        elif message == "Machines":
            machines = self.machines
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=machine, callback_data=f"{machine}:{switchMode}")] for machine in machines])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select your machine to operate...*', reply_markup=keyboard)
        else:
            self.publish(target=message,switchTo=switchMode)
    
    def notify(self,topic,msg):
        print(msg)
        message=json.loads(msg)
        self.tempthreshold=30
        self.crowdthreshold=30
        if message["n"]=="temperature":
            if message["value"]>self.tempthreshold:
                tosend=f"Temperature is reaching {message['value']}, do you want to turn on the AC?"                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Yes 🟡', callback_data='22'),
                    InlineKeyboardButton(text='No ⚪', callback_data='off')]
                ])
                for chat_ID in self.chatIDs:
                    self.bot.sendMessage(chat_ID, text=tosend, reply_markup=keyboard)
        elif message["n"]=="occupancy":
            if message["value"]>self.crowdthreshold:
                tosend=f"Our clients is reaching {message['value']}, we suggest you to come another time!"
                for chat_ID in self.chatIDs:
                    self.bot.sendMessage(chat_ID, text=tosend)
       

    def on_callback_query(self,msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data  == 'occupancy': #request
            try:
                response = requests.get(self.occupancy)
                if response.status_code == 200:
                    data = response.json()
                    print(f'The response of the post is {data}.')
                    self.bot.answerCallbackQuery(query_id, text='Currecnt occupancy is %'+ data["v"]+'Time:'+ data["bt"])
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}") 
        elif query_data  == 'availability':
            try: #choose machine
                response = requests.get(self.availbilaity, json=data)
                if response.status_code == 200:
                    data = response.json()
                    self.bot.answerCallbackQuery(query_id, text='Available machine:'+ data["n"]+'number:'+ data["v"] +'Time:'+ data["time"])
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}") 
        elif query_data  == 'forecast':
            try:
                response = requests.post(self.occupancy, json=data)
                if response.status_code == 200:
                    data = response.json()
                    self.bot.answerCallbackQuery(query_id, text='Predict occupancy:'+ data["prediction_matrix"])
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}") 
        elif query_data == 'on':
            self.publish(target="AC",switchTo="on:22")
            self.bot.sendMessage(chat_id, text=f"AC switched on and set 22°C")
        elif query_data == 'off':
            pass
        else:
            print(query_data)
            data = query_data.split(':')  
            machine = data[0] 
            switchMode = data[1]
            if machine in self.machines:
                self.bot.answerCallbackQuery(query_id, text= machine + " is " + switchMode)
                self.publish(target=machine, switchTo=switchMode)

def start_cherrypy():
    cherrypy.config.update({'server.socket_port': 8086, 'server.socket_host': '0.0.0.0'})
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    }
    # Ensure 'service' is defined properly before this
    cherrypy.tree.mount(telegrambot, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
        
if __name__ == "__main__":
    # configFile = input("Enter the location of configuration file: ")
    # if len(configFile) == 0:
    #     configFile = "TelegramBot/configuration.json"
    configFile = "TelegramBot/configuration.json"
    telegrambot = Telegrambot(configFile)
    
    
    # Register the service at startup
    service_id = "telegram"
    description = "Telegram Bot"
    status = "active"
    endpoint = "http://localhost:8086/TelegramBot"
    register_service(service_id, description, status, endpoint)
    print("Telegram Service Initialized and Registered")
    
    # Start CherryPy in a separate thread
    cherrypy_thread = threading.Thread(target=start_cherrypy)
    cherrypy_thread.start()
    
    telegrambot.start()

    print('waiting ...')

# Keep the program running.
    while (True):
        if input() == 'q':
            break

    telegrambot.stop()
    cherrypy.engine.exit()