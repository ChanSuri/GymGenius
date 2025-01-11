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
import calendar
import logging

logging.basicConfig(level=logging.INFO)

class Telegrambot():

    def __init__(self, conf_dict):
        self.conf = conf_dict
        self.token = self.conf["token"]
        self.bot = telepot.Bot(self.token)
        self.serviceId = self.conf["service_id"]
        self.service_catalog_url = self.conf['service_catalog'] 
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()  # Retrieve broker and port

        self.client = MyMQTT(self.serviceId, self.mqtt_broker, self.mqtt_port, self)
        self.webServerAddr = self.conf["webServerAddress"]
        self.device_connector = self.conf["device_connector"]
        #self.__message={'service': self.serviceId,'n':'','value':'', 'timestamp':'','unit':"status"}
        
        #publish
        self.publishedTopic = self.conf["published_topics"]
        self.switchTopic = self.publishedTopic["switchTopic"] 
        self.tempTopic = self.publishedTopic["TempTopic"] #send temperature, NEED directly get temp&humidity from device in env data  
        self.subscribed_topics = self.conf["subscribed_topics"]
        self.crowdTopic = self.subscribed_topics["crowdTopic"] 
        self.availTopic = self.subscribed_topics["availTopic"]
        self.overtempTopic = self.subscribed_topics["overtempTopic"]
        self.predictionTopic = self.subscribed_topics["predictionTopic"]
        
        self.crowdthreshold=30
        
        #Predict occupancy for each slot-hour/day combination
        self.timeslot=self.get_time_slots_from_service_catalog()
        self.weekdays=list(calendar.day_name)
        self.current_occupancy = 0
        
        self.user_states = {} #suggestion state
        self.suggestion = [] #suggestion context
        self.chat_auth = {} #auth id
        self.chatIDs=[] #store users chatid
        self.chat_ids = {} #map chatid for query
        self.switchMode = "None"
        self.ACMode = "None"
        self.prediction_matrix = [
            [42, 43, 31, 38, 46, 59, 54],  # 08:00-10:00
            [19, 25, 21, 28, 16, 34, 28],  # 10:00-12:00
            [9,  7,  6, 14,  9, 28, 24],   # 12:00-14:00
            [7,  9,  6,  6, 15, 21, 23],   # 14:00-16:00
            [13, 6, 10, 11, 10, 28, 25],   # 16:00-18:00
            [31, 42, 40, 39, 41, 52, 32],   # 18:00-20:00
            [5,  7, 17,  5, 20, 22, 25],    # 20:00-22:00
            [15, 7, 11, 12, 12, 26, 39],    # 22:00-24:00
            [0,  0,  2,  4,  3, 15,  9]     # 00:00-08:00
        ] #example #example
        self.machines = self.get_machines_from_service_catalog()
        self.zones = self.get_rooms_from_service_catalog() or [] 
        self.zones.append('All')
        #self.bot.message_loop(self.on_chat_message)

    
    #get info from service catalog   
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
        
    def get_rooms_from_service_catalog(self):
        """Retrieve rooms from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('roomsID')  # Return the list of room IDs
            else:
                raise Exception(f"Failed to get room information: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting room info from service catalog: {e}")
            return []  
    
    def get_machines_from_service_catalog(self):
        """Retrieve machine types from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            response.raise_for_status()  # 检查响应状态码
            service_catalog = response.json()
            
            # 提取机器ID列表
            machines_list = service_catalog.get('catalog', {}).get('machinesID', [])

            # 使用集合推导式创建机器类型集合
            machines_type = {machine_id.rsplit('_', 1)[0] for machine_id in machines_list}
            machines_type.add("All")
            # 返回排序后的机器类型列表
            return sorted(machines_type)

        except requests.exceptions.RequestException as e:
            print(f"Error getting machine types from service catalog: {e}")
            return []
        
    #MQTT        
    def start(self):
        self.client.start()
        try:
            for topic_key, topic_value in self.conf["subscribed_topics"].items():
                self.client.mySubscribe(topic_value)
                print(f"Subscribed to topic: {topic_key}")
            MessageLoop(self.bot,{'chat': self.on_chat_message,'callback_query': self.on_callback_query}).run_as_thread()
        except KeyError as e:
            print(f"Error in subscribed_topics format: {e}")
        
    def stop(self):
        self.workingStatus = False
        self.client.stop()
    
    
    #Telegram chat
    def on_chat_message(self,msg):
        try:
            # if 'text' in msg:
            #     content_type, chat_type, chat_id = telepot.glance(msg)
            #     message = msg['text']
            # elif 'data' in msg:  # 当按钮被点击时，msg会包含callback_data
            #     content_type, chat_type, chat_id = telepot.glance(msg['message'])
            #     message = msg['data']
            content_type, chat_type, chat_id = telepot.glance(msg)
            message = msg['text']
            print(content_type, chat_type, chat_id)
            self.chatIDs.append(chat_id)
            if chat_id in self.user_states and self.user_states[chat_id] != None:
                if self.user_states[chat_id] == 'awaiting_suggestion':
                    if message == "quit":
                        self.bot.sendMessage(chat_id, 'What do you want to know about us? [/knowus]')
                    else:
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with open("TelegramBot/suggestions.txt", "a") as file:
                            file.write(f"{current_time} | {chat_id} | {message}\n")
                        self.bot.sendMessage(chat_id, "Your suggestion is saved! Thank you.")
                    self.user_states[chat_id] = None
                elif self.user_states[chat_id] == "choosing_zone":
                    if message in self.zones:
                        self.user_states[chat_id] = None  # 清除状态
                        self.fetch_data(chat_id, message)  # 调用处理函数
                    else:
                        self.bot.sendMessage(chat_id, "Invalid selection. Please try again.")
                    return
            elif message ==  "/start":
                self.bot.sendMessage(chat_id, 'Welcome to GymGenius! You can start your incredible experience here!')
            elif message == '/knowus':
                self.bot.sendMessage(chat_id, 'The IoT application Gym Genius is intended to optimize gym management, improve customer satisfaction, and guarantee optimal utilization of resources. It employs automated mechanisms, a variety of sensors, and a Telegram bot to facilitate user interaction.')
            elif message == "/suggestion": #write as client
                self.user_states[chat_id] = 'awaiting_suggestion'
                mark_up = ReplyKeyboardMarkup(keyboard=[['quit']],one_time_keyboard=True)
                self.bot.sendMessage(chat_id, 'Please enter your suggestion:', reply_markup=mark_up)
            elif message == "/login":
                self.initial_message(chat_id)
            elif message == "Client":
                self.user_message(chat_id)
            elif message == "Administrator":
                self.chat_auth[str(chat_id)]=False
                self.bot.sendMessage(chat_id, 'Please enter the password')
            elif message == "Suggestions": #check as admin
                if self.check_auth(chat_id)==True:
                    self.admin_suggestion(chat_id)
                else:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
            elif message == "Envdata":
                if self.check_auth(chat_id)==True:
                    self.admin_env_zone(chat_id)
                else:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
            elif message == "Control":
                if self.check_auth(chat_id)==True:
                    self.admin_operate(chat_id)
                else:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
            elif message == "cool" or message == "heat":
                if self.check_auth(chat_id)==True:
                    self.switchMode ="turn_on"
                    self.ACMode = message
                    self.admin_switch_zone(chat_id)
                else:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
            elif message == "Switchon":
                if self.check_auth(chat_id)==True:
                    mark_up = ReplyKeyboardMarkup(keyboard=[['cool'], ['heat']],one_time_keyboard=True)
                    self.bot.sendMessage(chat_id, 'Which AC mode to set?', reply_markup=mark_up)
                else:
                    self.bot.sendMessage(chat_id, "Please send '/administrator' to login first!")
            elif message == "Switchoff":
                if self.check_auth(chat_id)==True:
                    self.switchMode="turn_off"
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
                # rooms = self.zones
                # keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=room, callback_data=f"{room}")] for room in rooms])
                # self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the room to see the Occupancy:*', reply_markup=keyboard)
                self.bot.sendMessage(chat_id, text=f"The current gym traffic is {self.current_occupancy}")
                mark_up = ReplyKeyboardMarkup(keyboard=[['Occupancy'], ['Availability'],['Forecast']],one_time_keyboard=True)
                self.bot.sendMessage(chat_id, 'What else would you like to know?', reply_markup=mark_up)
            elif message == "Availability":
                machines = self.machines
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=machine, callback_data=f"{machine}")] for machine in machines])
                self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select your machine to see the availability:*', reply_markup=keyboard)
            elif message == "Forecast":
                # rooms = self.zones
                # keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=room, callback_data=f"{room}")] for room in rooms])
                # self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the room to predict:*', reply_markup=keyboard)
                mark_up = ReplyKeyboardMarkup(keyboard=[['Day'], ['Timeslot'],['Return']],one_time_keyboard=True)
                self.client.mySubscribe(self.conf["subscribed_topics"]['predictionTopic']) #NEED TO CORRECT
                self.bot.sendMessage(chat_id, text='Which way would you like to forecast?', reply_markup=mark_up)
            elif message == "Day":    
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=day, callback_data=f"{day}")] for day in self.weekdays])
                self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the day that you want to predict:*', reply_markup=keyboard)
            elif message == "Timeslot": 
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{slot['start']} - {slot['end']}", callback_data=key)] for key, slot in self.timeslot.items()])
                self.bot.sendMessage(chat_id, parse_mode='Markdown',text='*Please select the time slot that you want to predict:*', reply_markup=keyboard)
            else:
                if self.switchMode == "turn_on" or self.switchMode=="turn_off":
                    if self.check_auth(chat_id) ==True:
                        if message in self.zones:
                            self.bot.sendMessage(chat_id, text= f"AC in {message} switched to {self.switchMode} in mode {self.ACMode}")
                            self.send_hvac_command(message,self.switchMode,self.ACMode) #publish on/off
                            self.switchMode ="None"
                            self.ACMode ="None"
                            self.bot.sendMessage(chat_id, "Command sent successfully!")
                            mark_up = ReplyKeyboardMarkup(keyboard=[['Control'], ['Envdata'],['Suggestions'],['Logout']],one_time_keyboard=True)
                            self.bot.sendMessage(chat_id, text='What would you like to do next?', reply_markup=mark_up)
                            return
                        self.bot.sendMessage(chat_id, 'Please enter the correct command!')
                    else:
                        self.bot.sendMessage(chat_id, "Please send 'Administrator' to login first!")
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
                        self.bot.sendMessage(chat_id, "Please send 'Administrator' to login !")
        except Exception as e:
            logging.error(f"Error handling message: {e}", exc_info=True)
            self.bot.sendMessage(chat_id, "An error occurred in handling message. Please try again later.")
                    
            
    def initial_message(self,chat_id):
        # design as reply keyboard
        mark_up = ReplyKeyboardMarkup(keyboard=[['Client'], ['Administrator']],one_time_keyboard=True)
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
        mark_up = ReplyKeyboardMarkup(keyboard=[['Control'],['Envdata'],['Suggestions']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Login success!', reply_markup=mark_up)

    def admin_suggestion(self,chat_id):
        with open("TelegramBot/suggestions.txt", "r") as file:
            for line in file:
                self.bot.sendMessage(chat_id, text=line.strip())

    def admin_see_data(self,chat_id,room):
        # check if the room in device_connector
        if room not in self.device_connector:
            self.bot.sendMessage(chat_id, f"Room '{room}' not configured.")
            return
        device_connector_url = self.device_connector[room] + "/environment"
        # from Device Connector get data
        response = requests.get(device_connector_url) 
        if response.status_code == 200:
            data = response.json()  # Assume JSON response with "temperature" and "humidity" keys
            senml_record = data.get("senml_record", {})
            if 'e' in senml_record and data.get("location", {}) == room:
                temperature = next((e["v"] for e in senml_record["e"] if e["n"] == "temperature"), None)
                humidity = next((e["v"] for e in senml_record["e"] if e["n"] == "humidity"), None)

                if temperature is not None or humidity is not None:
                    if isinstance(temperature, dict):
                        temperature = next(iter(temperature.values()))
                    if isinstance(humidity, dict):
                        humidity = next(iter(humidity.values()))
                    self.bot.sendMessage(chat_id, f"Room <{room}> current environment:\n Temperature: {temperature}°C \n Humidity: {humidity}%\n")
                else:
                    self.bot.sendMessage(chat_id, "Unable to fetch the environment data.")
            mark_up = ReplyKeyboardMarkup(keyboard=[['Control'], ['Envdata'],['Suggestions']],one_time_keyboard=True)
            self.bot.sendMessage(chat_id, text='What else would you like to do?', reply_markup=mark_up)
        else:
            raise Exception(f"Failed to fetch data from DeviceConnector: {response.status_code}")
    
    def admin_operate(self, chat_id):
        mark_up = ReplyKeyboardMarkup(keyboard=[['Switchon'], ['Switchoff']],one_time_keyboard=True)
        self.bot.sendMessage(chat_id, text='Please select your operation for HVAC...', reply_markup=mark_up)
        
    def admin_switch_zone(self,chat_id):
        mark_up = ReplyKeyboardMarkup(
            keyboard=[[room] for room in self.zones],
            one_time_keyboard=True
        )
        self.bot.sendMessage(chat_id, text='Please select the zone you want to switch...', reply_markup=mark_up)
    def admin_env_zone(self,chat_id):
        mark_up = ReplyKeyboardMarkup(
            keyboard=[[room] for room in self.zones],
            one_time_keyboard=True
        )
        self.bot.sendMessage(chat_id, text='Please select the zone you want to check environment...', reply_markup=mark_up)
        self.user_states[chat_id] = "choosing_zone"
        
    def fetch_data(self, chat_id, room):
        # 处理房间选择后的逻辑
        self.bot.sendMessage(chat_id, f"You selected '{room}'. Fetching data...")
        self.admin_see_data(chat_id, room)  # 调用查看数据函数
            
    def send_hvac_command(self, room, command, mode=None):
        if room == "All":
            room = "#"
        payload = json.dumps({
            "topic": self.switchTopic + room, #gym/hvac/on_off/#
            "message": {
                "device_id": "Temperature control",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "control_command": command,
                    "mode": mode
                }
            }
        })
        self.client.myPublish(self.switchTopic + room, payload)
        print(f"[{room}] Sent HVAC command: {command} with mode {mode}")
        
    #self.notifier.notify (msg.topic, msg.payload)
    def notify(self, topic, msg):
        print(msg)
        try:
            message = json.loads(msg.decode('utf-8'))  # Decode and parse the JSON message
            
            if topic.startswith(self.overtempTopic):
                room = topic.split('/')[-1]
                alert_message = message["message"]["data"]["alert"]
                tosend = f'{alert_message}. Please check it and do some operations in {room}!'
                for chat_ID in self.chat_auth:
                    keyboard = ReplyKeyboardMarkup(keyboard=[['Control'], ['Envdata'], ['Suggestions']], one_time_keyboard=True)
                    self.bot.sendMessage(chat_ID, text=tosend, reply_markup=keyboard)

            elif topic == self.crowdTopic:
                self.current_occupancy = message["message"]["data"]["current_occupancy"]
                if self.current_occupancy > self.crowdthreshold:
                    tosend = f"Alert! Current occupancy is reaching {self.current_occupancy}. Please consider coming another time."
                    for chat_ID in self.chatIDs:
                        self.bot.sendMessage(chat_ID, text=tosend)

            elif topic == self.predictionTopic:
                self.prediction_matrix = message["message"]["data"]["prediction_matrix"]

            elif topic.startswith(self.availTopic):
                machine = topic.split('/')[-1]
                if machine == "#":
                    machine = "ALL"
                data = message["message"]["data"]
                if data["available"] == 0:
                    tosend = f"{machine} machine is full, we suggest you to train something else and come later!"
                    for chat_ID in self.chatIDs:
                        self.bot.sendMessage(chat_ID, text=tosend)
                else:
                    chat_id = self.chat_ids.get(machine)
                    if chat_id:
                        tosend = (
                            f"Situation for {machine} machine:\n"
                            f"Available num: {data['available']}\n"
                            f"Occupied num: {data['busy']}\n"
                            f"Total num: {data['total']}\n"
                        )
                        self.bot.sendMessage(chat_id, tosend)

        except Exception as e:
            print(f"Error processing message: {e}")

            


    def on_callback_query(self,msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data in self.machines:
            try: #choose machine: gym/availability/<machineID>
                # update chat_ids dict for sending users msg by query data
                self.chat_ids[query_data] = chat_id
                if query_data == "All":
                    query_data = "#"
                topic = f"{self.availTopic}/{query_data}"
                self.client.mySubscribe(topic)
                self.bot.sendMessage(chat_id, f"Subscribed to availability of {query_data.replace('#', 'All')}!")
            except Exception as e:
                self.bot.sendMessage(chat_id, f"Failed to subscribe to {query_data}: {str(e)}")
        elif query_data in self.weekdays:
            try:
                day_index = self.weekdays.index(query_data)  # index of selected weekdays
                day_prediction = [row[day_index] for row in self.prediction_matrix]
                #self.bot.sendMessage(chat_id, f"Forecasted traffic on {query_data} is {day_prediction}!")
                tosend = f"Forecasted traffic for {query_data}:\n"
                for key, prediction in zip(self.timeslot.keys(), day_prediction):
                    slot = self.timeslot[key]  # Get the time slot using the key
                    tosend += f"{slot['start']} - {slot['end']}: {prediction}\n"  # Format the message
                self.bot.sendMessage(chat_id, tosend)
            except Exception as e:
                self.bot.sendMessage(chat_id, f"Failed")
        elif query_data in map(str, range(9)): 
            try:
                #time_index = self.timeslot.index(query_data)  # index of selected timeslot
                time_prediction = self.prediction_matrix[int(query_data)]
                #self.bot.sendMessage(chat_id, f"Forecasted traffic from Monday to Sunday during {query_data} is {time_prediction}!")
                tosend = f"Forecasted traffic for timeslot between {self.timeslot[query_data]} across the week:\n"
                for i, prediction in enumerate(time_prediction):
                    day = self.weekdays[i]
                    tosend += f"{day}: {prediction}\n"

                self.bot.sendMessage(chat_id, tosend)
            except Exception as e:
                self.bot.sendMessage(chat_id, f"Failed")
                
def start_cherrypy(telegrambot):
    cherrypy.config.update({'server.socket_port': 8086, 'server.socket_host': '0.0.0.0'})
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
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
    configFile = "teleconfig.json"
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
