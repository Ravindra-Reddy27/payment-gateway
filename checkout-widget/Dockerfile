# Build Stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Build the SDK (webpack)
RUN npm run build

# Serve Stage (using a simple http server for static files)
FROM node:18-alpine
WORKDIR /app
RUN npm install -g http-server
COPY --from=build /app/dist ./dist
# We serve the dist folder on port 3001
CMD ["http-server", "dist", "-p", "3001", "--cors"]