FROM nodered/node-red:latest

USER root

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install --unsafe-perm --no-update-notifier --no-fund --only=production

COPY projects/GymGenius/flows.json ./projects/GymGenius/flows.json
COPY projects/GymGenius/flows_cred.json ./projects/GymGenius/flows_cred.json

COPY settings.js ./settings.js
COPY lib ./lib
COPY projects ./projects

USER node-red
