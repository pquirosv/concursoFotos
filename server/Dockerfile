FROM node:18-alpine

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm ci

COPY server ./server

EXPOSE 3000

CMD ["npm", "run", "dev"]
