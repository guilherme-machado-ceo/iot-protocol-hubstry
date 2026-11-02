import { PrismaClient } from '@prisma/client'

// Única instância do Prisma Client por processo.
// Evita multiplicar pools de conexão com o PostgreSQL (um por módulo de rota).
export const prisma = new PrismaClient()

export async function disconnectPrisma(): Promise<void> {
  await prisma.$disconnect()
}
