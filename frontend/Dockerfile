# =============================================================
# Loriaa AI Frontend - Dockerfile
# React + Vite Development
# =============================================================

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Default command for development
CMD ["yarn", "dev", "--host", "0.0.0.0", "--port", "3000"]
