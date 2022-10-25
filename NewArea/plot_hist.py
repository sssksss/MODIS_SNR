#!/usr/bin/env python
# -*-coding=utf-8-*-
import h5py
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy import stats
# plt.style.use('ggplot')

if __name__ == '__main__':

    bandNum = 10
    dir_path = '/RED1BDATA_A/SNR/XWW/file/Amer_West/3B/20150729/Band{}/'.format(bandNum)

    solz = []

    file_list = os.listdir(dir_path)
    for file in file_list:
        file_path = dir_path + file
        print (file_path)
        file_data = h5py.File(file_path,'r')
        try:
            ori_solz = file_data['SolZ_2'][:]
            new_solz = ori_solz[np.where(ori_solz!=0)]
            # band_Ltypical.append(np.mean(new_refFactor) * Es[str(bandNum)]) # 原始的Ltypical
            # band_Ltypical.append(np.mean(new_refFactor) * Es[str(bandNum)] * 0.001 / np.pi)# 加入0.1/pi
            solz.extend(new_solz)
            # print new_refFactor

            # print band_Ltypical
        except:
            print ('file error!')

    fig,ax = plt.subplots(figsize=(16,9))
    n,bins,patches = ax.hist(solz, bins=80, normed=True, color='b', alpha=0.6, histtype='bar', rwidth=0.8)

    ax.set_xlabel('Solz',fontsize=20)
    ax.set_ylabel('Percentage',fontsize=20)
    ax.minorticks_on()
    # ax.set_title('Band10',fontsize=20)
    ax.tick_params(labelsize=20)

    # -------------------------------
    x_model = np.linspace(min(solz), max(solz))
    # ax.plot(x_model, stats.norm(50.21, 6.85).pdf(x_model), "r-", linewidth=4)
    ax.plot(bins, stats.norm(np.mean(solz), np.std(solz)).pdf(bins), "r-", linewidth=4)
    # -------------------------------


    plt.grid(True,linestyle='--')
    plt.title('MERSI Solz Max={},Min={},Mean={:.2f},Std={:.2f}'.format(np.max(solz),np.min(solz),np.mean(solz),np.std(solz)),fontsize=20)
    plt.savefig('/RED1BDATA_A/SNR/XWW/file/Amer_West/Pic/bandhist.png')
    plt.show()
