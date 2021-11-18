import sys
import datetime
import numpy as np
from bluepy import btle
import matplotlib.pyplot as plt

from sensor import GyroAccelSensor, TempPressureSensor, AmbientLightSensor

if __name__=='__main__':
    print('Scanning...')

    scanner = btle.Scanner()

    address=None

    while sensor_address is None:
        devices = scanner.scan(10.0)
        for dev in devices:
            addr=dev.addr
            name=dev.getValueText(9)
            if name=='SENSOR_PRO':
                print('%s: %s' %  (name, addr))
                address=addr
                break

    print("Connecting...")
    dev = btle.Peripheral(address, "random")

    try:
        # Set sampling rate to 100
        MPU6050Service = dev.getServiceByUUID('6a800001-b5a3-f393-e0a9-e50e24dcca9e')
        SampIntChar = MPU6050Service.getCharacteristics('6a80ff0c-b5a3-f393-e0a9-e50e24dcca9e')[0]
        dev.writeCharacteristic(SampIntChar.valHandle, b"\x00\x64")

        gyro_acc = GyroAccelSensor(dev)
        gyro_acc.enable()
        temp_pres = TempPressureSensor(dev)
        temp_pres.enable()
        prox = AmbientLightSensor(dev)
        prox.enable()

        gyro_data = np.zeros((3, 100))
        accel_data = np.zeros((3, 100))
        ang_data = np.zeros((3, 100))
        temp_data = np.zeros((1,100))
        press_data = np.zeros((1,100))
        light_data = np.zeros((1,100))

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

        t_plt=plt.subplot(3, 2, 3)
        t_h1, = plt.plot(temp_data[0, :])
        plt.ylim(19.36, 19.38)
        plt.legend(['temp'])
        p_plt=plt.subplot(3, 2, 4)

        p_h1, = plt.plot(press_data[0, :])
        plt.ylim(28, 35)
        plt.legend(['pressure'])
        l_plt=plt.subplot(3, 2, 5)
        l_h1, = plt.plot(light_data[0, :])
        plt.ylim(0,5000)
        plt.legend(['light'])
        plt.draw()

        angle=np.zeros((3,1))
        last_t=datetime.datetime.now()

        gyroX=0
        gyroY=0
        yaw=0
        while True:
            (gyro, accel) = gyro_acc.read()
            (temp, press) = temp_pres.read()
            light=prox.read()
            t=datetime.datetime.now()
            dt=t-last_t
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

            #ang_data[:, 0:-1] = ang_data[:, 1:]
            #ang_data[:, -1] = angle[:,[0]]

            temp_data[:, 0:-1] = temp_data[:, 1:]
            temp_data[:,-1]=temp

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
            #ang_h1.set_ydata(ang_data[0, :])
            #ang_h2.set_ydata(ang_data[1, :])
            #ang_h3.set_ydata(ang_data[2, :])
            t_h1.set_ydata(temp_data[0,:])
            t_plt.set_ylim(np.min(temp_data)-np.std(temp_data)/2,np.max(temp_data)+np.std(temp_data)/2)
            p_h1.set_ydata(press_data[0, :])
            p_plt.set_ylim(np.min(press_data) - np.std(press_data) / 2, np.max(press_data) + np.std(press_data) / 2)
            l_h1.set_ydata(light_data[0, :])
            l_plt.set_ylim(np.min(light_data) - np.std(light_data) / 2, np.max(light_data) + np.std(light_data) / 2)
            plt.draw()
            plt.pause(0.0000001)

    finally:
        gyro_acc.disable()
        temp_pres.disable()
        prox.disable()
        dev.disconnect()
