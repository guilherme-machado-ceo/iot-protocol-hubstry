-- Harmonic IoT Protocol — initial schema
-- Applied automatically by PostgreSQL on first container start
-- Mirrors server/prisma/migrations/20260420000000_init/migration.sql

CREATE TABLE IF NOT EXISTS "Device" (
    "id" SERIAL NOT NULL,
    "deviceId" TEXT NOT NULL,
    "deviceType" TEXT NOT NULL DEFAULT 'generic',
    "fundamentalFreq" DOUBLE PRECISION NOT NULL DEFAULT 1000,
    "sensors" TEXT NOT NULL DEFAULT '[]',
    "harmonicChannels" TEXT NOT NULL DEFAULT '{}',
    "capabilities" TEXT NOT NULL DEFAULT '[]',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastSeen" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Device_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "SensorReading" (
    "id" SERIAL NOT NULL,
    "deviceId" TEXT NOT NULL,
    "channel" INTEGER NOT NULL,
    "frequency" DOUBLE PRECISION NOT NULL,
    "value" DOUBLE PRECISION NOT NULL,
    "unit" TEXT NOT NULL DEFAULT '',
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "SensorReading_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "HarmonicProtocolLog" (
    "id" SERIAL NOT NULL,
    "fundamentalFreq" DOUBLE PRECISION NOT NULL,
    "channels" TEXT NOT NULL,
    "message" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "HarmonicProtocolLog_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "Device_deviceId_key" ON "Device"("deviceId");
CREATE INDEX IF NOT EXISTS "SensorReading_deviceId_timestamp_idx" ON "SensorReading"("deviceId", "timestamp");
CREATE INDEX IF NOT EXISTS "HarmonicProtocolLog_createdAt_idx" ON "HarmonicProtocolLog"("createdAt");

ALTER TABLE "SensorReading"
    ADD CONSTRAINT IF NOT EXISTS "SensorReading_deviceId_fkey"
    FOREIGN KEY ("deviceId") REFERENCES "Device"("deviceId")
    ON DELETE RESTRICT ON UPDATE CASCADE;
