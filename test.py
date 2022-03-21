import matplotlib.pyplot as plt
import numpy as np
import dpkt

beamformer_mac = b"\xe8\x4e\x06\x95\x29\x24"
beamformee_mac = b"\xe8\x4e\x06\x95\x28\xcd"


def main():
    filename = '/Volumes/EDISK/ndprate_result/test_plot/rtl8814.pcap'
    fig, [ax1, ax2] = plt.subplots(ncols=1, nrows=2, figsize=(20, 14), dpi=100)
    num_subcarrier = 0
    x1 = []
    x2 = []
    Z1 = []
    Z2 = []
    for ts, pkt in dpkt.pcap.Reader(open(filename, 'rb')):
        # print(ts)
        try:
            rad = dpkt.radiotap.Radiotap(pkt)
            frame = rad.data
            if frame.type == 0 and frame.subtype == 14:
                if frame.mgmt.src == beamformer_mac:
                    x1.append(ts)
                    num_subcarrier = frame.action_no_ack.VHT.num_subcarriers
                    Z1.append([a[1] for a in frame.action_no_ack.VHT.angles])
                elif frame.mgmt.src == beamformee_mac:
                    x2.append(ts)
                    num_subcarrier = frame.action_no_ack.VHT.num_subcarriers
                    Z2.append([a[1] for a in frame.action_no_ack.VHT.angles])
        except Exception as e:
            # print("[E]: ", e)
            pass

    ref_time_1 = x1[0]
    x1 = [t - ref_time_1 for t in x1]
    y = [i for i in range(num_subcarrier)]
    Z1 = np.array(Z1)
    ref_time_2 = x2[0]
    x2 = [t - ref_time_2 for t in x2]
    Z2 = np.array(Z2)

    vmin = min(np.min(Z1), np.min(Z2))
    vmax = max(np.max(Z1), np.max(Z2))
    pcm = ax1.pcolormesh(x1, y, Z1.transpose(), cmap='rainbow', vmin=vmin, vmax=vmax)
    ax1.set_xlabel("Elapsed Time (Seconds)", fontsize=15)
    ax1.set_ylabel("Subcarrier Index", fontsize=15)
    ax1.set_title('Angle $\psi_{21}$ of Beamformer', fontsize=18)
    fig.colorbar(pcm, ax=ax1)


    pcm = ax2.pcolormesh(x2, y, Z2.transpose(), cmap='rainbow', vmin=vmin, vmax=vmax)
    ax2.set_xlabel("Elapsed Time (Seconds)", fontsize=15)
    ax2.set_ylabel("Subcarrier Index", fontsize=15)
    ax2.set_title('Angle $\psi_{21}$ of Beamformee', fontsize=18)
    fig.colorbar(pcm, ax=ax2)
    plt.show()


if __name__ == '__main__':
    main()
    # dpkt.ieee80211.test_80211_action_no_ack()
