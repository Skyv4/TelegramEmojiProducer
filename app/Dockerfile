# Use an official Node.js runtime as a parent image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm

# Copy package.json and pnpm-lock.yaml for pnpm install
COPY package.json ./
COPY pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy the rest of the application code
COPY . .

COPY ./first_frame.png ./public/first_frame.png

# Expose port 3000
EXPOSE 3000

# Command to run the application (specified in docker-compose.yml)
# CMD ["pnpm", "dev"]
