import binascii  # for CRC calculation
import re  # for pattern matching in long hex strings
import sys  # to enable running the script from command line
from colorama import init, Fore, Back, Style  # to help colorizing the output

#Important variables
check = True
drive = '\\\\.\PHYSICALDRIVE0'
hexData = None
# List containing feature of partition entries
pEntMBR = []
pEntGPT = []

# Required Functions, if any

# converts hex string of length hexLength to binary string of maxlength or arbitrary length
def hexToBin(string, hexLength=2, maxBits=None):
    mBin = str(bin(int(string[0:hexLength], 16)))[2:]
    if maxBits is not None:
        while len(mBin) < maxBits: mBin = '0' + mBin
    return mBin

# Interpret partition Attributes
def partAttrib(attrib_hex, partitionName):
    while len(attrib_hex) < 16: attrib_hex = '0' + attrib_hex
    attrib_bin = ''
    startIdx = 0
    len_ah = len(attrib_hex)
    while startIdx < len_ah:
        attrib_bin += hexToBin(attrib_hex[startIdx:startIdx+2], maxBits=8)
        startIdx += 2
    # attrib_bin = attrib_bin[::-1]
    # print('Attrib Bin = ' + attrib_bin)
    print('Platform Reuired = ' + str(attrib_bin[0] == '1'))
    print('EFI firmware should ignore the content of the partition and not try to read from it = ' + str(attrib_bin[1] == 1))
    print('Legacy BIOS Bootable = ' + str(attrib_bin[2] == '1'))
    if partitionName == 'Basic data partition':
        print('Read Only = ' + str(attrib_bin[60] == '1'))
        print('Shadow copy (of another partition) = ' + str(attrib_bin[61] == '1'))
        print('Hidden = ' + str(attrib_bin[62] == '1'))
        print('No drive letter (i.e. do not automount) = ' + str(attrib_bin[63] == '1'))

# translate hex to ascii to display partition name
def partName(param):
    name = ''
    len_p = len(param)
    if len_p % 2 == 0:
        startIdx = 0
        while startIdx < len_p:
            if param[startIdx:startIdx + 2] == '00':
                startIdx += 2
                continue
            name += chr(int(param[startIdx:startIdx+2], 16))
            startIdx += 2
    return name

# isGPTPartitionEntryValid, Checks if first and last sector numbers don;t overlap with another volume
def isPEValid(mList, fLBA, lLBA):
    mCheck = True
    for mItem in mList:
        if mItem['fLBA'] <= fLBA <= mItem['lLBA']:
            mCheck = False
            print('First LBA of this sector overlaps with another volume. Entry invalid')
        elif mItem['fLBA'] <= lLBA <= mItem['lLBA']:
            mCheck = False
            print('Last LBA of this sector overlaps with another volume. Entry invalid')
        if not mCheck: break
    # return mCheck


# Little Endian Function
def littleEndian(param):
    temp = ''
    temp2 = ''
    len_p = len(param)
    if len_p % 2 == 0:
        startIdx = len_p - 1
        while startIdx > 0:
            temp = temp + param[startIdx - 1] + param[startIdx]
            startIdx -= 2
        idx = 0
        for idx, val in enumerate(temp):
            if val != '0': break
        if len(temp[idx:]) % 2 == 1: temp2 = '0'
        return temp2 + temp[idx:]
    else: return None


# Partition Array Entry
def pae(param, mList):
    if len(param) == sizeSinglePartEnt and re.fullmatch(r'0*', param) is None:
        fLBA = int(littleEndian(param[64:80]), 16)
        lLBA = int(littleEndian(param[80:96]), 16)
        tSize = (((((lLBA - fLBA) + 1) * 512) // 1024) // 1024)
        isPEValid(mList, fLBA, lLBA)
        print('Partition Type GUID in le: {' + littleEndian(param[:8]) + '-' + littleEndian(param[8:12]) + '-' + littleEndian(param[12:16]) + '-' + littleEndian(param[16:20]) + '-' + littleEndian(param[20:32]) + '}')
        print('Partition GUID: {' + param[32:64] + '}')
        print('First LBA in le: ' + param[64:80] + ' ' + littleEndian(param[64:80]) + ' ' + str(fLBA))
        print('Last LBA in le: ' + param[80:96] + ' ' + littleEndian(param[80:96]) + ' ' + str(lLBA))
        print('Size in MBs: ' + str(tSize))
        pn = partName(param[112:])
        print('Attributes in le: ' + littleEndian(param[96:112]))
        partAttrib(littleEndian(param[96:112]), pn)
        print('Partition Name: ' + pn + '\n')
        mList.append({'fLBA': fLBA, 'lLBA': lLBA})


# Read sector number
def readDriveSector(mDrive, driveSectorNum, totalBytes=None):
    wholeData = ''
    if totalBytes is None:
        endByte = driveSectorNum * 512
        startByte = endByte - 512
    else:
        startByte = (driveSectorNum - 1) * 512
        endByte = startByte + totalBytes
    with open(mDrive, 'rb') as file:
        file.seek(startByte)
        while startByte < endByte:
            readByte = str(file.read(1))
            if readByte[3] == 'x': readByte = readByte[4:6]
            elif readByte == "b'\\t'": readByte = '09'
            else:
                readByte = readByte[2]
                readByte = str(hex(int(ord(readByte))))[2:]
            startByte += 1
            wholeData = wholeData + readByte
    return str(wholeData)


# Status of Physical Drive
def sopd(param):
    if param == '80': return 'active valid'
    elif param == '00': return 'inactive valid'
    else: return 'invalid'


# CHS Calculator
def chs(param):
    hpc = 255
    spt = 63
    h = int(param[0:2], 16)
    s = str(bin(int(param[2:4], 16)))[2:]
    while len(s) < 8: s = '0' + s
    # Cylinder attachment, 2 msbs from sector number
    ca = int(s[0:2], 2)
    s = int(s, 2)
    c = str(bin(int(param[4:6], 16)))[2:]
    while len(c) < 6: c = '0' + c
    c = ca + int(c, 2)
    print('h = ' + str(h) + '\ts = ' + str(s) + '\tc = ' + str(c))
    lbaVal = (c * hpc + h) * spt + (s - 1)
    if lbaVal == -1: lbaVal = 0
    print('Sector = ' + str(lbaVal))
    return str(lbaVal)

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
    if len(hex16) == 16 * 2:
        print('Status: ' + sopd(hex16[:2]))
        chs1 = chs(hex16[2:8])
        chsLast = chs(hex16[10:16])
        lbaStart = lba(hex16[16:24])
        sectorsTotal = lba(hex16[24:]) + 1
        print('1st CHS: ' + str(chs1))
        print('Partition Type: ' + partitionType(hex16[8:10]))
        print('Last CHS: ' + str(chsLast))
        print('Start LBA: ' + str(lbaStart))
        print('Total Sectors: ' + str(sectorsTotal))
        print('Total Size = ' + str(((sectorsTotal * 512) // 1024) // 1024) + ' MBs')


##############################

# This is where the program actually starts execution

# First read cmd arguments which is actually the name of the hard disk
init(convert=True)
if len(sys.argv) > 2 or len(sys.argv) == 1:
    check = False
    print("Command should be like this in Windows 'python mGPT.py PHYSICALDRIVEn' where n is the number of physical drives attached to a Windows based system. n >= 0")
    print("Command should be like this in Linux 'python mGPT.py /dev/sda'")
    sys.exit(0)
else:
    if str(sys.argv[1]).__contains__('PHYSICAL') or str(sys.argv[1]).__contains__('DRIVE'):
        if str(sys.argv[1]).__contains__('PHYSICALDRIVEn'): sys.argv[1] = 'PHYSICALDRIVE0'
        print('Using Windows')
        drive = r'\\.\\' + str(sys.argv[1]).replace('"', '')
    elif str(sys.argv[1]).__contains__('dev') or str(sys.argv[1]).__contains__('sd'):
        print('Using Linux')
        drive = str(sys.argv[1]).replace('"', '')
    print(drive)

# Read the Protective MBR hex file
hexData = readDriveSector(drive, 1)
print('Read File for HEX Data complete')

# Check if whole data is in hex
if check:
    for item in hexData:
        if ('0' <= item <= '9') or ('A' <= item <= 'F') or ('a' <= item <= 'f'): check = True
        else: break

if not check: print('Not all values are in hex')
else:
    print('All Values are in hex')
    check = True

    # Check length of file
    if len(hexData) != 1024: print('Length of hexData is invalid')

    # Check if last two hex values are 55 AA
    if check: print('Boot Signature is' + str(hexData[510 * 2:] == '55AA' or hexData[510 * 2:] == '55aa'))

    # Since all checks are complete. We can print now
    sop = 1
    if check:
        print('Bootstrap Code: ')
        print(hexData[:446 * 2])
        sop = 446 * 2
        print('\nPartition Entry 0: ')
        partitionEntry(hexData[sop:sop + 32], pEntMBR)

    check = not [True if item == '0' else False for item in hexData[sop + 32:len(hexData) - 4]].__contains__(False)
    if not check: print('Protective MBR contains more than 1 partition entry')
    else:
        print('Read LBA 2 for GPT Header\n')
        hexData = readDriveSector(drive, 2)
        print('Read GPT Header')
        # if len(hexData) != 512 * 2:

        # All other required variables
        signature = gptVersion = headerSize = CRC_32 = reserved = currentLBA = backupLBA = firstUsableLBA = lastUsableLBA = diskGUID = startLBA = numPartEnt = sizeSinglePartEnt = None

        if check:
            signature = hexData[:8 * 2]
            if signature == '4546492050415254': print(str(signature) + ' Signature is Valid')
            else: print('Signature is invalid')

            if check:
                gptVersion = hexData[16:24]
                if gptVersion == '00000100': print(str(gptVersion) + ' Valid GPT Version')
                else: print('Invalid GPT Version')

            if check:
                headerSize = hexData[24:32]
                print(littleEndian(headerSize) + ' Header Size in le')

            if check:
                CRC_32 = hexData[:32] + '0' * 8 + hexData[40:int(littleEndian(headerSize), 16) * 2]
                CRC_32 = binascii.crc32(binascii.a2b_hex(CRC_32))
                CRC_32 = str(hex(int(CRC_32) % (1 << 32)))[2:]
                if littleEndian(hexData[32:40]) == CRC_32: print(CRC_32 + ' Calculated CRC32 matches original')
                else: print("Calculated CRC32 doesn't match original CRC32")

            if check:
                reserved = hexData[40:48]
                if reserved == '0' * 8: print(reserved + ' Reserved Entry is valid')
                else: print('Reserved Entry is invalid')

            if check:
                currentLBA = littleEndian(hexData[48:64])
                if currentLBA == '1': print(currentLBA + ' Current LBA location is valid in le')
                else: print(currentLBA + ' Current LBA location is invalid')

            if check:
                backupLBA = littleEndian(hexData[64:80])
                if backupLBA != currentLBA: print(backupLBA + ' Backup LBA location in le')
                else: print("Backup LBA" + backupLBA + " and Current LBA " + currentLBA + " are same, which isn't possible. LBA invalid")

            if check:
                firstUsableLBA = littleEndian(hexData[80:96])
                print(firstUsableLBA + ' First Usable LBA location in le')

            if check:
                lastUsableLBA = littleEndian(hexData[96:112])
                print(lastUsableLBA + ' Last usable LBA in le')

            if check:
                diskGUID = littleEndian(hexData[112:144])
                print(diskGUID + ' Disk GUID in le')

            if check:
                startLBA = littleEndian(hexData[144:160])
                if startLBA == '2': print(startLBA + ' Starting LBA of array of partition entries in le')
                else: print(startLBA + ' Starting LBA for array of partition entries is invalid')

            if check:
                numPartEnt = littleEndian(hexData[160:168])
                print(numPartEnt + ' Number of partition Entries in array in le')

            if check:
                sizeSinglePartEnt = littleEndian(hexData[168:176])
                print(sizeSinglePartEnt + ' Size of single partition entry in le')

            if check:
                crc32partEnt = littleEndian(hexData[176:184])
                tBytes = (int(numPartEnt, 16)) * int(sizeSinglePartEnt, 16)
                CRC_32 = readDriveSector(drive, int(startLBA, 16) + 1, tBytes)
                CRC_32 = binascii.crc32(binascii.a2b_hex(CRC_32))
                CRC_32 = str(hex(int(CRC_32) % (1 << 32)))[2:]
                if crc32partEnt == CRC_32: print(CRC_32 + ' Calculated CRC32 for Partition Entries Array in le is Valid')
                else: print('Original ' + crc32partEnt + ' CRC32 of partition entry in le is invalid with calculated ' + CRC_32)

            if check:
                if re.match(r'0*', hexData[176:]): print('Valid GPT Header')
                else: print('Invalid GPT Header')

            if check:
                print('\nRead Partition Entries Array')
                numPartEnt = int(numPartEnt, 16)
                sizeSinglePartEnt = int(sizeSinglePartEnt, 16)
                hexData = readDriveSector(drive, int(startLBA, 16) + 1, numPartEnt * sizeSinglePartEnt)
                startEnt = start = 0
                sizeSinglePartEnt *= 2
                len_h = len(hexData)
                while startEnt < numPartEnt:
                    if re.fullmatch(r'0*', hexData[start:start + sizeSinglePartEnt]) is None:
                        print('Partition Array Entry ' + str(start // sizeSinglePartEnt) + ':')
                        pae(hexData[start:start + sizeSinglePartEnt], pEntGPT)
                    start += 256
                    startEnt += 1