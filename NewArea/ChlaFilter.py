#coding:utf-8
from h5py import File
import numpy
import sys
import os
import numpy as np



'''
maxlon = latlon[4]
minlon = latlon[2]
maxlat = latlon[1]
minlat = latlon[3]
'''

class ChlaFilter(object):

	def __init__(self, chalFile,RefLon,RefLat):
		#ChlaLonLat叶绿素经纬度分辨率9km,一天一个文件,RefLonLat反射率经纬度分辨率1KM五分钟时次
		#剔除叶绿素值ChlaData大于0.2mg/m3,最终返回RefLonLat反射率经纬度中符合条件的下标
		self.RefLon = RefLon
		self.RefLat = RefLat
		self.chalFile = chalFile


	def mwork(self):

		y = 90 - self.RefLat
		x = self.RefLon + 180
		y *= 12
		x *= 12
		x[x == 4320] = 0
		x = x.astype('i2')
		y = y.astype('i2')


		with File(self.chalFile, 'r') as f:
				data = f['chlor_a'].value
		cla = data[y, x]




		# # cla[cla >= 0.07] = -32767
		# cla[cla >= 0.2] = -32767
		#
		# cla[cla == -32767] = 0
		# cla[cla > 0] = 1
		# # print cla
		return cla





