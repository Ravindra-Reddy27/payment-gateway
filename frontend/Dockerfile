# Build Stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve Stage
FROM nginx:alpine
# 1. Copy the build output
COPY --from=build /app/dist /usr/share/nginx/html

# 2. COPY THE CUSTOM NGINX CONFIG (This fixes the 404)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]