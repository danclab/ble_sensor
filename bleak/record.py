import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from sensor import RecordingDevice

async def main():

    print('Scanning...')

    address = None
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name == 'SENSOR_PRO':
            address = d.address
            print('SENSOR_PRO found: %s' % address)

    if address is None:
        print('SENSOR_PRO not found')
    else:
        async with BleakClient(address) as client:
            dev=RecordingDevice(client)
            await dev.enable(gyro_acc=True, temp_press=False, ambient_light=False)

            try:
                await dev.read('test.tsv')
            finally:
                await dev.disconnect()

asyncio.run(main())