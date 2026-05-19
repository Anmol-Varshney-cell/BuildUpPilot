FROM node:20-alpine
WORKDIR /app
RUN apk add --no-cache docker-cli
COPY package.json package-lock.json* ./
RUN npm install
COPY tsconfig.json ./
COPY src ./src
EXPOSE 5001
CMD ["npm", "run", "dev"]
