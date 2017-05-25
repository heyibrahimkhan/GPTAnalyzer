#!/usr/bin/python
import re
# import mMBR
import sys

# import time, os, sys
#
#
# def split_list(n):
#     """will return the list index"""
#     return [(x + 1) for x, y in zip(n, n[1:]) if y - x != 1]
#
#
# def get_sub_list(my_list):
#     """will split the list base on the index"""
#     my_index = split_list(my_list)
#     output = list()
#     prev = 0
#     for index in my_index:
#         new_list = [x for x in my_list[prev:] if x < index]
#         output.append(new_list)
#         prev += len(new_list)
#     output.append([x for x in my_list[prev:]])
#     return output
#
#
# def usage():
#     print
#     'Usage: read-sector.py file'
#     exit()
#
#
# def main():
#     if (len(sys.argv) != 2):
#         usage()
#     else:
#         try:
#             f = open(sys.argv[1], 'r')
#
#         except:
#             usage()
#
#         # Initialize list of non-empty sectors
#         nums = []
#
#         # Find number of sectors in the file
#         sectors = (os.path.getsize(sys.argv[1]) / 512)
#
#         for i in range(sectors):
#             result = False
#             # for j in range(511):
#             f.seek(i * 512, 0)
#             line = f.read(1).encode('hex')
#             # Scan first value
#             if (line != '00'):
#                 result = True
#
#             if (result):
#                 print(i)
#                 nums.append(i)
#
#         # Print the list of non-empty sectors
#         nums = get_sub_list(nums)
#
#
# if __name__ == "__main__":
#     main()
# possible_drives = [
#         r'\\.\PHYSICALDRIVE0', # Windows
#         r"\\\\.\\PhysicalDrive2",
#         r"\\.\PhysicalDrive3",
#         "/dev/mmcblk0", # Linux - MMC
#         "/dev/mmcblk1",
#         "/dev/mmcblk2",
#         "/dev/sdb", # Linux - Disk
#         "/dev/sdc",
#         "/dev/sdd",
#         "/dev/disk1", #MacOSX
#         "/dev/disk2",
#         "/dev/disk3",
#         ]
# sector_size = 512
# for drive in possible_drives:
#     try:
#         with open(drive, 'rb') as file:
#             print('Opened')
#             # disk = file.seek(0*sector_size)
#             # disk = file.readlines(100)
#             disk = str(file.read(1))
#             disk = str(file.read(1))
#             disk = str(file.read(1))
#             # disk = '' + str(disk)[0]
#             print(str(disk))
#             # disk.seek(14000*sector_size)
#             # if "MOMS" in disk.read(7):
#             #     print("MOMS disk found at " + drive)
#             #     break
#     except:
#         pass

def readSector(drive, sectorNumber):
    wholeData = ''
    endByte = sectorNumber * 512
    startByte = endByte - 512
    with open(drive, 'rb') as file:
        file.seek(startByte)
        while startByte < endByte:
            readByte = str(file.read(1))
            if readByte[3] == 'x':
                readByte = readByte[4:6]
            else:
                readByte = readByte[2]
                readByte = str(hex(int(ord(readByte))))[2:]
            startByte += 1
            wholeData = wholeData + readByte
    print('Whole Data = ' + wholeData)


# print(str(hex(int(ord('c')))))
# readSector(r'\\.\PHYSICALDRIVE0', 2)
# data = ['a','b','c','d']
# data[2:4] = 'gh'
# print(data)
# print(str(int('5c', 16)))
# print(str(re.fullmatch(r'0*', '000')))
# print(str(int('09', 16)))
# hexData = mMBR.readDriveSector(mMBR.drive, 3)
# with open('msect.txt', 'r') as file:
#     hexData2 = file.read()
# if len(hexData) == len(hexData2):
#     len_h = len(hexData)
#     start = 0
#     while start < len_h:
#         if hexData[start].capitalize() != hexData2[start].capitalize():
#             print(hexData[start] + ' ' + hexData2[start])
#             break
#         start += 1
# else: print('Not Wow')

if len(sys.argv) > 2 or len(sys.argv) == 1:
    check = False
    print(sys.argv)
    print("Command should be like this 'python mMBR.py r'\\\\.\PHYSICALDRIVE2'")
else:
    print(sys.argv)
    print('Correct')