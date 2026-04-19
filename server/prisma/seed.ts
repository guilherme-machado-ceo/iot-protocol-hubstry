import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()
const isPerformanceSeed = process.argv.includes('--performance')

async function main() {
  console.log('Seeding database...')

  // Seed demo devices
  const devices = [
    {
      deviceId: 'rpi_demo_001',
      deviceType: 'raspberry_pi',
      fundamentalFreq: 1000,
      sensors: JSON.stringify(['temp_sensor', 'humidity_sensor']),
      harmonicChannels: JSON.stringify({ 3: 'temp_sensor', 4: 'humidity_sensor' }),
      capabilities: JSON.stringify(['harmonic_communication', 'sensor_reading', 'fft_processing']),
    },
    {
      deviceId: 'rpi_demo_002',
      deviceType: 'raspberry_pi',
      fundamentalFreq: 1000,
      sensors: JSON.stringify(['led_actuator']),
      harmonicChannels: JSON.stringify({ 5: 'led_actuator' }),
      capabilities: JSON.stringify(['harmonic_communication', 'actuator_control']),
    },
  ]

  for (const device of devices) {
    await prisma.device.upsert({
      where: { deviceId: device.deviceId },
      update: device,
      create: device,
    })
  }

  console.log(`Seeded ${devices.length} devices`)

  // Performance seed: add bulk sensor readings
  if (isPerformanceSeed) {
    console.log('Seeding performance data...')
    const readings = []
    const now = Date.now()

    for (let i = 0; i < 10000; i++) {
      readings.push({
        deviceId: 'rpi_demo_001',
        channel: (i % 2 === 0) ? 3 : 4,
        frequency: (i % 2 === 0) ? 3000 : 4000,
        value: 20 + Math.random() * 10,
        unit: (i % 2 === 0) ? 'celsius' : 'percent',
        timestamp: new Date(now - i * 1000),
      })
    }

    await prisma.sensorReading.createMany({ data: readings, skipDuplicates: true })
    console.log(`Seeded ${readings.length} sensor readings`)
  }
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(() => prisma.$disconnect())
