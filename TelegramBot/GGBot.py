import requests
import telepot
import json
import datetime
import time
from MyMQTT import *
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup,InlineKeyboardMarkup, InlineKeyboardButton
from registration_functions import register_service
import cherrypy
import threading


class Telegrambot():

    def __init__(self, conf_dict):
        try:
            self.conf = conf_dict
        except:
            print("Configuration file not found")
            exit()
        self.token = self.conf["token"]
        self.bot = telepot.Bot(self.token)
        self.serviceId = self.conf["serviceId"]
        self.service_catalog_url = self.conf['service_catalog'] 
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()  # Retrieve broker and port
        self.time_slots = self.get_time_slots_from_service_catalog()
        
        self.client = MyMQTT(self.serviceId, self.mqtt_broker, self.mqtt_port, self)
        self.webServerAddr = self.conf["webServerAddress"]
        #self.__message={'service': self.serviceId,'n':'','value':'', 'timestamp':'','unit':"status"}

        self.switchTopic = self.conf["switchTopic"] 
        self.availTopic = self.conf["availTopic"]
        self.crowdTopic = self.conf["crowdTopic"] #occupancy/current
        self.overtempTopic = self.conf["overtempTopic"]
        self.predictionTopic = self.conf["predictionTopic"]
        self.mqtt_topic_control_base = self.conf["mqtt_topic_control_base"]
        self.crowdthreshold=60
        
        #Predict occupancy for each slot-hour/day combination
        self.timeslot=['8:00-10:00','10:00-12:00','12:00-14:00','14:00-16:00','16:00-18:00','18:00-20:00','20:00-22:00','22:00-24:00','24:00-8:00']
        self.weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        self.current_occupancy = 0
        
        self.user_states = {} #suggestion
        self.suggestion = []
        self.chat_auth = {} #auth id
        self.chatIDs=[] #store users chatid
        self.chat_ids = {} #map chatid for query
        self.switchMode = "None"
        self.prediction_matrix = [
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
            [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1],
            [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
            [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
            [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
            [0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        ] #example
        self.possibleSwitch =[]
        self.machines = self.conf["machines"]
        self.zones = self.conf["zones"]
        #self.current_command = {room: "ON" for room in self.rooms}  # Default command state is ON for each room
        # for zone in self.zones:
        #     temp = [zone]
        #     self.possibleSwitch.append(temp)
        self.possibleSwitch.append(["AC"])
        self.possibleSwitch.append(["Entrance"])
        self.possibleSwitch.append(["Machines"])
        
    def get_mqtt_info_from_service_catalog(self):
        """Retrieve MQTT broker and port information from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('brokerIP'), catalog.get('brokerPort')  # Return both broker IP and port
            else:
                raise Exception(f"Failed to get broker information: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting MQTT info from service catalog: {e}")
            return None, None
    def get_time_slots_from_service_catalog(self):
        """Retrieve time slots configuration from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('time_slots')
            else:
                raise Exception(f"Failed to get time slots: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving time slots from service catalog: {e}")
            return {}
            
    def start(self):
        self.client.start()
        self.client.mySubscribe(self.crowdTopic) #occupancy alert
        # subscribe to topic according to available device...not sure to subscribe
        self.client.mySubscribe(self.availTopic)
        self.client.mySubscribe(self.overtempTopic)
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
            if not message.startswith('/'):
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
        elif message == "Suggestions": #check as admin
            if self.check_auth(chat_id)==True:
                self.admin_suggestion(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "Envdata":
            if self.check_auth(chat_id)==True:
                self.admin_see_data(chat_id)
            else:
                self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
        elif message == "Operate":
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
        elif message == "Logout":
            if self.check_auth(chat_id)==True:
                del self.chat_auth[str(chat_id)]
            else:
                self.bot.sendMessage(chat_id, "You haven't logged in!")
        elif message == "Return":
            mark_up = ReplyKeyboardMarkup(keyboard=[['Occupancy'], ['Availability'],['Forecast']],one_time_keyboard=True)
            self.bot.sendMessage(chat_id, 'What would you like to know?', reply_markup=mark_up)
        elif message == "Occupancy":
            self.bot.sendMessage(chat_id, text=f"The current gym traffic is {self.current_occupancy}")
        elif message == "Availability":
            machines = self.machines
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=machine, callback_data=f"{machine}")] for machine in machines])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select your machine to see the availability:*', reply_markup=keyboard)
        elif message == "Forecast":
            mark_up = ReplyKeyboardMarkup(keyboard=[['Day'], ['Timeslot'],['Return']],one_time_keyboard=True)
            self.client.mySubscribe(self.predictionTopic)
            self.bot.sendMessage(chat_id, text='Which way would you like to forecast?', reply_markup=mark_up)
        elif message == "Day":    
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=day, callback_data=f"{day}")] for day in self.weekdays])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the day that you want to predict:*', reply_markup=keyboard)
        elif message == "Timeslot": 
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=slot, callback_data=f"{slot}")] for slot in self.timeslot])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the time slot that you want to predict:*', reply_markup=keyboard)
        elif message in list(map(str, range(16, 27))):
            self.publish(target="AC",switchTo="on:"+message)
            self.bot.sendMessage(chat_id, f"AC switched on and set {message} °C")
        else:
            if self.switchMode == "on" or self.switchMode=="off":
                if self.check_auth(chat_id) ==True:
                    for switch in self.possibleSwitch:
                        if switch[0] == message:
                            self.admin_switch(chat_id,message,self.switchMode) #message: AC,Entrance,Machines
                            self.switchMode ="None"
                            self.bot.sendMessage(chat_id, "Command sent successfully!")
                            mark_up = ReplyKeyboardMarkup(keyboard=[['Operate'], ['Envdata'],['Suggestions'],['Logout']],one_time_keyboard=True)
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
        mark_up = ReplyKeyboardMarkup(keyboard=[['Occupancy'], ['Availability'],['Forecast']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, 'What would you like to know?', reply_markup=mark_up)

    def check_auth(self,chat_id):
        try:
            if self.chat_auth[str(chat_id)]==True:
                return True
            else:
                return False
        except:
            return False
        
    def admin_message(self,chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=[['Operate'],['Envdata'],['Suggestions']],one_time_keyboard=True)
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
        mark_up = ReplyKeyboardMarkup(keyboard=[['Operate'], ['Envdata'],['Suggestions']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='What else would you like to do?', reply_markup=mark_up)
       
    def admin_operate(self, chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=[['/switchon'], ['/switchoff']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Please select your operation...', reply_markup=mark_up)
        
    def admin_switch_zone(self,chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=self.possibleSwitch, one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Please select the zone or the devices you want to switch...', reply_markup=mark_up)
    
    def publish(self,target, switchTo):
        msg = {"target":target,"switchTo":switchTo,"timestamp":str(datetime.datetime.now())}
        self.client.myPublish(self.mqtt_topic_control_base + target, msg)
        print("Published: " + json.dumps(msg))
                
    def send_hvac_command(self, room, command, mode=None):
        payload = json.dumps({
            "topic": self.mqtt_topic_control_base + room,
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "control_command": command,
                    "mode": mode
                }
            }
        })
        self.client.myPublish(self.mqtt_topic_control_base + room, payload)
        print(f"[{room}] Sent HVAC command: {command}")
    
        
    def admin_switch(self,chat_id,message,switchMode):
        if message == "AC":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=room, callback_data=f"AC:{room}:{switchMode}")] for room in self.zones])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the room to operate...*', reply_markup=keyboard)
        elif message == "Entrance": #button
            self.publish(target="entrance",switchTo=switchMode)
        elif message == "Machines":
            machines = self.machines
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=machine, callback_data=f"Machines:{machine}:{switchMode}")] for machine in machines])
            self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select your machine to operate...*', reply_markup=keyboard)
    
    def notify(self,topic,msg):
        print(msg)
        message=json.loads(msg.payload.decode('utf-8'))
        if message["topic"].startswith(self.overtempTopic):
            tosend=f"{message["message"]["data"]["alert"]}. Please check it and do some operations!"
            for chat_ID in self.chat_auth:
                keyboard = ReplyKeyboardMarkup(keyboard=[['Operate'], ['Envdata'],['Suggestions']],one_time_keyboard=True)
                self.bot.sendMessage(chat_ID, text=tosend, reply_markup=keyboard)
        elif message["topic"]==self.crowdTopic: #entrance
            self.current_occupancy = message["message"]["data"]["current_occupancy"]
            if self.current_occupancy > self.crowdthreshold:
                tosend = f"Alert! Current occupancy is reaching {self.current_occupancy}. Please consider coming another time."
                for chat_ID in self.chatIDs:
                    self.bot.sendMessage(chat_ID, text=tosend)
        elif message["topic"]==self.predictionTopic: #prediction_matrix update
            self.prediction_matrix = message["message"]["data"]["prediction_matrix"]
        elif message["topic"].startswith(self.availTopic):
            machine=message["topic"].split('/')[-1]
            data=message["message"]["data"]
            if data["available"] == 0:
                tosend=f"The machine {machine} is full, we suggest you to train something else and come later!"
                for chat_ID in self.chatIDs:
                    self.bot.sendMessage(chat_ID, text=tosend)
            else:
                chat_id = self.chat_ids.get(machine)
                if chat_id:
                    tosend = f"Situation for {machine}:\n Available num: {data["available"]}\n Occupied num: {data["busy"]}\n Total num: {data["total"]}\n"
                    self.bot.sendMessage(chat_id, tosend)
        


    def on_callback_query(self,msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data in self.machines:
            try: #choose machine
                topic = f"{self.availTopic}/{query_data}"
                self.client.mySubscribe(topic)
                # update chat_ids dict for sending users msg by query data
                self.chat_ids[query_data] = chat_id
                self.bot.sendMessage(chat_id, f"Subscribed to {query_data}!")
            except Exception as e:
                self.bot.sendMessage(chat_id, f"Failed to subscribe to {query_data}: {str(e)}")
        elif query_data in self.weekdays:
            try:
                day_index = self.weekdays.index(query_data)  # index of selected weekdays
                day_prediction = [row[day_index] for row in self.prediction_matrix]
                #self.bot.sendMessage(chat_id, f"Forecasted traffic on {query_data} is {day_prediction}!")
                tosend = f"Forecasted traffic for {query_data}:\n"
                for i, prediction in enumerate(day_prediction):
                    slot = self.timeslot[i]
                    tosend += f"{slot}: {prediction}\n"
                self.bot.sendMessage(chat_id, tosend)
            except Exception as e:
                self.bot.sendMessage(chat_id, f"Failed")
        elif query_data in self.timeslot:
            try:
                time_index = self.timeslot.index(query_data)  # index of selected timeslot
                time_prediction = self.prediction_matrix[time_index]
                #self.bot.sendMessage(chat_id, f"Forecasted traffic from Monday to Sunday during {query_data} is {time_prediction}!")
                tosend = f"Forecasted traffic for {query_data} across the week:\n"
                for i, prediction in enumerate(time_prediction):
                    day = self.weekdays[i]
                    tosend += f"{day}: {prediction}\n"

                self.bot.sendMessage(chat_id, tosend)
            except Exception as e:
                self.bot.sendMessage(chat_id, f"Failed")
        elif query_data.startswith('AC'):
            print(query_data)
            data = query_data.split(':')  
            room = data[1] 
            switchMode = data[2]
            if switchMode == 'on':
                switchMode = 'turn_on'
            else:
                switchMode = 'turn_off'
            if room in self.zones:
                self.bot.answerCallbackQuery(query_id, text= f"AC in {room} switched to {switchMode}")
                self.send_hvac_command(room,switchMode) #publish on/off
        else:
            print(query_data)
            data = query_data.split(':')  
            machine = data[1] 
            switchMode = data[2]
            if machine in self.machines:
                self.bot.answerCallbackQuery(query_id, text= machine + " is " + switchMode)
                self.publish(target=machine, switchTo=switchMode) #publish on/off

def start_cherrypy(service):
    cherrypy.config.update({'server.socket_port': 8086, 'server.socket_host': '0.0.0.0'})
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    }
    # Ensure 'service' is defined properly before this
    cherrypy.tree.mount(service, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
        
if __name__ == "__main__":
    # configFile = input("Enter the location of configuration file: ")
    # if len(configFile) == 0:
    #     configFile = "TelegramBot/configuration.json"
    configFile = "TelegramBot/configuration.json"
    with open(configFile) as config_file:
        config_dict = json.load(config_file)
        # Register the service at startup
    register_service(config_dict, config_dict["service_catalog"])    
    print("Telegram Service Initialized and Registered")
    telegrambot = Telegrambot(config_dict)
    # Start CherryPy in a separate thread
    cherrypy_thread = threading.Thread(target=start_cherrypy,args=(telegrambot,))
    cherrypy_thread.start()
    
    telegrambot.start()

    print('waiting ...')

# Keep the program running.
    while (True):
        if input() == 'q':
            break
    cherrypy.engine.exit()
    telegrambot.stop()