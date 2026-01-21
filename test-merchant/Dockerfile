FROM node:18-alpine

WORKDIR /app

# Initialize a package.json if one doesn't exist (simulates a real project)
RUN npm init -y

# Install express (required for the receiver script)
RUN npm install express body-parser

# Copy the script
COPY webhook-receiver.js .

# Expose the port
EXPOSE 4000

# Run the script
CMD ["node", "webhook-receiver.js"]