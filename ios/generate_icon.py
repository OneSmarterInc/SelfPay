"""Generate the existing simple MySelfPay plus mark without external dependencies."""
from pathlib import Path
import struct
import zlib
size=1024
rows=[]
for y in range(size):
    row=bytearray([0])
    for x in range(size):
        plus=(286 <= x <= 737 and 445 <= y <= 579) or (445 <= x <= 579 and 286 <= y <= 737)
        row.extend((255,255,255) if plus else (16,86,101))
    rows.append(bytes(row))
def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
(Path(__file__).parent/'MySelfPay/Assets.xcassets/AppIcon.appiconset/icon.png').write_bytes(png)
