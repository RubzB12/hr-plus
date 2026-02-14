# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY apps/public-careers/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY apps/public-careers .

# Build Next.js application
RUN npm run build

# ============================================================================
# Stage 2: Runner
# ============================================================================
FROM node:20-alpine

WORKDIR /app

# Install dumb-init to handle process signals properly
RUN apk add --no-cache dumb-init

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Copy built application from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set NODE_ENV to production
ENV NODE_ENV=production

# Use dumb-init to properly handle process signals
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "server.js"]
