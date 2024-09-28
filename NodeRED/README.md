# NodeRED
It is a dashboard that employs Raspberry Pi's REST Web Services to retrieve data from IoT devices and visualize it. Additionally, it imports plots of environmental measurements through the use of the Thingspeak Web Services


Docker start Node-RED service: http://localhost:1880

command:
docker pull nodered/node-red #image
docker run -it -p 1880:1880 --name GGnodered nodered/node-red #run the container

store in local:
docker run -it -p 1880:1880 -v node_red_data:/data --name GGnodered nodered/node-re