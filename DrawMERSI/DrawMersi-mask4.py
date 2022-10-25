#!/usr/bin/env python
# coding: utf-8
import h5py
import numpy as np
import matplotlib.pyplot as plt
import sys, glob
import math
import warnings;

warnings.filterwarnings('ignore')
import datetime, os, h5py, glob, time  # , Ngl
import numpy as np
import matplotlib.pyplot as plt
import shutil
from PIL import Image, ImageDraw

LandCoverType = ['Water', 'Evergreen Needleleaf Forest', 'Evergreen Broadleaf Forest',
                 'Deciduous Needleleaf Forest', 'Deciduous Broadleaf Forest', 'Mixed Forests',
                 'Closed Shrublands', 'Open Shrublands', 'Woody Savannas', 'Savannas', 'Grasslands',
                 'Permanent Wetlands', 'Croplands', 'Urban and Built-Up', 'Cropland/Natural Vegetation Mosaic',
                 'Snow and Ice', 'Barren or Sparsely Vegetated',
                 '(IGBP Water Bodies, recoded to 0 for MODIS Land Product consistency.)']

CloudPhaseType = ['水云', '冰云', '冰水混合云', '', '薄卷云']


def mkcb(a, b):
    cb = np.arange(4096, dtype='f4')
    cb *= a
    cb += b
    cb *= 0.01
    cb -= 0.06
    cb[cb < 0] = 0
    cb[cb > 1] = 1
    return cb


CB = mkcb(0.02542, - 3.253)
CG = mkcb(0.02682, - 3.609)
CR = mkcb(0.02783, - 6.913)

STABLE = np.linspace(0, 1, 2048)
STABLE **= 0.4
STABLE *= 255
STABLE1 = STABLE.astype('u1')


def Chrange(d, steps=2047):
    d[0] = CR[d[0]] * steps
    d[1] = CG[d[1]] * steps
    d[2] = CB[d[2]] * steps
    d = d.astype('u2')
    return STABLE1[d]


# return d

def DrawRGB(Refdata, LandSeaMask, points):
    print("start DrawRGB;")
    # print(points)
    d = Refdata[(2, 1, 0),]
    d[d > 4095] = 4095
    rgb = Chrange(d)
    imrgb = Image.fromarray(rgb.transpose(1, 2, 0), 'RGB')
    lsm = (LandSeaMask == 2).astype('u1')
    lsm *= 255
    coastline = Image.fromarray(255 - lsm, 'L')
    alpha = Image.fromarray(lsm, 'L')
    # imrgb.paste(coastline,mask=alpha) # color image
    t = np.empty((1, 1), 'u1')
    t.fill(255)
    alpha = Image.fromarray(t, 'L')
    imd = ImageDraw.ImageDraw(imrgb)
    N = iter(xrange(2550))
    N.next()
    redrect = Image.new("RGB", (1, 1))
    redrect.im.fillband(0, 255)
    print("len(point):", len(points))
    for x, y in points:
        imrgb.paste(redrect, (y, x), alpha)
    # imd.text((y-8,x-8-10),"%d"% N.next(),(255,0,0))
    # imd.text((y - 8, x - 8 - 10))
    # print "Y=",y,"X=",x
    # outFile = 'tmp.png'
    imrgb.save(outFile)
    # imrgb = imrgb.resize((2000, 2048))

    return


outFile = 'aa.png'


# def main(HIRASFile, MERSI1KMFile,MERSIGeoFile, CLPFile):
def main(refFactorFile, MERSI1KMFile, tempOutFile, dataset):
    # /RED1BDATA/EXE/SNR/SNR/v4/20150604_2225_validRefFactor_Band9.HDF /FYDISK/DATA/FY3/FY3B/MERSI/L1/1000M/2015/20150604/FY3B_MERSI_GBAL_L1_20150604_2225_1000M_MS.HDF /FYDISK/DATA/FY3/FY3B/MERSI/L1/GEO/2015/20150604/FY3B_MERSI_GBAL_L1_20150604_2225_GEOXX_MS.HDF
    global outFile
    fid_hdf1 = h5py.File(refFactorFile, "r")
    print(refFactorFile)
    # MERSI_refFactor = np.array(fid_hdf1['validRef'])
    MERSI_refFactor = np.array(fid_hdf1[dataset])
    # noise图
    MERSI_refFactor[np.isnan(MERSI_refFactor)] = 0.0
    print(MERSI_refFactor)

    outFile = tempOutFile
    # outFile="/RED1BDATA/EXE/SNR/SNR/v4/1"+".png"
    fid_hdf2 = h5py.File(MERSI1KMFile, "r")
    Latitude_MERSI = np.array(fid_hdf2['Latitude'])
    Longitude_MERSI = np.array(fid_hdf2['Longitude'])
    LandCover_MERSI = np.array(fid_hdf2['LandCover'])
    LandSeaMask_MERSI = np.array(fid_hdf2['LandSeaMask'])
    MERSI_RefSB = np.array(fid_hdf2['EV_250_Aggr.1KM_RefSB'])  # 获取原始band9

    earth = 6371.0
    Rad1Deg = 0.017453292
    Pi = math.pi
    mersi_sz = np.array(Latitude_MERSI).shape
    mersi_sz_col = mersi_sz[1]

    Hiras_loc_Mersi_col = []
    Hiras_loc_Mersi_row = []
    LandCover = []
    CloudPhase = []
    MERSI_1KM_RefSB = []

    iIndex = 1
    temp = list(np.where(MERSI_refFactor != 0.0))
    f = open("./1.txt", 'w')
    f.write(str(temp))
    f.close()
    n1, n2 = np.array(temp[0]), np.array(temp[1])
    print("len(n1):", len(n1))
    for Step in range(len(n1)):
        FindFlag = True
        # 有效MERSI_refFactor与MERSI观测区域匹配
        if FindFlag == True:
            hiras_loc_row = n1[Step]
            hiras_loc_col = n2[Step]
            MERSI_RefSB_RGB = MERSI_RefSB[:, hiras_loc_row - 8:hiras_loc_row + 8,
                              hiras_loc_col - 8: hiras_loc_col + 8]  # band9
            Hiras_loc_Mersi_col.append(hiras_loc_col)
            Hiras_loc_Mersi_row.append(hiras_loc_row)

            LandCover.append(LandCover_MERSI[hiras_loc_row, hiras_loc_col])

            MERSI_1KM_RefSB.append(MERSI_RefSB_RGB)
            iIndex += 1
    # fpReadMe.close()
    # print(Hiras_loc_Mersi_row,Hiras_loc_Mersi_col)
    points = zip(Hiras_loc_Mersi_row, Hiras_loc_Mersi_col)
    # print(points)
    DrawRGB(MERSI_RefSB, LandSeaMask_MERSI, points)


if __name__ == '__main__':
    # refFactorFile, MERSI1KMFile,tempOutFile,dataset
    # python DrawMersi.py ./DrawRGB.HDF /FYDISK/DATA/FY3/FY3B/MERSI/L1/1000M/2015/20150604/FY3B_MERSI_GBAL_L1_20150604_2225_1000M_MS.HDF ./2RefFactor9_band3Mask.png 2RefFactor9_band3Mask
    # file = h5py.File("/RED1BDATA/EXE/SNR/SNR/v4/DrawRGB.HDF", "r")
    dayList = []
    begin = datetime.date(2015, 3, 27)
    end = datetime.date(2015, 3, 27)
    for i in range((end - begin).days + 1):
        day = begin + datetime.timedelta(days=i)
        day = str(day).split("-")
        day = "".join(day)
        dayList.append(day)
    print "!!!dayList", dayList

    for i in dayList:
        # inputPath = "/RED1BDATA/FIXSITE/SNR/MERSI/AllRegionValidRef/2015ceshi/2015/v6/validRefFactor/%s/Band9/" % i
        # inputPath = "/RED1BDATA_A/SNR/XWW/file/3B/%s/Band8/" % i
        inputPath = "/RED1BDATA_A/SNR/XWW/file/new_ref/20150327/"
        print inputPath

        hdfList = glob.glob(inputPath + "*.HDF")
        for f in hdfList:
            # YMD_HM = "20150610_1550"
            # f = "/RED1BDATA/FIXSITE/SNR/MERSI/AllRegionValidRef/2015ceshi/2015/v6/validRefFactor/20150610/Band9/20150610_1550_validRefFactor_Band9.HDF"
            YMD_HM = f.split('/')[-1][:13]
            noise_th = f.split('/')[-1][-8:-4]
            print(noise_th)
            # print(YMD_HM)
            file = h5py.File(f, "r")
            print("len(file.keys()):", len(file.keys()))
            dateset = file.keys()
            # main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])

            for ds in dateset:
                # savePath = "/RED1BDATA/FIXSITE/SNR/MERSI/AllRegionValidRef/2015ceshi/2015/v6/validRefFactor/pic_008/"
                savePath = "/RED1BDATA_A/SNR/XWW/draw_image/20150327/"
                if not os.path.exists(savePath):
                    os.makedirs(savePath)
                if ds == "RefFactor_4_GlintMask":
                    # if ds == "RefData_band3":
                    # if ds == "noise_refFactor":
                    main(f, "/FYDISK/DATA/FY3/FY3B/MERSI/L1/1000M/2015/%s/FY3B_MERSI_GBAL_L1_%s_1000M_MS.HDF" % (
                    i, YMD_HM), savePath + "%s_%s_1111noise%s.png" % (YMD_HM, ds, noise_th), ds)
