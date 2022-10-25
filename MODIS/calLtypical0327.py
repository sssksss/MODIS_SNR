#!/usr/bin/env python
# -*-coding=utf-8-*-
import datetime
import os
import h5py
import numpy as np

if __name__ == '__main__':



    bandNum = '3'
    noise = {
        'percentage': 0.020609,

    }

    Es = {
        '1':1608.05,
        '2':991.33,
        '3':2088.17,
        '4':1865.27,
        '5':474.94,
        '6':240.61,
        '7':90.4,
        '8':1747.74,
        '9':1906.19,
        '10':1977.14,
        '11':1885.26,
        '12':1892.84,
        '13L':1547.47,
        '13H':1547.47,
        '14L':1506.12,
        '14H':1506.12,
        '15':1294.69,
        '16':973.5,
        '17':934.5,
        '18':872.39,
        '19':873.11,
        '26':365.07,
    }
    # 0327原R
    S0 = {
        '1': 0.028513756,
        '2':0.013310088,
        '3':0.097783138,
        '4':0.050401368,
        '5':0.005973087,
        '6':0.004249983,
        '7':0.002919179,
        '8':0.152312617,
        '9':0.120789284,
        '10':0.087257635,
        '11':0.062114969,
        '12':0.054546841,
        '13H':0.02707202,
        '13L':0.02707202,
        '14H':0.026063129,
        '14L':0.026063129,
        '15':0.019108854,
        '16':0.013892713,
        '17':0.009883662,
        '18':0.011721689,
        '19':0.011712023,
        '26':0.008132153,

    }

    # R-5%
    S1 = {
        '1': 0.160618056,
        '2': 0.109738144,
        '3': 0.297439839,
        '4': 0.213544464,
        '5': 0.073513414,
        '6': 0.06200986,
        '7': 0.051392236,
        '8': 0.371223186,
        '9': 0.33058364,
        '10': 0.280975771,
        '11': 0.237063826,
        '12': 0.222152884,
        '13H': 0.156504735,
        '13L': 0.156504735,
        '14H': 0.153560823,
        '14L': 0.153560823,
        '15': 0.131487502,
        '16': 0.112114217,
        '17': 0.094564058,
        '18': 0.102982219,
        '19': 0.102939749,
        '26': 0.085776816,
    }

    # R+5%
    S2 = {
        '1': 0.168860166,
        '2': 0.115369353,
        '3': 0.312702954,
        '4': 0.224502491,
        '5': 0.077285752,
        '6': 0.065191894,
        '7': 0.054029427,
        '8': 0.390272491,
        '9': 0.347547528,
        '10': 0.295394034,
        '11': 0.249228748,
        '12': 0.233552651,
        '13H': 0.16453577,
        '13L': 0.16453577,
        '14H': 0.161440792,
        '14L': 0.161440792,
        '15': 0.138234778,
        '16': 0.117867355,
        '17': 0.09941661,
        '18': 0.108266748,
        '19': 0.108222099,
        '26': 0.09017845,

    }




    begin = datetime.date(2015, 7, 29)
    end = datetime.date(2015, 7, 29)



    for i in range((end - begin).days + 1):
        day = begin + datetime.timedelta(days=i)
        day = str(day).split("-")
        day = "".join(day)
        dir_path = '/RED1BDATA_A/SNR/XWW/file/MODIS/result1/{}/Band{}/'.format(day, bandNum)
        file_list = os.listdir(dir_path)
        print os.path.join(dir_path, file_list[0])
        for filename in file_list:

            file_path = dir_path + filename
            file_data = h5py.File(file_path, 'r')
            try:
                ori_refFactor = file_data['RefFactor_3_GlintMask'][:]
                new_refFactor = ori_refFactor[np.where(ori_refFactor > 0)]
                ref = new_refFactor * 0.01
                print ref.shape

                # exit(-1)
            except:
                print 'file error!'

    SZA_mean = np.round(np.nanmean(ref), 5)
    SZA_std = np.round(np.nanstd(ref), 5)
    N2 = noise['percentage']/100 * S0[str(bandNum)] / np.sqrt(SZA_mean)
    SNR = (SZA_mean) / N2
    print ''.center(80, '*')
    print u'人工区域统计'
    print u'SNR：', SNR
    print u'相对噪声：',N2


    print 'mean: ', SZA_mean
    print 'std:  ', SZA_std


    print 'my: ',SZA_mean/SZA_std








