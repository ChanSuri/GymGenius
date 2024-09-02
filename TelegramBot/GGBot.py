import requests
import telepot
import json
import datetime
import base64
import pickle
import os
import cv2
from MyMQTT import *
from pprint import pprint
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup,InlineKeyboardMarkup, InlineKeyboardButton

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
        self.crowdTopic = self.conf["crowdTopic"]
        self.switchTopic = self.conf["switchTopic"]
        self.machines = self.conf["machines"]
        self.availbilaity = self.conf["machineAvailable"]
        self.occupancy = self.conf["occupancy"]
        self.user_states = {}
        self.status = None
        self.suggestion = []
        
        self.possibleSwitch =[]
        self.zones = self.conf["zones"]
        for zone in self.zones:
            temp = [zone]
            self.possibleSwitch.append(temp)
        self.possibleSwitch.append(["All light"])
        self.possibleSwitch.append(["All AC"])
        self.possibleSwitch.append(["All camera"])
        self.possibleSwitch.append(["Entrance"])
        self.possibleSwitch.append(["All Machines"])
        self.possibleSwitch.append(["ALL"])
        self.possibleSwitch.append(["Machines"])
        
        self.chat_auth = {}
        self.switchMode = "None"
        
    def start(self):
        self.client.start()
        # subscribe to topic according to available device
        self.client.mySubscribe(self.crowdTopic)
        MessageLoop(self.bot,{'chat': self.on_chat_message,'callback_query': self.on_callback_query}).run_as_thread()
        
    def stop(self):
        self.workingStatus = False
        self.client.stop()
        # unregister device
        # self.Reg.delete("service", self.serviceId)
    
    #example
    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)
        message = msg['text']
        if chat_id in self.user_states and self.user_states[chat_id] == 'awaiting_suggestion':
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("TelegramBot/suggestions.txt", "a") as file:
                file.write(f"{current_time} | {chat_id} | {message}\n")
            self.bot.sendMessage(chat_id, "Your suggestion is saved! Thank you.")
            self.user_states[chat_id] = None
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
                        [InlineKeyboardButton(text='Occupancy', callback_data='Occupancy')],
                        [InlineKeyboardButton(text='Availability', callback_data='Availability')],
                        [InlineKeyboardButton(text='Forecast', callback_data='Forecast')],
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
        msg = {"target":target,"switchTo":switchTo,"timestamp":str(datetime.datetime.now())}
        self.client.myPublish(self.switchTopic, msg)
        print("Published: " + json.dumps(msg))
        
    def admin_switch(self,chat_id,message,switchMode):
        if message == "ALL":
            self.publish(target="ALL",switchTo=switchMode)
        elif message == "All light":
            self.publish(target="light",switchTo=switchMode)
        elif message == "All AC":
            self.publish(target="AC",switchTo=switchMode)
        elif message == "All camera":
            self.publish(target="camera",switchTo=switchMode)
        elif message == "All machines":
            self.publish(target="machines",switchTo=switchMode)
        elif message == "Entrance":
            self.publish(target="entrance",switchTo=switchMode)
        elif message == "Machines":
            machines = self.machines
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=machine, callback_data=f"{machine}:{switchMode}")] for machine in machines])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select your machine to operate...*', reply_markup=keyboard)
    
    def getImage(self, uri, seq):
        uri = uri+"/"+str(seq)
        response = requests.get(uri,None)
        img =self.exactImageFromResponse(response)
        return img
    def exactImageFromResponse(self,response):
        data = response.text
        imgs = json.loads(data)["img"]
        img = self.json2img(imgs)
        return img
    def json2im(self,jstr):
        """Convert a JSON string back to a Numpy array"""
        load = json.loads(jstr)
        imdata = base64.b64decode(load['image'])
        im = pickle.loads(imdata)
        return im
                   
    #Actuation via MQTT
    def notify(self, topic, msg):
        msg = json.loads(msg)
        info = "ALERT!!Too crowded!!!"
        print(msg)
        info2 = "In "+self.zone[msg["id"]]+" ,with occupancy: "+str(msg["occupancy"])
        imMagAddr = self.camera[msg["id"]]
        photo = self.getImage(imMagAddr,msg["sequenceNum"])
        cv2.imwrite("./camera/"+str(msg["sequenceNum"])+".jpg",photo)
        if self.chat_auth!=[]:
            for chat_id in set(self.chat_auth.keys()):
                if self.chat_auth[chat_id]==True:
                    self.bot.sendMessage(chat_id, info)
                    self.bot.sendMessage(chat_id,info2)
                    self.bot.sendPhoto(chat_id,photo=open("./camera/"+str(msg["sequenceNum"])+".jpg","rb"))
        os.remove("./camera/"+str(msg["sequenceNum"])+".jpg")
        

    def on_callback_query(self,msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data  == 'Occupancy':
            self.bot.answerCallbackQuery(query_id, text='Occupancy situation is %'+self.occupancy)
        if query_data  == 'Availability':
            self.bot.answerCallbackQuery(query_id, text='Available machine:'+self.availbilaity)
        if query_data  == 'Forecast':
            self.bot.answerCallbackQuery(query_id, text='Predict')
        else:
            data_parts = query_data.split(':')  
            machine = data_parts[0] 
            switchMode = data_parts[1]
            if machine in self.machines:
                self.bot.answerCallbackQuery(query_id, text= machine + " is " + switchMode)
                self.publish(target=machine, switchTo=switchMode)
        
        
if __name__ == "__main__":
    # configFile = input("Enter the location of configuration file: ")
    # if len(configFile) == 0:
    #     configFile = "TelegramBot/configuration.json"
    configFile = "TelegramBot/configuration.json"
    telegrambot = Telegrambot(configFile)
    telegrambot.start()
    

    print('waiting ...')

# Keep the program running.
    while (True):
        if input() == 'q':
            break

    telegrambot.stop()