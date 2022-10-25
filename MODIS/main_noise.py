# coding:utf-8
from scipy.interpolate import spline
from scipy import stats
from numpy.linalg import cholesky
import math
from scipy.stats import kstest, anderson, shapiro, normaltest, norm
import matplotlib
matplotlib.use('Agg')
from matplotlib import patheffects
from matplotlib.ticker import AutoMinorLocator
from matplotlib.pyplot import MultipleLocator
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt

import os
import glob
import numpy as np
from h5py import File
import sys
import pandas as pd
import datetime
import time
from multiprocessing import Pool
import traceback

from FilterRef import FilterRef
from FilterRefA import FilterRefA
from FilterRefC import FilterRefC
from LonLatFilter import *
from GlintFilter import *
from ChlaFilter import *
from CalNoise import *

import warnings

warnings.filterwarnings("ignore")


text_config = dict(
    path_effects=[
        patheffects.Stroke(
            linewidth=3,
            foreground='white',
            alpha=0.8),
        patheffects.Normal()])


# -----------------------------------------------------def cal noise------
def readRefData(file):
    with File(file, 'r') as f:
        # for idx, key in enumerate(f.keys()):
        # 	if key == "RefFactor_3_GlintMask":
        RefDset = f["RefFactor_3_GlintMask"].value
    return RefDset


def main(bandNUM, threshold, day):
    # 计算MERSI的DN值噪声
    # FY3A
    # baseFilePath = '/RED1BDATA_A/SNR/XWW/file/3A/%s/Band%s/' % (day, bandNUM)
    # FY3C
    # baseFilePath = '/RED1BDATA_A/SNR/XWW/file/3C/%s/Band%s/' % (day, bandNUM)
    # MODIS
    baseFilePath = '/RED1BDATA_A/SNR/XWW/file/MODIS/resultChangeLoc/%s/Band%s/' % (day, bandNUM)

    if not baseFilePath:
        print "no valid ref file;"
        exit()

    # FY3A
    # noiseBasePath = "/RED1BDATA_A/SNR/XWW/file/3A/noise/%s/Band%s/noise/" % (day, bandNUM)
    # FY3C
    # noiseBasePath = "/RED1BDATA_A/SNR/XWW/file/3C/noise/%s/Band%s/noise/" % (day, bandNUM)
    # MODIS
    noiseBasePath = "/RED1BDATA_A/SNR/XWW/file/MODIS/resultChangeLoc/noise/%s/Band%s/" % (day, bandNUM)

    # 获取HDF文件列表
    HDF_list = glob.glob(baseFilePath + "*.HDF")
    print HDF_list
    if len(HDF_list) > 0:
        for hdfName in HDF_list:
            bandData = readRefData(hdfName)
            bandData[bandData < 0.0] = 0.0

            # Noise存入中间文件
            fileName = hdfName.split('/')[-1][:-4] + "_"
            thTemp = str(round(threshold, 4)).split('.')

            if np.any(bandData):
                noiseData = CalNoise(bandData, (3, 3), threshold).calProcess()

            noisePath = noiseBasePath + "noise" + thTemp[0] + thTemp[1] + "/"
            if not os.path.exists(noisePath):
                os.makedirs(noisePath)
                print "makeDirnoisePath:", noisePath
            noiseFile = noisePath + fileName + "noise" + thTemp[0] + thTemp[1] + '.HDF'
            print "noiseFile:", noiseFile

            f = File(noiseFile, 'w')
            f.create_dataset('noise_refFactor', data=noiseData, compression='gzip')
            print "save Noise OK;"


def _main(args):
    try:
        main(*args)
        return args, 'success'
    except:
        traceback.print_exc()
        return args, 'fail'


# ----------------------------------------------------draw picture--------


def dataProcess(HDF_list, dataSetName):
    drawData = []
    count = 0
    # print "len(HDF_list)", len(HDF_list)
    # 无效值是nan
    for filename in HDF_list:
        f = File(filename, 'r')

        Data = f[dataSetName].value.ravel()
        Data[Data <= 0] = np.nan  # 无效值都设置nan;
        flag = np.where(np.isnan(Data))
        # print flag
        Data = np.delete(Data, flag, axis=0)
        Data = Data.tolist()
        # print(Data)
        drawData += Data
        f.close()
    # count += 1
    # print(count)
    # print "dataProcess OK!!"
    return drawData


def to_percent(y, position):
    return "%.1f%%" % (y * 100)



def drawHistogram(satName,dataSetName,xLabel,fileNum,picType,bandNum,titelTh,thrMin=0,thrMax=0):
    # print "picSavePath:",picSavePath
    # 1、path可以是一个文件全路径，也可以是一个文件夹路径,也可以直接是数组；
    # 2、dataSetName：HDF文件中的dataset名字；
    # 3、图片X轴名字xLabel;
    # 4、fileNum=1传的是一个文件全路径，fileNum > 1传的是一个文件夹路径，fileNum = 0直接是数组;
    # 5、picType:频次（counts）统计还是 百分比统计（percentage）;
    # 6、thrMin,thrMax：画图阈值，均默认为0；
    pfmter = matplotlib.ticker.FuncFormatter(to_percent)
    figsize = (8, 6)
    fig = plt.figure(figsize=figsize)
    # 读取noise
    # FY3A
    # inputData = "/RED1BDATA_A/SNR/XWW/file/3A/noise/"
    # FY3C
    # inputData = "/RED1BDATA_A/SNR/XWW/file/3C/noise/"
    # FY3B
    inputData = "/RED1BDATA_A/SNR/XWW/file/3B/noise/"


    # 输出图像
    # FY3A
    # picSavePath = "/RED1BDATA_A/SNR/XWW/file/3A/picture/%s/"%(bandNum)
    # FY3C
    # picSavePath = "/RED1BDATA_A/SNR/XWW/file/3C/picture/%s/"%(bandNum)
    # FY3B
    picSavePath = "/RED1BDATA_A/SNR/XWW/file/3B/image/20151027/%s/"%(bandNum)


    if not os.path.exists(picSavePath):
        os.makedirs(picSavePath)

    dayList = []
    pathList = []

    dirList = titelTh.split('.')
    dir = "noise" + dirList[0] + dirList[1]

    # for i in range(2,31):
    begin = datetime.date(2015, 10, 27)
    end = datetime.date(2015, 10, 27)

    for i in range((end - begin).days + 1):
        day = begin + datetime.timedelta(days=i)
        day = str(day).split("-")
        day = "".join(day)
        pathTemp = inputData + day + "/Band" + bandNum + '/' + 'noise/' + dir + "/"
        print(pathTemp)
        if not os.path.exists(pathTemp):
            continue

        pathList.append(pathTemp)
        dayList.append(day)
    # print "len(dayList):", len(dayList)

    # print pathList
    HDF_list = []
    for p in pathList:
        # print "p:",p
        for root, dirs, files in os.walk(p):
            HDF_list += [root + i for i in files if i.endswith(".HDF")]
    # print("len(HDF_list):",HDF_list)
    drawList = dataProcess(HDF_list, dataSetName)  # 返回的无效值都是nan

    drawData = np.array(drawList)

    print(HDF_list)
    picname = HDF_list[0].split("/")[-1][:-4] + '_%s_Band%s.png' % (picType,bandNum)
    picname = picname.split('_')

    if xLabel == 'Ref':
        del picname[-4]
    if xLabel == 'CV' or xLabel == "Max/Min":
        del picname[-5]
    if xLabel == 'noise':
        picname[1] = HDF_list[-1].split("/")[-3]
        # print(HDF_list[-1].split("/"))
        del picname[3]
    picname = "_".join(picname)
    picSaveAllPath = picSavePath + picname
    # print "picSaveAllPath:", picSaveAllPath
    # print "drawData:", drawData
    # 考虑画图阈值范围,超出范围均设置0；
    if float(thrMin) > 0 or float(thrMax) > 0:
        drawData[drawData < float(thrMin)] = np.nan
        drawData[drawData > float(thrMax)] = np.nan

    # drawData[drawData < 0] = 0
    # flag = np.where(drawData == 0.0000)
    # print flag
    # drawData = np.delete(drawData, flag, axis=0)
    # drawData[drawData==0] = np.nan
    # drawData = drawData.flatten().tolist()
    # drawData = drawData.ravel().tolist()
    # print "Band" + bandNum + ":drawDataOk;"
    # drawData.remove(0)

    # 画图

    if len(drawData) > 0:
        ax1 = plt.subplot2grid((1, 1), (0, 0))

        if picType == 'counts':
            # print "start picType == 'counts';"
            n, bins, patches = plt.hist(drawData, bins=10, normed=1, color='b')  # normed=0为统计counts
            # ax1.plot(drawData,color='b')  # normed=0为统计counts
            plt.ylabel('$Counts$', fontsize=15)
            y = numpy.array(n, 'f8')
            y = y / y.sum()
            x = (bins[1:] + bins[:-1]) / 2.
            area_size = ((bins[1:] - bins[:-1]) * y).sum()
            x_smooth = np.linspace(bins[0], bins[-1], 600)
        elif picType == 'percentage':
            # n, bins, patches = ax1.hist(drawData, bins=35, normed=1, color='b')
            hist, bins = np.histogram(drawData, bins=10)
            n = hist
            y = numpy.array(hist, 'f8')
            y = y / y.sum()  # [float(i) / float(hist.sum()) for i in list(hist)]
            x = (bins[1:] + bins[:-1]) / 2.
            area_size = ((bins[1:] - bins[:-1]) * y).sum()
            plt.ylabel('$Percentage$', fontsize=15)
            ax1.yaxis.set_major_formatter(FuncFormatter(to_percent))
            ######平滑化
            x_smooth = np.linspace(bins[0], bins[-1], 600)
            y_smooth = spline(x, y, x_smooth)
            y_smooth[y_smooth < 0] = 0
            ax1.plot(x_smooth, y_smooth, label='$Percentage(%.4f)$' % float(titelTh))
            ax1.xaxis.set_minor_locator(AutoMinorLocator())
            ax1.yaxis.set_minor_locator(AutoMinorLocator())
        else:
            assert 0
        # 原始数值drawData的mu和sigma
        mu = round(np.nanmean(drawData), 7)
        sigma = round(np.nanstd(drawData), 7)
        # print "MERSI_Data:", mu, sigma

        #######################拟合线##################
        # mu_model, sigma_model = stats.norm.fit(drawData)

        ynorm = stats.norm(mu, sigma).pdf(x_smooth) * area_size

        ax1.plot(x_smooth, ynorm, "r-", linewidth=2,
                 label="$Normal\ Fitted\ Line$")
        # print "666"

        # modelData = stats.norm.rvs(loc=mu_model, scale=sigma_model, size=len(drawData))
        # 第1种方法画拟合线
        # y = mlab.normpdf(bins,mu_model,sigma_model)
        # ax1.plot(bins, y, "g-", linewidth=2)

        # 第2种方法画拟合线
        # print "4444"
        # x = np.linspace(mu - 3 * sigma, mu + 3 * sigma, 50)
        # y_sig = np.exp(-(x - mu) ** 2 / (2 * sigma ** 2)) / (math.sqrt(2 * math.pi) * sigma)
        # print "555"

        # # ax1.plot(x, y_sig, "r-", linewidth=2)
        # print "666"

        # print "拟合线：", np.nanmean(y_sig), np.nanstd(y_sig)

        maxdata = round(np.nanmax(drawData), 7)
        mindata = round(np.nanmin(drawData), 10)

        # title = "MERSI:Band%s(20150601),Max/Min_th=%s,$\mu=%s$,$\sigma=%s$,min=%s,max=%s"%(bandNum,titelTh,mu,sigma,mindata,maxdata)
        title = "%s_MERSI: Band %s (%s - %s)\n min=%s, max=%s" % (satName,
            bandNum, dayList[0], dayList[-1], mindata, maxdata)
        plt.title(title)

        plt.xlabel('$%s$' % xLabel)
        plt.legend(frameon=False, fontsize=15)

        # print "picSaveAllPath:",picSaveAllPath
        plt.grid(True)

        text = "$Mean\ Noise: %.5g\ {\pm}\ %.5g$" % (mu, sigma)
        if picType == 'percentage':
            rr = (np.abs(ynorm - y_smooth) * (bins[1] - bins[0])).sum()
            print titelTh,rr
            text += "\n${\Delta}Area:\ %.5g$" % rr
        x1, x2 = ax1.get_xlim()
        y1, y2 = ax1.get_ylim()
        px = x1 * .97 + x2 * .03
        py = y1 * .03 + y2 * .97
        ax1.text(px, py, text, fontsize=15, verticalalignment='top', horizontalalignment='left', **text_config)
        # ax1.yaxis.set_major_formatter()
        # ax1.set_xlim(x1, x2)
        plt.savefig(picSaveAllPath, dpi=300)
        print "save Done!!!!!!"
        plt.clf()
    # print 'mu:',mu,'sigma:',sigma
    else:
        print "no Valid Data;"





def _drawHistogram(args):
    try:
        drawHistogram(*args)
        return args, 'success'
    except:
        traceback.print_exc()
        return args, 'fail'


if __name__ == "__main__":
    # -----------------------------------------filter data-----------------------------------------------
    # cmd：python main.py FY3B MERSI 20150604 9
    # args = sys.argv[1:]
    # if len(args) == 4:
    #     sat = args[0]
    #     sensor = args[1]
    #     YYMMDD = args[2]
    #     bandNUM = args[3]
    # else:
    #     print "input params error, exit"
    #     sys.exit(-1)
    #
    # if sat == "FY3B":
    #     FilterRef(sat, sensor, YYMMDD, bandNUM).filterData()
    # elif sat == "FY3A":
    #     print "3A Go+++"
    #     FilterRefA(sat, sensor, YYMMDD, bandNUM).filterData()
    # elif sat=='FY3C':
    #     FilterRefC(sat, sensor, YYMMDD, bandNUM).filterData()

    # -----------------------------------------------cal noise----------------

    dayList = []
    begin = datetime.date(2015, 7, 29)
    end = datetime.date(2015, 7, 29)
    for i in range((end - begin).days + 1):
        day = begin + datetime.timedelta(days=i)
        day = str(day).split("-")
        day = "".join(day)
        dayList.append(day)
    # --------------------------原始-----------------------------------
    thList = np.arange(1.002, 1.055, 0.0005) # np.arange(1.0085, 1.015, 0.0005)
    BandList = [1,2,3,4,5,6,7,8,9,10,11,12,'13L','13H','14L','14H',15,16,17,18,19,26]  # int
    # BandList = [8, 9, 10,]  # int
    # BandList = [8, ]  # int

    # ---------------------------0209 修改噪声参数-----------------------
    r = Pool(20)
    args = [(str(band), threshold, str(day),) for band in BandList for threshold in thList for day in dayList]
    for i in r.imap_unordered(_main, args):
    	print i


    # -----------------------------------------------draw image------------------------------------------------
    # bandList = ['6','7','8','9','10','11','12','13','14','15','16','17','18','19','20' ]  # str
    # bandList = ['8','9','10']  # str
    # bandList = ['8',]  # str
    # thList = np.arange(1.002, 1.015, 0.0005) # (1.0085, 1.015, 0.0005)
    # --------------------------------------0209修改-------------------------------
    # r = Pool(20)
    # args = [('FY3B',"noise_refFactor", 'noise', 2, 'percentage', str(band), str(round(th, 4))) for band in bandList for th in
    #         thList]
    # print args
    # for i in r.imap_unordered(_drawHistogram, args):
    # 	print i
