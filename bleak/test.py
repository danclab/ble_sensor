import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from sensor import GyroAccelSensor, TempPressureSensor, AmbientLightSensor
import matplotlib.pyplot as plt
import numpy as np
import datetime

IO_SAMP_CHAR_UUID = "6a80ff0c-b5a3-f393-e0a9-e50e24dcca9e"

async def main():
    address=None
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name=='SENSOR_PRO':
            address=d.address
            print('SENSOR_PRO found: %s' % address)

    if address is None:
        print('SENSOR_PRO not found')
    else:
        async with BleakClient(address) as client:
            # Set sampling rate to 100
            print('Setting sampling rate')
            write_value = b"\x00\x64"
            value = await client.read_gatt_char(IO_SAMP_CHAR_UUID)
            await client.write_gatt_char(IO_SAMP_CHAR_UUID, write_value)
            value = await client.read_gatt_char(IO_SAMP_CHAR_UUID)
            assert value == write_value

            gyro_acc = GyroAccelSensor(client)
            await gyro_acc.enable()
            temp_pres = TempPressureSensor(client)
            await temp_pres.enable()
            prox = AmbientLightSensor(client)
            await prox.enable()

            gyro_data = np.zeros((3, 100))
            accel_data = np.zeros((3, 100))
            ang_data = np.zeros((3, 100))
            temp_data = np.zeros((1, 100))
            press_data = np.zeros((1, 100))
            light_data = np.zeros((1, 100))

            plt.subplot(3, 2, 1)
            g_h1, = plt.plot(gyro_data[0, :])
            g_h2, = plt.plot(gyro_data[1, :])
            g_h3, = plt.plot(gyro_data[2, :])
            plt.ylim(-250, 250)
            plt.legend(['gyro x', 'gyro y', 'gyro z'])

            plt.subplot(3, 2, 2)
            a_h1, = plt.plot(accel_data[0, :])
            a_h2, = plt.plot(accel_data[1, :])
            a_h3, = plt.plot(accel_data[2, :])
            plt.ylim(-2, 2)
            plt.legend(['acc x', 'acc y', 'acc z'])

            t_plt = plt.subplot(3, 2, 3)
            t_h1, = plt.plot(temp_data[0, :])
            plt.ylim(19.36, 19.38)
            plt.legend(['temp'])
            p_plt = plt.subplot(3, 2, 4)

            p_h1, = plt.plot(press_data[0, :])
            plt.ylim(28, 35)
            plt.legend(['pressure'])
            l_plt = plt.subplot(3, 2, 5)
            l_h1, = plt.plot(light_data[0, :])
            plt.ylim(0, 5000)
            plt.legend(['light'])
            plt.draw()

            angle = np.zeros((3, 1))
            last_t = datetime.datetime.now()

            gyroX = 0
            gyroY = 0
            yaw = 0
            while True:
                (gyro, accel) = await gyro_acc.read()
                (temp, press) = await temp_pres.read()
                light = await prox.read()
                t = datetime.datetime.now()
                dt = t - last_t
                # accX=(math.atan(accel[1]/math.sqrt(math.pow(accel[0],2)+math.pow(accel[2],2)))*180/math.pi)+3.56
                # accY=(math.atan(-1*accel[0]/math.sqrt(math.pow(accel[1],2)+math.pow(accel[2],2)))*180/math.pi)+3.77
                # gyroX=(gyroX+1.211)+gyro[0]*dt.total_seconds()
                # gyroY=(gyroY-0.291)+gyro[1]*dt.total_seconds()
                # yaw=(yaw-0.165)+gyro[2]*dt.total_seconds()
                # roll=0.96*gyroX+0.04*accX
                # pitch=0.96*gyroY+0.04*accY
                # angle=np.array([roll,pitch,yaw])

                # gyro=2*np.random.randn(3,1)
                # accel = 1*np.random.randn(3, 1)

                gyro_data[:, 0:-1] = gyro_data[:, 1:]
                gyro_data[:, -1] = gyro

                accel_data[:, 0:-1] = accel_data[:, 1:]
                accel_data[:, -1] = accel

                # ang_data[:, 0:-1] = ang_data[:, 1:]
                # ang_data[:, -1] = angle[:,[0]]

                temp_data[:, 0:-1] = temp_data[:, 1:]
                temp_data[:, -1] = temp

                press_data[:, 0:-1] = press_data[:, 1:]
                press_data[:, -1] = press

                light_data[:, 0:-1] = light_data[:, 1:]
                light_data[:, -1] = light

                g_h1.set_ydata(gyro_data[0, :])
                g_h2.set_ydata(gyro_data[1, :])
                g_h3.set_ydata(gyro_data[2, :])
                a_h1.set_ydata(accel_data[0, :])
                a_h2.set_ydata(accel_data[1, :])
                a_h3.set_ydata(accel_data[2, :])
                # ang_h1.set_ydata(ang_data[0, :])
                # ang_h2.set_ydata(ang_data[1, :])
                # ang_h3.set_ydata(ang_data[2, :])
                t_h1.set_ydata(temp_data[0, :])
                t_plt.set_ylim(np.min(temp_data) - np.std(temp_data) / 2, np.max(temp_data) + np.std(temp_data) / 2)
                p_h1.set_ydata(press_data[0, :])
                p_plt.set_ylim(np.min(press_data) - np.std(press_data) / 2, np.max(press_data) + np.std(press_data) / 2)
                l_h1.set_ydata(light_data[0, :])
                l_plt.set_ylim(np.min(light_data) - np.std(light_data) / 2, np.max(light_data) + np.std(light_data) / 2)
                plt.draw()
                plt.pause(0.0000001)

            await gyro_acc.disable()
            await temp_pres.disable()
            await prox.disable()

asyncio.run(main())
