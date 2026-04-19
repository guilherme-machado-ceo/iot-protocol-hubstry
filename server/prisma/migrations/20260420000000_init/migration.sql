-- CreateTable
CREATE TABLE "Device" (
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

-- CreateTable
CREATE TABLE "SensorReading" (
    "id" SERIAL NOT NULL,
    "deviceId" TEXT NOT NULL,
    "channel" INTEGER NOT NULL,
    "frequency" DOUBLE PRECISION NOT NULL,
    "value" DOUBLE PRECISION NOT NULL,
    "unit" TEXT NOT NULL DEFAULT '',
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SensorReading_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "HarmonicProtocolLog" (
    "id" SERIAL NOT NULL,
    "fundamentalFreq" DOUBLE PRECISION NOT NULL,
    "channels" TEXT NOT NULL,
    "message" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "HarmonicProtocolLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Device_deviceId_key" ON "Device"("deviceId");

-- CreateIndex
CREATE INDEX "SensorReading_deviceId_timestamp_idx" ON "SensorReading"("deviceId", "timestamp");

-- CreateIndex
CREATE INDEX "HarmonicProtocolLog_createdAt_idx" ON "HarmonicProtocolLog"("createdAt");

-- AddForeignKey
ALTER TABLE "SensorReading" ADD CONSTRAINT "SensorReading_deviceId_fkey"
    FOREIGN KEY ("deviceId") REFERENCES "Device"("deviceId")
    ON DELETE RESTRICT ON UPDATE CASCADE;
