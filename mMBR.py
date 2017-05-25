import binascii
import re

# Required Functions, if any

# Read sector number
def readSector(drive, driveSectorNum):
    wholeData = ''
    endByte = driveSectorNum * 512
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
    return str(wholeData)

# Status of Physical Drive
def sopd(param):
    if param == '80':
        return 'active valid'
    elif param == '00':
        return 'inactive valid'
    else:
        return 'invalid'


# CHS Calculator
def chs(param):
    hpc = 255
    spt = 63
    h = int(param[0:2], 16)
    s = str(bin(int(param[2:4], 16)))[2:]
    while (len(s) < 8): s = '0' + s
    # Cylinder attachment, 2 msbs from sector number
    ca = int(s[0:2], 2)
    s = int(s, 2)
    c = str(bin(int(param[4:6], 16)))[2:]
    while (len(c) < 6): c = '0' + c
    c = ca + int(c, 2)
    print('h = ' + str(h) + '\ts = ' + str(s) + '\tc = ' + str(c))
    lbaVal = (c * hpc + h) * spt + (s - 1)
    if lbaVal == -1: lbaVal = 0
    print('Sector = ' + str(lbaVal))


# Partition Type
def partitionType(param):
    if param == '07': return 'NTFS'
    elif param == '0C' or param == '0c': return 'FAT32'
    elif param == '05': return 'Extended'
    elif param == 'EE' or param == 'ee': return 'Unknown'
    else: return 'Other'


def lba(param):
    temp = ''
    len_p = len(param)
    while len_p > 1:
        temp = temp + param[len_p - 2] + param[len_p - 1]
        len_p = len_p - 2
    return int(temp, 16)


def partitionEntry(hex16, mList):
    check = True
    if len(hex16) == 16 * 2:
        print('Status: ' + sopd(hex16[:2]))
        chs1 = chs(hex16[2:8])
        chsLast = chs(hex16[10:16])
        lbaStart = lba(hex16[16:24])
        sectorsTotal = lba(hex16[24:])
        if check:
            print('1st CHS: ' + str(chs1))
            print('Partition Type: ' + partitionType(hex16[8:10]))
            print('Last CHS: ' + str(chsLast))
            print('Start LBA: ' + str(lbaStart))
            print('Total Sectors: ' + str(sectorsTotal))
            print('Total Size = ' + str(((sectorsTotal*512)//1024)//1024) + ' MBs')
    else: print('Partition entry invalid length')


##############################

# This is where the program actually starts execution
# Read the Protective MBR hex file
drive = r'\\.\PHYSICALDRIVE2'
hexData = ""
hexData = readSector(drive, 1)
print('Read File for HEX Data complete')

# List containing feature of partition entries
pEntList = []

# Check if whole data is in hex
check = True
for item in hexData:
    if ('0' <= item <= '9') or ('A' <= item <= 'F') or ('a' <= item <= 'f'):
        check = True
    else:
        check = False
        break

# Little Endian Function
def littleEndian(param):
    temp = ''
    len_p = len(param)
    if len_p % 2 == 0:
        start = len_p - 1
        while start > 0:
            temp = temp + param[start - 1] + param[start]
            start -= 2
        idx = 0
        for idx, val in enumerate(temp):
            if val != '0':
                break
        return temp[idx:]
    else: return None

if not check:
    print('Not all values are in hex')
else:
    print('All Values are in hex')
    check = True

    # Check length of file
    if len(hexData) != 1024:
        print('File length is invalid')
        check = False

    # Check if last two hex values are 55 AA
    if check:
        check = (hexData[510 * 2:] == '55AA' or hexData[510 * 2:] == '55aa')
        if check: print('Boot Signature is Valid')
        else: print('Boot Signature is inavlid')

    # Since all checks are complete. We can print now
    if check:
        print('Bootstrap Code: ')
        print(hexData[:446 * 2])
        sop = 446 * 2
        print('\nPartition Entry 0: ')
        partitionEntry(hexData[sop:sop + 32], pEntList)

    check = not [True if item == '0' else False for item in hexData[sop+32:len(hexData) - 4]].__contains__(False)
    if not check:
        print('Protective MBR contains more than 1 partition entry')
    else:
        print('Read LBA 2 for GPT Header\n')
        hexData = readSector(drive, 2)
        print('Read GPT Header')
        if(len(hexData) != 512*2): check = False
        if check:
            signature = hexData[:8*2]
            if signature == '4546492050415254': print(str(signature) + ' Signature is Valid')
            else:
                print('Signature is invalid')
                check = False

            if check:
                gptVersion = hexData[16:24]
                if gptVersion == '00000100': print(str(gptVersion) + ' Valid GPT Version')
                else:
                    print('Invalid GPT Version')
                    check = False

            if check:
                headerSize = hexData[24:32]
                print(littleEndian(headerSize) + ' Header Size')

            if check:
                CRC_32 = hexData[:32] + '0'*8 + hexData[40:int(littleEndian(headerSize), 16)*2]
                CRC_32 = binascii.crc32(binascii.a2b_hex(CRC_32))
                CRC_32 = str(hex(int(CRC_32) % (1 << 32)))[2:]
                if littleEndian(hexData[32:40]) == CRC_32: print(CRC_32 + ' Calculated CRC32 matches original')
                else:
                    print("Calculated CRC32 doesn't match original CRC32")
                    check = False

            if check:
                reserved = hexData[40:48]
                if reserved == '0'*8: print(reserved + ' Reserved Entry is valid')
                else:
                    check = False
                    print('Reserved Entry is invalid')

            if check:
                currentLBA = littleEndian(hexData[48:64])
                if currentLBA == '1': print(currentLBA + ' Current LBA location is valid')
                else:
                    check = False
                    print(currentLBA + ' Current LBA location is invalid')

            if check:
                backupLBA = littleEndian(hexData[64:80])
                if backupLBA != currentLBA: print(backupLBA + ' Backup LBA location')
                else: check = False

            if check:
                firstUsableLBA = littleEndian(hexData[80:96])
                print(firstUsableLBA + ' First Usable LBA location')

            if check:
                lastUsableLBA = littleEndian(hexData[96:112])
                print(lastUsableLBA + ' Last usable LBA')

            if check:
                diskGUID = littleEndian(hexData[112:144])
                print(diskGUID + ' Disk GUID')

            if check:
                startLBA = littleEndian(hexData[144:160])
                if startLBA == '2': print(startLBA + ' Starting LBA of array of partition entries')
                else:
                    check = False
                    print(startLBA + ' Starting LBA for array of partition entries is invalid')

            if check:
                numPartEnt = littleEndian(hexData[160:168])
                print(numPartEnt + ' Number of partition Entries in array')

            if check:
                sizeSinglePartEnt = littleEndian(hexData[168:176])
                print(sizeSinglePartEnt + ' Size of single partition entry')

            if check:
                crc32partEnt = littleEndian(hexData[176:184])
                print(crc32partEnt + ' CRC32 of partition entry')

            if check:
                if re.match(r'0*', hexData[176:]): print('Valid GPT')
                else:
                    check = False
                    print('Invalid GPT')
                # if crc32Original == '00000100':
                #     print('Valid GPT Version')
                # else:
                #     print('Invalid GPT Version')
                #     check = False
        # iterations = 0
        # while (iterations < 4):
        #     print('\nPartition Entry ' + str(iterations) + ':')
        #     partitionEntry(hexData[sop:sop + 32], pEntList)
        #     sop += 32
        #     iterations += 1