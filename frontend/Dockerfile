# frontend/Dockerfile

########## Build stage ##########
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* yarn.lock* ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

########## Run stage (Nginx) ##########
FROM nginx:alpine

# Copy built React app to Nginx html directory
COPY --from=build /app/build /usr/share/nginx/html

# Optional: custom nginx.conf could go here if needed
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
