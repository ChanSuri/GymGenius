FROM nodered/node-red:latest

USER root

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install --unsafe-perm --no-update-notifier --no-fund --only=production

COPY flows.json flows_cred.json settings.js ./  
COPY lib ./lib
COPY projects ./projects

USER node-red
