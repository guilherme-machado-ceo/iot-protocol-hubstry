FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3000
RUN addgroup -g 1001 -S nodejs && adduser -S harmonic -u 1001
COPY --from=builder --chown=harmonic:nodejs /app/.next/standalone ./
COPY --from=builder --chown=harmonic:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=harmonic:nodejs /app/public ./public
USER harmonic
EXPOSE 3000
CMD ["node", "server.js"]
