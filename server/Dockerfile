# API do Nautam IoT Protocol (Fastify + Prisma + PostgreSQL)
# Contexto de build: a pasta server/
#   docker build -f server/Dockerfile --target runtime -t nautam-api server/
#   docker build -f server/Dockerfile --target migrate -t nautam-migrate server/
#
# Alvos:
#   runtime -> imagem da API, só com dependências de execução
#   migrate -> tarefa avulsa do ECS que roda "prisma migrate deploy" dentro da VPC

ARG NODE_IMAGE=node:24-bookworm-slim

# ---------------------------------------------------------------------------
# Base com OpenSSL, exigido pelos engines do Prisma
# ---------------------------------------------------------------------------
FROM ${NODE_IMAGE} AS base
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# ---------------------------------------------------------------------------
# Build: dependências completas, Prisma Client e compilação TypeScript
# ---------------------------------------------------------------------------
FROM base AS build
COPY package.json package-lock.json ./
RUN npm ci
COPY prisma ./prisma
RUN npx prisma generate
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# ---------------------------------------------------------------------------
# Dependências de produção (sem TypeScript, Prisma CLI, Vitest etc.)
# ---------------------------------------------------------------------------
FROM base AS prod-deps
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

# ---------------------------------------------------------------------------
# Migração: dependências de produção + só o Prisma CLI e seus engines.
# Não leva o node_modules de build: ferramentas de teste e compilação
# (vitest, tsx, esbuild, typescript) ficam fora da imagem.
# ---------------------------------------------------------------------------
FROM base AS migrate
ENV NODE_ENV=production
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/node_modules/prisma ./node_modules/prisma
COPY --from=build /app/node_modules/@prisma ./node_modules/@prisma
COPY prisma ./prisma
COPY package.json ./
USER node
CMD ["node", "node_modules/prisma/build/index.js", "migrate", "deploy"]

# ---------------------------------------------------------------------------
# Runtime da API
# ---------------------------------------------------------------------------
FROM base AS runtime
ENV NODE_ENV=production \
    PORT=3001 \
    HOST=0.0.0.0
COPY --from=prod-deps /app/node_modules ./node_modules
# Prisma Client gerado no estágio de build (código + engine nativo)
COPY --from=build /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=build /app/dist ./dist
COPY prisma/schema.prisma ./prisma/schema.prisma
COPY package.json ./
USER node
EXPOSE 3001
CMD ["node", "dist/index.js"]
