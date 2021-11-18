import datetime
import sys

from bluepy import btle

from sensor import GyroAccelSensor, TempPressureSensor, AmbientLightSensor, RecordingDevice

if __name__=='__main__':

    print('Scanning...')

    scanner = btle.Scanner()

    sensor_address=None

    while sensor_address is None:
        devices = scanner.scan(10.0)
        for dev in devices:
            addr=dev.addr
            name=dev.getValueText(9)
            if name=='SENSOR_PRO':
                print('%s: %s' %  (name, addr))
                sensor_address=addr
                break

    if sensor_address is not None:
        dev=RecordingDevice(sensor_address)
        dev.enable(gyro_acc=True, temp_press=False, ambient_light=False)

        try:
            dev.read('test.tsv')
        finally:
            dev.disconnect()
