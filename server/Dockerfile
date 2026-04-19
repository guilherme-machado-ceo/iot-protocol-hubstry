FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npx prisma generate && npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3001
RUN addgroup -g 1001 -S nodejs && adduser -S harmonic -u 1001
COPY --from=builder --chown=harmonic:nodejs /app/dist ./dist
COPY --from=builder --chown=harmonic:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=harmonic:nodejs /app/prisma ./prisma
COPY --from=builder --chown=harmonic:nodejs /app/package.json ./
USER harmonic
EXPOSE 3001
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://localhost:3001/api/health > /dev/null || exit 1
CMD ["sh", "-c", "npx --no-install prisma migrate deploy && node dist/index.js"]
