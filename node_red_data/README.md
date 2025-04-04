# Node-RED Dashboard for Smart Gym Monitoring

This Node-RED project provides a smart gym monitoring system that tracks real-time occupancy, environmental conditions, and historical data analysis. The system is designed with an intuitive **Dashboard** structured into three main tabs:

- **Environment**: Monitors temperature and humidity across different rooms.
- **Occupancy**: Displays real-time gym occupancy, machine availability, and future occupancy predictions.
- **History Data**: Allows users to analyze historical trends of occupancy and environmental conditions.

## Features

- **Real-time occupancy tracking**: View current gym usage and machine availability.
- **Environmental monitoring**: Track temperature and humidity in different areas.
- **Historical analysis**: Load and visualize past occupancy and environmental data.
- **Telegram Notifications**: Alerts when gym conditions exceed predefined thresholds.
- **User-defined time selection**: Select a time range to analyze historical data.

---

## Dashboard Tabs

### **1. Environment** 🌡️

This tab displays real-time **temperature** and **humidity** readings from different areas in the gym.

#### **Groups (Rooms)**:

- **Entrance**
- **lifting room**
- **Cardio room**
- **Changing room**

**Charts**:

- **Temperature (°C) per Room**
- **Humidity (%) per Room**

---

### **2. Occupancy** 🏋️‍♂️

This tab provides real-time gym occupancy and machine availability insights.

#### **Features**:

- **Current Occupancy**: Shows how many people are inside the gym.
- **Current Machines Availability**: Tracks available and occupied gym machines.
- **Occupancy Prediction**: Uses historical data to predict future gym attendance.

**Charts**:

- **Real-time Occupancy**
- **Available vs. Busy Machines**
- **Predicted Occupancy for the Next Hours**

---

### **3. History Data** 📊

This tab allows users to analyze past occupancy trends and environmental conditions.

#### **Features**:

- Select a **custom time range** to filter historical data.
- Compare temperature, humidity, and occupancy trends over time.
- Analyze **machine usage trends** based on past data.

**Charts**:

- **Temperature over Time**
- **Humidity over Time**
- **Gym Occupancy over Time**
- **Machine Usage Trends**

---

## Setup & Installation

### **1. Install Node-RED & Dependencies**

Ensure you have Node-RED installed. If not, install it using:

```bash
npm install -g node-red
```

### **2. Clone the Repository Or Using docker**

```bash
git clone https://github.com/your-repo/nodered-gym-monitoring.git
cd nodered-gym-monitoring
```

docker-compose.yml:
node_red:
    image: nodered/node-red:latest
    ports:
      - "1880:1880"
    volumes:
      - ./node_red_data:/data  #  Node-RED data
    networks:
      - gym-genius-network
    depends_on:
      - service_catalog
      - resource_catalog
    environment:
      # - NODE_RED_ENABLE_PROJECTS=true  # for project function, single project doesn't need it yet 
      - TZ=Europe/Amsterdam #Timezone

### **3. Start Node-RED**

```bash
node-red
# or directly using docker setting to open
```

By default, the dashboard will be available at:

```
http://localhost:1880/ui
```
The nodes info will be created by your own PC which is in a file named node_modules. (.gitignore)
### **4. Import the Flow or Edit extra flows**

- Open **Node-RED Editor** (`[localhost](http://127.0.0.1:1880/)`)
- Click `Import` and select the provided JSON flow file.
- Deploy the flow.

---

## **How to Use**

1. **Access the Dashboard**
   - Open a browser and navigate to `http://your-server-ip:1880/ui`.
2. **Monitor real-time data** in the `Environment` and `Occupancy` tabs.
3. **Analyze historical trends** in the `History Data` tab.
4. **Set a custom time range** to view past data.
5. **Receive alerts via Telegram** when gym conditions exceed thresholds.

---

## **Integrations**

### **Telegram Alerts** 📲

- Sends alerts if **temperature** exceeds the threshold.
- Notifies users when **occupancy is too high**.
- **Set up:** Configure your **Telegram Bot Token** in Node-RED’s global variables.

### **Thingspeak Adapter**

- Imports historical occupancy and environmental data.
- Fetches past records for analysis in the History Data tab.

---

## **Future Improvements** 🚀

- Add **machine-specific usage analytics**.
- Enhance **occupancy prediction models**.
- Implement **user authentication for dashboard access**.

📌 **Maintained by**: Shurui Chen

