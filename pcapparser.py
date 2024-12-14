from scapy.all import *
import sys
import os
import pandas as pd

if (len(sys.argv) not in [2, 3]):
    print("""Arguments can be one or two:
        1) path to pcap file to be parsed, e.g. "capture.pcap"
        2) [optional] filename for the xlsx and csv output""")
    exit()
pcapfile = sys.argv[1]
outname = sys.argv[2] if (len(sys.argv) == 3) else pcapfile.split(".")[0]


def unpack(p):
    row = []
    row += [p[TCP].sport, p[TCP].dport, p[TCP].seq,
            p[TCP].ack, p[TCP].flags.value, p[TCP].window]
    if p[TCP].payload:
        row += [len(p[TCP].load)]
    else:
        row += [0]
    try:
        tsval, tsecr = dict(p[TCP].options)['Timestamp']
        row += [tsval, tsecr]
    except:
        row += [0, 0]
    row += [str(p[TCP].options)]
    row += [p[IP].src, p[IP].dst]
    row += [p[Ether].src, p[Ether].dst]
    row += [p.time]
    return row


table = []
pktreader = PcapReader(pcapfile)
print(f"Parsing {pcapfile}...")
count = 0
for p in pktreader:
    symbol = '|' if count % 2 == 0 else '-'
    if TCP not in p:
        continue
    row = unpack(p)
    table.append(row)
    count += 1
    print(f"{symbol}", end="\r")

columns = ['sport', 'dport', 'seq', 'ack', 'flags', 'rcwnd', 'tcppayloadlen',
           'tcptsval', 'tcptsecr', 'tcpoptions', 'ipsrc', 'ipdst', 'ethsrc',
           'ethdst', 'captureTime']
df = pd.DataFrame(table, columns=columns)

# Setting startCaptureTime to zero
startCapture = df.captureTime[0]
df['captureTime'] = df['captureTime'] - startCapture

# https://datagy.io/python-int-to-binary/
df['binflags'] = df['flags'].apply(lambda x: "{0:b}".format(x).zfill(9))
df['syn'] = df['binflags'].apply(lambda x: True if x[-2] == '1' else False)
df['fin'] = df['binflags'].apply(lambda x: True if x[-1] == '1' else False)
df['ack'] = df['binflags'].apply(lambda x: True if x[-5] == '1' else False)


df.to_csv(f"{outname}.csv", index=False)
df.to_excel(f"{outname}.xlsx", index=False)
print(f"{outname}.xlsx and {outname}.csv written to {os.getcwd()}")
