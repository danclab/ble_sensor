import datetime
import numpy as np
from bluepy import btle
from bluepy.btle import AssignedNumbers
import matplotlib.pyplot as plt

class RecordingDevice:

    def __init__(self, address):
        print("Connecting...")
        self.dev = btle.Peripheral(address, "random")
        print('Connected!')
        self.gyro_acc = GyroAccelSensor(self.dev)
        self.temp_press = TempPressureSensor(self.dev)
        self.ambient_light = AmbientLightSensor(self.dev)
        self.data=[]
        self.t_log=[]
        self.data_log=[]

    def enable(self, gyro_acc=False, temp_press=False, ambient_light=False):
        # Set sampling rate to 100
        print('Setting sampling rate')
        MPU6050Service = self.dev.getServiceByUUID('6a800001-b5a3-f393-e0a9-e50e24dcca9e')
        SampIntChar = MPU6050Service.getCharacteristics('6a80ff0c-b5a3-f393-e0a9-e50e24dcca9e')[0]
        self.dev.writeCharacteristic(SampIntChar.valHandle, b"\x00\x64")

        print('Enabling sensors')
        dim=0
        if gyro_acc:
            self.gyro_acc.enable()
            dim=dim+6
        else:
            self.gyro_acc.disable()
        if temp_press:
            self.temp_press.enable()
            dim=dim+2
        else:
            self.temp_press.disable()
        if ambient_light:
            self.ambient_light.enable()
            dim=dim+1
        else:
            self.ambient_light.disable()
        self.data=np.zeros((1,dim))
        self.data_log=[]#np.zeros((self.n,dim))

    def read(self, fname=None):
        print('Recording data')
        if fname is not None:
            self.log_file=open(fname, 'w')
            self.log_file.write('time')
            if self.gyro_acc.enabled:
                self.log_file.write('\tg_x\tg_y\tg_z\ta_x\ta_y\ta_z')
            if self.temp_press.enabled:
                self.log_file.write('\tt\tp')
            if self.ambient_light.enabled:
                self.log_file.write('\tl')
            self.log_file.write('\n')

        start_t = datetime.datetime.now()
        #last_t=start_t
        while True:
            idx=0
            if self.gyro_acc.enabled:
                (gyro, accel) = self.gyro_acc.read()
                self.data[0,idx:idx+3]=gyro
                self.data[0,idx+3:idx+6]=accel
                idx=idx+6
            if self.temp_press.enabled:
                (temp, press) = self.temp_press.read()
                self.data[0,idx+6]=temp
                self.data[0,idx+7]=press
                idx=idx+2
            if self.ambient_light.enabled:
                amb_light = self.ambient_light.read()
                self.data[0,idx]=amb_light
            t=datetime.datetime.now()
            #dt=(t-last_t).total_seconds()*1000.0
            #print('%.2f' % dt)
            #last_t=t
            #print('%.2f:' % ((t - start_t).total_seconds() * 1000.0))
            #print(self.data)
            self.t_log.append((t - start_t).total_seconds() * 1000.0)
            self.data_log.append(np.copy(self.data))
        # plt.figure()
        # plt.hist(self.dts, 100)
        # plt.show()

    def disconnect(self):

        for t,row in zip(self.t_log, self.data_log):
            self.log_file.write('%.2f' % t)
            idx=0
            if self.gyro_acc.enabled:
                self.log_file.write('\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f' % (row[0,idx],row[0,idx+1],row[0,idx+2],row[0,idx+3],row[0,idx+4],row[0,idx+5]))
                idx=idx+6
            if self.temp_press.enabled:
                self.log_file.write('\t%.3f\t%.3f' % (row[0, idx], row[0, idx + 1]))
                idx=idx+2
            if self.ambient_light.enabled:
                self.log_file.write('\t%.3f' % (row[0, idx]))
            self.log_file.write('\n')
        self.log_file.close()
        if self.gyro_acc is not None:
            self.gyro_acc.disable()
        if self.temp_press is not None:
            self.temp_press.disable()
        if self.ambient_light is not None:
            self.ambient_light.disable()
        if self.dev is not None:
            self.dev.disconnect()


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
        self.enabled=False

    def enable(self):
        if self.service is None:
            self.service = self.periph.getServiceByUUID(self.svcUUID)
        if self.data is None:
            self.data = self.service.getCharacteristics(self.dataUUID)[0]
        if self.ctrl is None:
            self.ctrl = self.data.getDescriptors(AssignedNumbers.client_characteristic_configuration)[0]
        if self.sensorOn is not None:
            self.ctrl.write(self.sensorOn, withResponse=True)
        self.enabled=True

    def read(self):
        return self.data.read()

    def disable(self):
        if self.ctrl is not None:
            self.ctrl.write(self.sensorOff)
        self.enabled=False


class GyroAccelSensor(SensorBase):
    gyro_scale = 250.0 / 32768.0
    acc_scale_2_g = 2.0 / 32768.0

    def __init__(self, periph):
        SensorBase.__init__(self, periph, '6a800001-b5a3-f393-e0a9-e50e24dcca9e',
                            '6a806050-b5a3-f393-e0a9-e50e24dcca9e')
        self.gyro = np.zeros((1, 3))
        self.accel = np.zeros((1, 3))

    def read(self):
        data = self.data.read()

        # Compute gyro
        for idx, iter in enumerate(range(6, 12, 2)):
            self.gyro[0, idx] = int.from_bytes(data[iter:iter + 2], byteorder='big', signed=True) * self.gyro_scale

        # Compute acceleraton
        for idx, iter in enumerate(range(0, 6, 2)):
            self.accel[0, idx] = int.from_bytes(data[iter:iter + 2], byteorder='big', signed=True) * self.acc_scale_2_g

        return self.gyro, self.accel



class AmbientLightSensor(SensorBase):
    light_scale = 0.35

    def __init__(self, periph):
        SensorBase.__init__(self, periph, '6a800001-b5a3-f393-e0a9-e50e24dcca9e',
                            '6a803216-b5a3-f393-e0a9-e50e24dcca9e')

        self.light=0

    def read(self):
        data = self.data.read()
        self.light = int.from_bytes(data, byteorder='big', signed=False) * self.light_scale

        return self.light


class TempPressureSensor(SensorBase):
    sensorOn = b"\x01\x01"
    sensorOff = b"\x00\x00"
    temp_scale=1/5120
    pressure_scale=1

    def __init__(self, periph):
        SensorBase.__init__(self, periph, '6a800001-b5a3-f393-e0a9-e50e24dcca9e',
                            '6a80b280-b5a3-f393-e0a9-e50e24dcca9e')
        self.temp=0
        self.pressure=0

    def read(self):
        data=self.data.read()
        self.temp = int.from_bytes(data[1:4], byteorder='big', signed=False) * self.temp_scale

        self.pressure=int.from_bytes(data[4:8], byteorder='big', signed=False)*self.pressure_scale

        return self.temp, self.pressure
