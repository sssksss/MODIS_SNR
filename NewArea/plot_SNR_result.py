# -*-coding=utf-8-*-

import matplotlib.pyplot as plt
import traceback


if __name__ == '__main__':

    band = list(range(8, 17))
    SNR_0 = [394.785896, 489.055759, 402.994968, 448.761161, 461.210449, 397.645846, 424.304678, 502.824639, 461.592693]
    SNR_1 = [405.041783, 501.7606, 413.464112, 460.419236, 473.191934, 407.976029,	435.327416,	515.887192,	473.584109]
    SNR_2 = [385.271585, 477.269552, 393.282818, 437.946049, 450.095309,388.062608, 414.07896, 490.706601, 450.468344]
    fig, ax = plt.subplots(1,1,figsize=(16, 9), dpi=300)
    print dir(ax)
    ax.plot(band, SNR_0, '*-k', lw=3, label='SNR')
    ax.plot(band, SNR_1, 'o-.r', lw=1, label='SNR R-5%')
    ax.plot(band, SNR_2, 'o-.b', lw=1, label='SNR R+5%')
    ax.set_xlabel('Band Number')
    ax.set_ylabel('SNR')
    ax.grid(which="both", axis="both")
    ax.set_ylim(300, 650)
    ax.legend()
    plt.savefig('/RED1BDATA_A/SNR/XWW/file/Amer_West/Pic/SNR_RESULT.png')
    print band


