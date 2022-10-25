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
		self.SunA[self.SunA < 0] += 36000
		self.SunZ[self.SunZ < 0] += 36000
		self.SatA[self.SatA < 0] += 36000
		self.SatZ[self.SatZ < 0] += 36000
		self.Azimuth = abs(self.SatA - self.SunA)
		radfactor = np.pi / 180

		self.fSGA = np.arccos(np.sin(self.SunZ* 0.01 * radfactor)*np.sin(
			self.SatZ * 0.01 * radfactor) * np.cos(self.Azimuth * 0.01 * radfactor)
		    + np.cos(self.SunZ * 0.01 * radfactor) * np.cos(self.SatZ * 0.01 * radfactor))

		self.fSGA  = self.fSGA * 180 / np.pi
		# print self.fSGA
		self.fSGA[self.fSGA <= 35] = 0
		self.fSGA[self.fSGA > 35] = 1
		return self.fSGA







