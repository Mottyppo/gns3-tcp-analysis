import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table

#TODO: documentation

class ConnectionData:# TODO: measurement units + refactor everything

    EXP_1_BANDWIDTH = 100000 # kb per second
    BANDWIDTH = 11100 # kb per second
    DELAY = 42 # milliseconds
    CLIENT_IP = ['192.168.1.10', '192.168.1.11']
    SERVER_IP = ['192.168.1.20', '192.168.1.21']
    ALPHA = 0.125
    BETA = 0.25

    duration = None # milliseconds
    total_throughput = None # kb
    throughput = None # kb per second
    rcwnd = None # bytes
    efficiency = None #nu, %
    rtt = None # milliseconds
    srtt = None
    rttvar = None
    rto = None

    # def __str__(self): #TODO: fix here
    #     return f"Duration: {self.duration} ms\nTotal throughput: {self.total_throughput} kb/s\nEfficiency: {self.efficiency}\nRTT: {self.rtt}\nSRTT: {self.srtt}\nRTTVar: {self.rttvar}\nRTO: {self.rto}"

def analyze_data(file : str, n : int) -> ConnectionData :

    packets = pd.read_csv(file)
    data : ConnectionData = ConnectionData()
    bandwidth = ConnectionData.EXP_1_BANDWIDTH if n == 0 else ConnectionData.BANDWIDTH

    # DURATION
    data.duration = int(packets['captureTime'].iloc[-1] * 1000)
    print(f"Duration: {data.duration} ms")

    # RTT
    client_to_server = packets[(packets['ipsrc'].isin(ConnectionData.CLIENT_IP)) & (packets['ipdst'].isin(ConnectionData.SERVER_IP))]
    server_to_client = packets[(packets['ipsrc'].isin(ConnectionData.SERVER_IP)) & (packets['ipdst'].isin(ConnectionData.CLIENT_IP))]
    packets['rtt'] = 0
    for index, ack_packet in server_to_client.iterrows():
        matching_packet = client_to_server[
            client_to_server['tcptsecr'] == ack_packet['tcptsval']
        ]
        if not matching_packet.empty:
            rtt = matching_packet['captureTime'].iloc[0] - ack_packet['captureTime']
            packets.at[index, 'rtt'] = int(rtt * 1000)
    
    data.rtt = packets[packets['rtt'] != 0]['rtt'].tolist()
    
    print(f"Average RTT: {sum(data.rtt) / len(data.rtt)} ms")
    print(f"Minimum RTT: {min(data.rtt)} ms")
    print(f"Maximum RTT: {max(data.rtt)} ms")
    
    # REMOVE CLIENT TO SERVER PACKETS
    packets = packets.drop(client_to_server.index)

    # RCWND
    data.rcwnd = (packets['rcwnd']).tolist()
    print(f"Average RCWND: {sum(data.rcwnd) / len(data.rcwnd)} bytes")
    print(f"Minimum RCWND: {min(data.rcwnd)} bytes")
    print(f"Maximum RCWND: {max(data.rcwnd)} bytes")
    
    # THROUGHPUT
    packets['throughput'] = 0
    for index, row in packets.iterrows():
        if row['rtt'] != 0:
            # throughput.append(row['tcppayloadlen'] * 8 / 1000 / (row['rtt'] / 1000)) #TODO: errore ??? --> controllare col file sulla vm
            packets.at[index, 'throughput'] = int(min(row['rcwnd'] * 8 / 1000 / (row['rtt'] / 1000), bandwidth))

    data.throughput = packets['throughput'].tolist()
    print(f"Throughput: {data.throughput[:5]}")
    # TOTAL THROUGHPUT 
    # total_throughput = packets['tcppayloadlen'].sum() * 8 / 1000 / (duration / 1000) #TODO: errore ??? --> controllare col file sulla vm
    total_throughput = sum(data.throughput) / sum(data.rtt) * 1000
    print(f"Total throughput: {total_throughput} kbps")
    print(f"Average Throughput: {sum(data.throughput) / len(data.throughput)} kbps")

    # MAX THROUGHPUT #TODO: here
    # max_throughput = max(data.throughput)
    # print(f"Maximum Throughput: {max_throughput} kbps")

    # EFFICIENCY //TODO: could be correct, we will see...
    packets = packets[packets['rtt'] != 0]
    packets['usage'] = packets.apply(lambda row: row['tcppayloadlen'] * 8 / (row['rtt'] * 1000) if row['rtt'] != 0 else 0, axis=1)

    data.efficiency = packets['usage'].mean() * 100
    print(f"Average usage: {data.efficiency} %")

    # SRTT
    data.srtt = []
    for i, rtt in enumerate(data.rtt):
        if i == 0:
            data.srtt.append(rtt)
        else:
            srtt = (1 - ConnectionData.ALPHA) * data.srtt[i - 1] + ConnectionData.ALPHA * rtt
            data.srtt.append(srtt)

    print(f"Smoothed RTT: {data.srtt[:5]}")

    # RTTVAR
    data.rttvar = []
    for i, rtt in enumerate(data.rtt):
        if i == 0:
            data.rttvar.append(rtt / 2)
        else:
            rttvar = (1 - ConnectionData.BETA) * data.rttvar[i - 1] + ConnectionData.BETA * abs(data.srtt[i] - rtt)
            data.rttvar.append(rttvar)

    print(f"RTT Variance: {data.rttvar[:5]}")

    # RTO
    data.rto = []
    for i, srtt in enumerate(data.srtt):
        rto = srtt + 4 * data.rttvar[i]
        data.rto.append(rto)

    print(f"Max RTO: {data.rto[:5]}")
    
    return data

def create_summary_table(folder: str, data: list[ConnectionData]): #TODO: fix here

    fig, ax = plt.subplots(figsize=(15, len(data) * 0.5 + 2))
    ax.axis('tight')
    ax.axis('off')

    table_data = [
        ["Experiment", "Duration (ms)", "Total Throughput (kbps)", "Average Throughput (kbps)", "Average RTT (ms)", "Efficiency (%)"]
    ]

    for i, exp_data in enumerate(data):
        table_data.append([
            f"Experiment {i + 1}",
            exp_data.duration,
            f"{sum(exp_data.throughput) / sum(exp_data.rtt) * 1000:.2f}",
            f"{sum(exp_data.throughput) / len(exp_data.throughput):.2f}",
            f"{sum(exp_data.rtt) / len(exp_data.rtt):.2f}",
            f"{exp_data.efficiency:.2f}"
        ])

    table = Table(ax, bbox=[0, 0, 1, 1])
    n_rows, n_cols = len(table_data), len(table_data[0])
    width, height = 1.0 / n_cols, 1.0 / n_rows
    for i in range(n_rows):
        for j in range(n_cols):
            facecolor = 'lightblue' if i == 0 else ('lightgrey' if i % 2 == 0 else 'white')
            table.add_cell(i, j, width, height, text=table_data[i][j], loc='center', facecolor=facecolor)

    table.set_fontsize(12)
    table.scale(1.2, 1.2)
    ax.add_table(table)

    plt.title('Summary of Experiments', fontsize=16)
    plt.savefig(folder + 'summary.png')
    plt.close()

def plot_single(filename : str, data : ConnectionData):
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    # Plot RTT
    axs[0, 0].plot(data.rtt, label='RTT')
    axs[0, 0].set_title('RTT')
    axs[0, 0].set_xlabel('Packet Index')
    axs[0, 0].set_ylabel('RTT (ms)')
    axs[0, 0].legend()

    # Plot SRTT
    axs[0, 1].plot(data.srtt, label='SRTT', color='orange')
    axs[0, 1].set_title('Smoothed RTT (SRTT)')
    axs[0, 1].set_xlabel('Packet Index')
    axs[0, 1].set_ylabel('SRTT (ms)')
    axs[0, 1].legend()

    # Plot RTT Variance
    axs[1, 0].plot(data.rttvar, label='RTT Variance', color='green')
    axs[1, 0].set_title('RTT Variance (RTTVAR)')
    axs[1, 0].set_xlabel('Packet Index')
    axs[1, 0].set_ylabel('RTTVAR (ms)')
    axs[1, 0].legend()

    # Plot RTO
    axs[1, 1].plot(data.rto, label='RTO', color='red')
    axs[1, 1].set_title('Retransmission Timeout (RTO)')
    axs[1, 1].set_xlabel('Packet Index')
    axs[1, 1].set_ylabel('RTO (ms)')
    axs[1, 1].legend()

    plt.tight_layout()
    plt.savefig(filename + '_rtt.png')

    # Plot Throughput
    deltaX = int(sum(data.rtt) / len(data.rtt))

    fig, ax1 = plt.subplots(figsize=(15, 10))

    color = 'tab:blue'
    ax1.set_xlabel(f'Packet Index (Segmented by {deltaX} ms)')
    ax1.set_ylabel('Throughput (kbps)', color=color)
    ax1.plot(range(0, len(data.throughput) * deltaX, deltaX), data.throughput, label='Throughput', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    color = 'tab:green'
    ax2.set_ylabel('RCWND (bytes)', color=color)
    ax2.plot(range(0, len(data.rcwnd) * deltaX, deltaX), data.rcwnd, label='RCWND', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.legend(loc='upper right')

    # Add vertical lines to represent segments
    for x in range(0, len(data.throughput) * deltaX, deltaX):
        ax1.axvline(x=x, color='orange', linestyle='dotted')

    plt.title('Throughput and RCWND')
    plt.tight_layout()
    plt.savefig(filename + '_throughput_rcwnd.png')

def plot_multiple(folder : str, data : list[ConnectionData]):

    # Plot RTT Distribution
    fig, ax = plt.subplots(figsize=(15, 10))

    for i, exp_data in enumerate(data):
        ax.hist(exp_data.rtt, bins=50, alpha=0.5, label=f'Experiment {i + 1}')

    ax.set_title('RTT Distribution Across Experiments')
    ax.set_xlabel('RTT (ms)')
    ax.set_ylabel('Frequency')
    ax.legend()

    plt.tight_layout()
    plt.savefig(folder + 'rtt_distribution.png')

if __name__ == "__main__":
    pcap_path = "./pcap/"
    data_path = "./data/"
    tables_path = "./tables/"
    single_plots_path = "./plots/single/"
    multiple_plots_path = "./plots/multiple/"

    # Create directories if unexisting
    os.makedirs(pcap_path, exist_ok=True)
    os.makedirs(data_path, exist_ok=True)
    os.makedirs(tables_path, exist_ok=True)
    os.makedirs(single_plots_path, exist_ok=True)
    os.makedirs(multiple_plots_path, exist_ok=True)

    experiments = []

    try:
    
        pcap_files = [f for f in os.listdir(pcap_path) if os.path.isfile(os.path.join(pcap_path, f))]
        for pcap_file in pcap_files:
            file_name = pcap_file.split('.')[0]
            os.system(f"python pcapparser.py {os.path.join(pcap_path, pcap_file)} {os.path.join(data_path, file_name)}")
            os.remove(os.path.join(data_path, file_name + ".xlsx"))
        
        files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
        for i, file in enumerate(files):
            file_name = file.split('.')[0]
            file_path = os.path.join(data_path, file)
            plots_path = single_plots_path + file_name
            data = analyze_data(file_path, i)
            experiments.append(data)
            plot_single(plots_path, data)
        create_summary_table(tables_path, experiments)
        plot_multiple(multiple_plots_path, experiments)
    
    except Exception as e:
        print(f"An error occurred: {e}")