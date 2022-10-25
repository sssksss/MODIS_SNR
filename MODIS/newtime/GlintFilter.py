#coding:utf-8
import numpy as np


class GlintFilter(object):

	def __init__(self, SunSatData):
		# print SunSatData
		self.SunA = SunSatData['SolarA']
		self.SunZ = SunSatData['SolarZ']
		self.SatA = SunSatData['SensorA']
		self.SatZ = SunSatData['SensorZ']

	def GlintProcess(self):
		"""
		修改MODIS角度的计算方式
		:return:
		"""

		self.SunA[self.SunA < 0] += 360
		self.SunZ[self.SunZ < 0] += 360
		self.SatA[self.SatA < 0] += 360
		self.SatZ[self.SatZ < 0] += 360
		self.Azimuth = abs(self.SatA - self.SunA)

		radfactor = np.pi / 180.0

		self.fSGA = np.arccos(np.sin(self.SunZ * radfactor)*np.sin(self.SatZ * radfactor) * np.cos(self.Azimuth * radfactor) + np.cos(self.SunZ * radfactor) * np.cos(self.SatZ  * radfactor))

		self.fSGA = self.fSGA * 180.0 / np.pi

		self.fSGA[self.fSGA <= 35] = 0
		self.fSGA[self.fSGA > 35] = 1
		print 'self.fSGA.shape', self.fSGA.shape
		return self.fSGA







