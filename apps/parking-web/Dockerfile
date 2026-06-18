FROM node:22-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Set dynamic build arguments for Vite
ARG VITE_API_URL
ARG VITE_GATEWAY_WS_URL

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_GATEWAY_WS_URL=$VITE_GATEWAY_WS_URL

RUN npm run build

EXPOSE 3000

# Run in preview mode on port 3000 (Vite configuration already sets the port to 3000)
CMD ["npm", "run", "preview"]
