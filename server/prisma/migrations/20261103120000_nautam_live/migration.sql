-- Nautam Live (E1): migração puramente aditiva.

-- CreateTable
CREATE TABLE "LiveRun" (
    "id" SERIAL NOT NULL,
    "slotUtc" TIMESTAMP(3) NOT NULL,
    "status" TEXT NOT NULL,
    "sources" TEXT[],
    "newObservations" INTEGER NOT NULL DEFAULT 0,
    "sourceObservedAt" TIMESTAMP(3),
    "expectedChannels" JSONB,
    "decodedPeaks" JSONB,
    "metrics" JSONB,
    "mqttBaseline" JSONB,
    "noiseSeed" TEXT,
    "requestedSnrDb" DOUBLE PRECISION,
    "measuredSnrDb" DOUBLE PRECISION,
    "errorCode" TEXT,
    "errorDetail" TEXT,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" TIMESTAMP(3),

    CONSTRAINT "LiveRun_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LiveObservation" (
    "id" SERIAL NOT NULL,
    "provider" TEXT NOT NULL,
    "stationRef" TEXT NOT NULL,
    "sensorRef" TEXT NOT NULL,
    "parameter" TEXT NOT NULL,
    "value" DOUBLE PRECISION NOT NULL,
    "unit" TEXT NOT NULL,
    "observedAt" TIMESTAMP(3) NOT NULL,
    "ingestedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "firstRunId" INTEGER,
    "locality" TEXT,
    "licenseName" TEXT NOT NULL,
    "licenseUrl" TEXT NOT NULL,
    "attribution" TEXT NOT NULL,
    "sourceUrl" TEXT NOT NULL,

    CONSTRAINT "LiveObservation_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "LiveRun_slotUtc_key" ON "LiveRun"("slotUtc");

-- CreateIndex
CREATE INDEX "LiveRun_status_slotUtc_idx" ON "LiveRun"("status", "slotUtc");

-- CreateIndex
CREATE INDEX "LiveRun_completedAt_idx" ON "LiveRun"("completedAt");

-- CreateIndex
CREATE INDEX "LiveObservation_parameter_observedAt_idx" ON "LiveObservation"("parameter", "observedAt");

-- CreateIndex
CREATE INDEX "LiveObservation_observedAt_idx" ON "LiveObservation"("observedAt");

-- CreateIndex
CREATE UNIQUE INDEX "LiveObservation_provider_sensorRef_observedAt_key" ON "LiveObservation"("provider", "sensorRef", "observedAt");
