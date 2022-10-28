#coding:utf-8
import numpy as np
import pandas as pd



class LonLatFilter(object):
	def __init__(self, LonLatData, row,col):
		self.LonLatData = LonLatData
		#self.LonLat_limit = [{'LonLimit': [-32.3, -11], 'LatLimit': [-19.9, -9.9]}]
		#所有区域
		# self.LonLat_limit = [{'LonLimit': [-32.3, -11], 'LatLimit': [-25, 0]}]
		self.LonLat_limit = [{'LonLimit': [-150.1, -120.1], 'LatLimit': [15.1, 45.1]}]
		# self.LonLat_limit = [{'LonLimit': [-130.2, -89], 'LatLimit': [-44.9, -20.7]},
		# 					 {'LonLimit': [139.5, 165.6], 'LatLimit': [10, 22.7]},
		# 					 {'LonLimit': [179.4, 180], 'LatLimit': [15, 23.5]},
		# 					 {'LonLimit': [-180, -159.4], 'LatLimit': [15, 23.5]},
		# 					 {'LonLimit': [-62.5, -44.2], 'LatLimit': [17, 27]},
		# 					 {'LonLimit': [-32.3, -11], 'LatLimit': [-19.9, -9.9]},
		# 					 {'LonLimit': [89.5, 100.1], 'LatLimit': [-29.9, -21.2]}]
		self.LonLatMask = np.zeros((row, col))

	def fileterProcess(self, minLimit, maxLimit, Data):
		Data[Data > maxLimit] = -999.0
		Data[Data < minLimit] = -999.0
		Data[Data > -999.0] = 1
		Data[Data == -999.++ 0] = 0
		return Data

	def LonLatProcess(self):
		for limitRegion in self.LonLat_limit:
			self.LonLatData['Lon'] = np.array(self.LonLatData['Lon'])
			self.LonLatData['Lat'] = np.array(self.LonLatData['Lat'])

			self.LonMask = self.fileterProcess(limitRegion['LonLimit'][0],limitRegion['LonLimit'][1],self.LonLatData['Lon'])
			self.LatMask = self.fileterProcess(limitRegion['LatLimit'][0],limitRegion['LatLimit'][1],self.LonLatData['Lat'])

			# print np.sum(self.LonMask),np.sum(self.LatMask)#0-1矩阵
			LonLatMask = self.LonMask + self.LatMask
			LonLatMask[LonLatMask < 2] = 0
			LonLatMask[LonLatMask == 2] = 1

			self.LonLatMask += LonLatMask #六块区域0-1叠加

		self.LonLatMask[self.LonLatMask > 0] = 1

		return self.LonLatMask
