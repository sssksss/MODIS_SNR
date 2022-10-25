#coding:utf-8
import numpy as np


class CalNoise(object):

	def __init__(self,RefSBData,windowShape,threshold):
		self.RefSBData = RefSBData
		self.windowShape = windowShape
		self.threshold = threshold


	def calProcess(self):
		# print('====================')
		# print('start calNoise:')
		#补一圈0
		for count in range(4):
			colum = self.RefSBData.shape[0]
			padding = np.zeros(colum)
			self.RefSBData = np.c_[self.RefSBData,padding].T
		# print self.RefSBData.shape#(1802, 2050)
		#滑动窗口
		r, c = self.windowShape
		shape = (self.RefSBData.shape[0] - r + 1, self.RefSBData.shape[1] - c + 1) + self.windowShape
		strides = self.RefSBData.strides * 2

		#得到小窗口矩阵self.rollingWinsowData,维度是(1800, 2048, 3, 3)
		self.rollingWindowData = np.lib.stride_tricks.as_strided(self.RefSBData, shape=shape, strides=strides)
		# print self.rollingWinsowData
		# self.rollingWindowData[self.rollingWindowData == 65535] = 0#无效值均为0,过滤计算完的ref没有65535

		#判断每个窗口是否有0值，返回0-1矩阵,有0值窗口标记为0，全为有效非0窗口标记1
		MaskMatrix = ~np.any(self.rollingWindowData == 0,(2,3)) + 0
		# print MaskMatrix


		self.rollingWindowData = np.where(self.rollingWindowData, self.rollingWindowData, np.nan)  # 0值转为nan值
		MinData = np.nanmin(self.rollingWindowData, (2, 3))
		MaxData = np.nanmax(self.rollingWindowData, (2, 3))

		MaxMinMask = MaxData / MinData
		# print "type MaxMinMask:",type(MaxMinMask)
		where_are_NaNs = np.isnan(MaxMinMask)
		MaxMinMask[where_are_NaNs] = 0

		MaxMinMask[MaxMinMask > self.threshold] = 0
		MaxMinMask[MaxMinMask != 0] = 1
		print self.rollingWindowData

		# #计算STD
		NoiseData = np.nanstd(self.rollingWindowData, (2, 3),ddof=1)


		###小窗口均匀性分析 过滤
		##计算窗口噪声的std和mean,用mean±3*std作为阈值筛选窗口；

		# NoiStd = np.nanstd(NoiseData)
		# stdMean = np.nanmean(NoiseData)



		# self.stdMeanData = stdMean * MaskMatrix
		# meanData = np.nanmean(self.rollingWindowData, (2, 3))

		# self.cv = (stdData / meanData) * MaskMatrix
		# self.cv = np.where(self.cv, self.cv, np.nan)



		# #过滤不符合阈值和小窗口存在0的STD
		self.Noise = NoiseData * MaxMinMask *MaskMatrix


		return self.Noise


