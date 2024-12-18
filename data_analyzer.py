import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table

class ConnectionData:
    """
    A class to represent the data of a TCP connection.
    Constants:
        NOBWLIM_BANDWIDTH (int): The bandwidth of the connection fpr the first experiment.
        BANDWIDTH (int): The bandwidth of the connection (based on the assignment).
        DELAY (int): The delay of the connection (based on the assignment).
        ALPHA (float): The alpha value for the SRTT calculation.
        BETA (float): The beta value for the RTTVAR calculation.
    Attributes:
        exp_name (str): The name of the experiment.
        duration (int): The duration of the capture in milliseconds.
        rcwnd (list[int]): The receiver's congestion window.
        average_rcwnd (float): The average receiver's congestion window.
        throughput (list[int]): The throughput for each packet.
        average_throughput (float): The average throughput.
        total_throughput (float): The total throughput.
        max_throughput (float): The maximum throughput.
        average_use (float): The average efficiency of the connection.
        rtt (list[int]): The round-trip time for packets.
        average_rtt (float): The average round-trip time.
        srtt (list[float]): The smoothed round-trip time.
        average_srtt (float): The average smoothed round-trip time.
        rttvar (list[float]): The round-trip time variance.
        average_rttvar (float): The average round-trip time variance.
        rto (list[float]): The retransmission timeout.
        average_rto (float): The average retransmission timeout.
    """

    NOBWLIM_BANDWIDTH = 100000 # kb per second
    BANDWIDTH = 11100 # kb per second #TODO: set based on the assignment 
    DELAY = 42 # milliseconds #TODO: set based on the assignment
    CLIENT_IP = ['192.168.1.10', '192.168.1.11']
    SERVER_IP = ['192.168.1.20', '192.168.1.21']
    ALPHA = 0.125
    BETA = 0.25

    exp_name = None # string
    duration = None # milliseconds
    rcwnd = None # bytes
    average_rcwnd = None # bytes
    throughput = None # kb per second
    average_throughput = None # kb per second
    total_throughput = None # kb
    max_throughput = None # kb per second
    average_use = None #eta, %
    rtt = None # milliseconds
    average_rtt = None # milliseconds
    srtt = None # milliseconds
    average_srtt = None # milliseconds
    rttvar = None # milliseconds
    average_rttvar = None # milliseconds
    rto = None # milliseconds
    average_rto = None # milliseconds

    def __str__(self):
        return (
            f"----------{self.exp_name}----------\n"
            f"duration:\t\t{self.duration} ms\n"
            f"average_rcwnd:\t\t{self.average_rcwnd:.2f} bytes\n"
            f"average_throughput:\t{self.average_throughput:.2f} kb/s\n"
            f"total_throughput:\t{self.total_throughput:.2f} kb\n"
            f"max_throughput:\t\t{self.max_throughput:.2f} kb/s\n"
            f"average_use:\t\t{self.average_use:.2f} %\n"
            f"average_rtt:\t\t{self.average_rtt:.2f} ms\n"
            f"average_srtt:\t\t{self.average_srtt:.2f} ms\n"
            f"average_rttvar:\t\t{self.average_rttvar:.2f} ms\n"
            f"average_rto:\t\t{self.average_rto:.2f} ms\n"
            f"---------------------------\n"
        )
def analyze_data(file : str, exp_name : str) -> ConnectionData :
    """
    Analyzes TCP connection data from a CSV file and computes various metrics.
    Args:
        file (str): The path to the CSV file containing the packet data.
        exp_name (str): The name of the experiment, used to determine bandwidth.
    Returns:
        ConnectionData: An object containing the analyzed data and computed metrics.
    The function performs the following analyses:
        - Extracts the experiment name from the file name.
        - Calculates the duration of the capture in milliseconds.
        - Computes the round-trip time (RTT) for packets.
        - Removes client-to-server packets from the dataset.
        - Calculates the receiver's congestion window (rcwnd) and its average.
        - Computes the throughput for each packet and calculates total, average, and maximum throughput.
        - Calculates the efficiency of the connection.
        - Computes the smoothed RTT (SRTT) and its average.
        - Computes the RTT variance (RTTVAR) and its average.
        - Calculates the retransmission timeout (RTO) and its average.
    """

    packets = pd.read_csv(file)
    data : ConnectionData = ConnectionData()
    bandwidth = ConnectionData.NOBWLIM_BANDWIDTH if exp_name == "nobwlim" else ConnectionData.BANDWIDTH

    # EXP NAME
    data.exp_name = exp_name

    # DURATION
    data.duration = int(packets['captureTime'].iloc[-1] * 1000)
    
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
    data.average_rtt = sum(data.rtt) / len(data.rtt)
    
    # REMOVE CLIENT TO SERVER PACKETS
    packets = packets.drop(client_to_server.index)

    # RCWND
    data.rcwnd = (packets['rcwnd']).tolist()
    data.average_rcwnd = sum(data.rcwnd) / len(data.rcwnd)

    # THROUGHPUT
    packets['throughput'] = 0
    for index, row in packets.iterrows():
        if row['rtt'] != 0:
            packets.at[index, 'throughput'] = int(min(row['rcwnd'] * 8 / 1000 / (row['rtt'] / 1000), bandwidth))

    data.throughput = packets['throughput'].tolist()
    
    # TOTAL THROUGHPUT
    data.total_throughput = sum(data.throughput) / sum(data.rtt) * 1000
    data.average_throughput = sum(data.throughput) / len(data.throughput)

    # MAX THROUGHPUT
    data.max_throughput = max([throughput / rtt for throughput, rtt in zip(data.throughput, data.rtt) if rtt != 0])
    
    # EFFICIENCY
    packets = packets[packets['rtt'] != 0]
    packets['usage'] = packets.apply(lambda row: row['tcppayloadlen'] * 8 / (row['rtt'] * 1000) if row['rtt'] != 0 else 0, axis=1)

    data.average_use = packets['usage'].mean() * 100

    # SRTT
    data.srtt = []
    for i, rtt in enumerate(data.rtt):
        if i == 0:
            data.srtt.append(rtt)
        else:
            srtt = (1 - ConnectionData.ALPHA) * data.srtt[i - 1] + ConnectionData.ALPHA * rtt
            data.srtt.append(srtt)
    data.average_srtt = sum(data.srtt) / len(data.srtt)

    # RTTVAR
    data.rttvar = []
    for i, rtt in enumerate(data.rtt):
        if i == 0:
            data.rttvar.append(rtt / 2)
        else:
            rttvar = (1 - ConnectionData.BETA) * data.rttvar[i - 1] + ConnectionData.BETA * abs(data.srtt[i] - rtt)
            data.rttvar.append(rttvar)
    data.average_rttvar = sum(data.rttvar) / len(data.rttvar)

    # RTO
    data.rto = []
    for i, srtt in enumerate(data.srtt):
        rto = srtt + 4 * data.rttvar[i]
        data.rto.append(rto)
    data.average_rto = sum(data.rto) / len(data.rto)
    
    return data

def create_summary_table(folder: str, data: dict[str, ConnectionData]): #TODO: implement this --> to create a table as a summary
    pass

def plot_single(filename : str, data : ConnectionData): #TODO: implement this --> to plot graphs for each experiment
    pass

def plot_multiple(folder : str, data : dict[str, ConnectionData]): #TODO: implement this --> to plot graphs for multiple experiments together
    pass

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

    experiments = {
        "nobwlim" : None,
        "s1" : None,
        "s2" : None,
        "p1" : None,
        "p2" : None
    }

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
            data = analyze_data(file_path, file_name)
            print(data)
            experiments[file_name] = data
            plot_single(plots_path, data)
        create_summary_table(tables_path, experiments)
        plot_multiple(multiple_plots_path, experiments)
    
    except Exception as e:
        print(f"An error occurred: {e}")