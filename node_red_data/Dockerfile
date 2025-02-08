FROM nodered/node-red

WORKDIR /app

COPY . .

RUN npm install node-red-dashboard
RUN -e TELEGRAM_BOT_TOKEN="6961607644:AAGN_aC1t3TjkkuiuR9FAHM53fAFgj-OkPw" -p 1880:1880 nodered/node-red

