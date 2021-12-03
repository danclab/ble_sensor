import csv

import matplotlib.pyplot as plt
import numpy as np

if __name__=='__main__':
    fname='test.tsv'
    with open(fname) as filename:
        read_tsv=csv.reader(filename,delimiter='\t')
        header=None
        data=[]
        for row in read_tsv:
            if header is None:
                header=row
            else:
                row=[float(x) for x in row]
                data.append(row)
    data=np.array(data)


    print('')

    dts = np.diff(data[:, 0])

    plt.figure()
    plt.subplot(2,2,1)
    plt.plot(data[:, 0], data[:, 1])
    plt.plot(data[:, 0], data[:, 2])
    plt.plot(data[:, 0], data[:, 3])
    plt.ylabel('Gyroscope')
    plt.legend(['x','y','z'])

    plt.subplot(2, 2, 3)
    plt.plot(data[:, 0], data[:, 4])
    plt.plot(data[:, 0], data[:, 5])
    plt.plot(data[:, 0], data[:, 6])
    plt.xlabel('Time (ms)')
    plt.ylabel('Accelerometer')
    plt.legend(['x', 'y', 'z'])

    plt.subplot(2,2,2)
    plt.hist(dts,100)
    plt.xlabel('DT')
    plt.ylabel('Count')
    plt.show()