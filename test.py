import sys
import datetime
import numpy as np
from bluepy import btle
from bluepy.btle import AssignedNumbers
import matplotlib.pyplot as plt


class SensorBase:
    sensorOn = b"\x19\x90"
    sensorOff = b"\x00\x00"

    def __init__(self, periph, svcUUID, dataUUID):
        self.periph = periph
        self.svcUUID = svcUUID
        self.dataUUID = dataUUID
        self.service = None
        self.ctrl = None
        self.data = None
        self.last_data_bytes = None
        self.last_t = datetime.datetime.now()

    def enable(self):
        if self.service is None:
            self.service = self.periph.getServiceByUUID(self.svcUUID)
        if self.data is None:
            self.data = self.service.getCharacteristics(self.dataUUID)[0]
        if self.ctrl is None:
            self.ctrl = self.data.getDescriptors(AssignedNumbers.client_characteristic_configuration)[0]
        if self.sensorOn is not None:
            self.ctrl.write(self.sensorOn, withResponse=True)

    def read(self):
        return self.data.read()

    def disable(self):
        if self.ctrl is not None:
            self.ctrl.write(self.sensorOff)


def compute_gyro(data):
    gyro_scale = 250.0 / 32768.0
    gyr = np.zeros((3, 1))
    for idx, iter in enumerate(range(6, 12, 2)):
        gyr[idx]=int.from_bytes(data[iter:iter+2], byteorder='big', signed=True) * gyro_scale
    return gyr


def compute_acceleration(data):
    acc_scale_2_g = 2.0 / 32768.0
    acc = np.zeros((3, 1))
    for idx, iter in enumerate(range(0, 6, 2)):
        acc[idx] = int.from_bytes(data[iter:iter + 2], byteorder='big', signed=True) * acc_scale_2_g
    return acc

def compute_temp(data):
    temp_scale=1/5120
    temp=int.from_bytes(data[0:4], byteorder='big', signed=True)*temp_scale
    return temp

def compute_pressure(data):
    pressure_scale=1/100
    pressure=int.from_bytes(data[4:8], byteorder='big', signed=True)*pressure_scale
    return pressure

class GyroAccelSensor(SensorBase):
    def __init__(self, periph):
        SensorBase.__init__(self, periph, '6a800001-b5a3-f393-e0a9-e50e24dcca9e',
                            '6a806050-b5a3-f393-e0a9-e50e24dcca9e')
        self.gyro = np.zeros((3, 1))
        self.accel = np.zeros((3, 1))

    def read(self):
        data_bytes = self.data.read()
        t = datetime.datetime.now()

        self.gyro = compute_gyro(data_bytes)
        self.accel = compute_acceleration(data_bytes)

        if not data_bytes == self.last_data_bytes:
            dt = t - self.last_t
            print('DT=%.2f ms' % (dt.total_seconds() * 1000))
            self.last_t = t

        self.last_data_bytes = data_bytes
        return self.gyro, self.accel


class TempPressureSensor(SensorBase):
    def __init__(self, periph):
        SensorBase.__init__(self, periph, '6a800001-b5a3-f393-e0a9-e50e24dcca9e',
                            '6a80b280-b5a3-f393-e0a9-e50e24dcca9e')
        self.temp=0
        self.pressure=0

    def read(self):
        data_bytes=self.data.read()
        t = datetime.datetime.now()
        self.temp=compute_temp(data_bytes)
        self.pressure=compute_pressure(data_bytes)

        if not data_bytes == self.last_data_bytes:
            dt = t - self.last_t
            print('DT=%.2f ms' % (dt.total_seconds() * 1000))
            self.last_t = t

        self.last_data_bytes = data_bytes
        return self.temp, self.pressure


if __name__=='__main__':
    address=sys.argv[1]
    print("Connecting...")
    dev = btle.Peripheral(address, "random")

    try:
        # Set sampling rate to 100
        MPU6050Service = dev.getServiceByUUID('6a800001-b5a3-f393-e0a9-e50e24dcca9e')
        SampIntChar = MPU6050Service.getCharacteristics('6a80ff0c-b5a3-f393-e0a9-e50e24dcca9e')[0]
        dev.writeCharacteristic(SampIntChar.valHandle, b"\x00\x64")

        gyro_acc = GyroAccelSensor(dev)
        gyro_acc.enable()
        #temp_pres = TempPressureSensor(dev)
        #temp_pres.enable()

        gyro_data = np.zeros((3, 100))
        accel_data = np.zeros((3, 100))
        #temp_data = np.zeros((1,100))
        #press_data = np.zeros((1,100))

        plt.subplot(2, 1, 1)
        g_h1, = plt.plot(gyro_data[0, :])
        g_h2, = plt.plot(gyro_data[1, :])
        g_h3, = plt.plot(gyro_data[2, :])
        plt.ylim(-250, 250)
        plt.legend(['gyro x', 'gyro y', 'gyro z'])
        plt.subplot(2, 1, 2)
        a_h1, = plt.plot(accel_data[0, :])
        a_h2, = plt.plot(accel_data[1, :])
        a_h3, = plt.plot(accel_data[2, :])
        plt.ylim(-2, 2)
        plt.legend(['acc x', 'acc y', 'acc z'])
        # plt.subplot(4, 1, 3)
        # t_h1, = plt.plot(temp_data[0, :])
        # plt.ylim(19.25, 19.5)
        # plt.legend(['temp'])
        # plt.subplot(4, 1, 4)
        # p_h1, = plt.plot(press_data[0, :])
        # plt.ylim(0, 1000)
        # plt.legend(['pressure'])
        plt.draw()

        while True:
            (gyro, accel) = gyro_acc.read()
            # (temp, press) = temp_pres.read()
            # gyro=2*np.random.randn(3,1)
            # accel = 1*np.random.randn(3, 1)

            gyro_data[:, 0:-1] = gyro_data[:, 1:]
            gyro_data[:, -1] = np.transpose(gyro)

            accel_data[:, 0:-1] = accel_data[:, 1:]
            accel_data[:, -1] = np.transpose(accel)

            # temp_data[:, 0:-1] = temp_data[:, 1:]
            # temp_data[:,-1]=temp
            #
            # press_data[:, 0:-1] = press_data[:, 1:]
            # press_data[:, -1] = press

            g_h1.set_ydata(gyro_data[0, :])
            g_h2.set_ydata(gyro_data[1, :])
            g_h3.set_ydata(gyro_data[2, :])
            a_h1.set_ydata(accel_data[0, :])
            a_h2.set_ydata(accel_data[1, :])
            a_h3.set_ydata(accel_data[2, :])
            # t_h1.set_ydata(temp_data[0,:])
            # p_h1.set_ydata(press_data[0, :])
            plt.draw()
            plt.pause(0.0000001)

    finally:
        dev.disconnect()
