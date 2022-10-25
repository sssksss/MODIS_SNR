# -*-coding=utf-8-*-
import os
from h5py import File
import numpy as np
import datetime
import time

from LonLatFilter import *
from GlintFilter import *
from ChlaFilter import *

PI = 3.14159265
FY3A_Sat_Time = "20080527"
FY3B_Sat_Time = "20101104"

FY3C_Sat_Time = "20130923"
FY3D_Sat_Time = "20171115"


# 用于日地距离矫正
def sun_ds2(yy, mm, dd):
	dss = 0.0
	ymd_hms1 = yy + '01' + "01" + "00:00:00"
	ymd_hms2 = yy + mm + dd + "00:00:00"

	timeStartstr = time.strptime(ymd_hms1, "%Y%m%d%H:%M:%S")
	timeStartStamp = time.mktime(timeStartstr)

	timeEndstr = time.strptime(ymd_hms2, "%Y%m%d%H:%M:%S")
	timeEndStamp = time.mktime(timeEndstr)

	# print 'timeStartStamp:',timeStartStamp
	# print 'timeEndStamp:',timeEndStamp

	time_Start = time.localtime(timeStartStamp)
	time_End = time.localtime(timeEndStamp)

	# print 'time_Start.tm_yday:',time_Start.tm_yday
	# print 'time_End.tm_yday:',time_End.tm_yday

	J = time_End.tm_yday - time_Start.tm_yday + 1.0
	# print 'J:',J
	OM = (0.9856 * (J - 4)) * PI / 180.0
	# print 'OM:',OM
	dss = 1.0 / ((1.0 - 0.01673 * np.cos(OM)) ** 2)
	# print 'dss:',dss

	return dss


class FilterRef():
	def __init__(self,sat,sensor,YYMMDD,bandNUM):
		self.sat = sat
		self.sensor = sensor #FY3B
		self.year = YYMMDD[:4]
		self.month = YYMMDD[4:6]
		self.day = YYMMDD[6:]
		self.bandNum = bandNUM
		self.YYMMDD = YYMMDD

		self.L1BasePath = '/FYDISK/DATA/%s/%s/%s/L1/1000M/%s/%s/'%(self.sat[:3],self.sat,self.sensor,self.year,YYMMDD)
		print self.L1BasePath
		# 获取HDF文件列表
		for root, dirs, files in os.walk(self.L1BasePath):
			self.HDF_list = [root + i for i in files if i.endswith(".HDF")]
		# self.HDF_list = ['/FYDISK/DATA/FY3/FY3B/MERSI/L1/1000M/2015/20150327/FY3B_MERSI_GBAL_L1_20150327_1530_1000M_MS.HDF']
		self.HDF_list.sort(key=lambda x: int(x[-17:-13]))  # 按时间顺序排列
		print self.HDF_list

	def readData(self, fileName):
		# filename:/FYDISK/DATA/FY3/FY3C/MERSI/L1/1000M/2015/20150104/FY3C_MERSI_GBAL_L1_20150104_0025_1000M_MS.HDF
		#          /FYDISK/DATA/FY3/FY3C/MERSI/L1/GEO1K/2015/20150104/FY3C_MERSI_GBAL_L1_20150104_0025_GEO1K_MS.HDF
		# h5File = File(fileName, 'r')
		LonLat_data = {}
		SunSat_data = {}

		with File(fileName) as h5File:
			band_6_20 = h5File.get('/EV_1KM_RefSB')[:]
			band_1_4 = h5File.get("/EV_250_Aggr.1KM_RefSB")[:]  # band3 648.63nm对应modis666nm,band4 863.49nm对应modis 865nm
			# print(fileName)
			LonLat_data['Lon'] = h5File.get('/Longitude')[:]
			LonLat_data['Lat'] = h5File.get('/Latitude')[:]
			SunSat_data['SolarA'] = h5File.get('/SolarAzimuth')[:]
			SunSat_data['SolarZ'] = h5File.get('/SolarZenith')[:]
			SunSat_data['SensorA'] = h5File.get('/SensorAzimuth')[:]
			SunSat_data['SensorZ'] = h5File.get('/SensorZenith')[:]
		return band_6_20, band_1_4, LonLat_data, SunSat_data



	def CalRef(self, bandData, L1File, band3_dn, band4_dn):  ###Band3(648.63nm)反射率阈值0.1过滤
		condition = np.logical_not(bandData != 0)  # 无效值均为0
		index = np.where(condition)  # 无效值的index
		dss = sun_ds2(self.year, self.month, self.day)
		DSL1 = datetime.datetime(int(self.year), int(self.month), int(self.day))

		DSL2 = datetime.datetime(int(FY3B_Sat_Time[0:4]), int(FY3B_Sat_Time[4:6]), int(FY3B_Sat_Time[6:8]))


		DSL = (DSL1 - DSL2).days
		print('DSL:', DSL)
		h5File = File(L1File, 'r')

		# (1)计算DN值
		# 计算slope
		if self.sat=='FY3B':
			Cal_Model_Coeff = h5File.get('/RSB_Cal_Cor_Coeff')[:]
			k0 = Cal_Model_Coeff[:, 0]
			k1 = Cal_Model_Coeff[:, 1]
			k2 = Cal_Model_Coeff[:, 2]


		Slope = k0 + k1 * DSL + k2 * (DSL ** 2)
		# print("oldslopeList:", Slope)
		SlopeData = Slope[int(self.bandNum) - 2]
		# print("band9 SlopeData:",SlopeData)
		SlopeData_band3 = Slope[2]
		SlopeData_band4 = Slope[3]


		# print("oldSlope:", SlopeData)  # 19个，band1-4,20-10

		slopeAttr = float(h5File['/EV_1KM_RefSB'].attrs['Slope'][0])  # 0.01
		InterceptAttr = float(h5File['/EV_1KM_RefSB'].attrs['Intercept'][0])  # 0
		svInput = h5File.get('/SV_1KM_RefSB')[int(self.bandNum) - 6]
		svData = np.array(2048 * [svInput]).T[0]  # (2000, 2048)

		svInput_band3 = h5File.get("/SV_250_Aggr1KM_RefSB")[2]
		svInput_band4 = h5File.get("/SV_250_Aggr1KM_RefSB")[3]
		svData_band3 = np.array(2048 * [svInput_band3]).T[0]  # (2000, 2048)
		svData_band4 = np.array(2048 * [svInput_band4]).T[0]  # (2000, 2048)
		SolZ = h5File['/SolarZenith'].value * 0.01

		if slopeAttr < 100:
			EV_DN = (bandData * 0.01 + InterceptAttr) / SlopeData + svData
			EV_DN_band3 = (band3_dn * 0.01 + InterceptAttr) / SlopeData_band3 + svData_band3
			EV_DN_band4 = (band4_dn * 0.01 + InterceptAttr) / SlopeData_band4 + svData_band4
		elif slopeAttr == 100:
			EV_DN = (bandData / 100 + InterceptAttr) / SlopeData + svData  ###无效的值会产生有效值！！！！！！！！后续会筛掉
			EV_DN_band3 = (band3_dn / 100 + InterceptAttr) / SlopeData_band3 + svData_band3
			EV_DN_band4 = (band4_dn / 100 + InterceptAttr) / SlopeData_band4 + svData_band4


		# 测试版
		# 要算EV值！！！用数据集中的EV = (refFactor/slope)+SV；
		# slope用RSB_Cal_Cor_Coeff,  SV用数据集的原始值;

		# （2）读取定标模型系数；
		with open("./FY3B_MERSI_CalModPar_v1.txt", "r") as f:
			CalModelCoeff = f.readlines()
		dataset = []
		temp = []
		for line in CalModelCoeff:
			data1 = line.strip('\n')  # 去掉开头和结尾的换行符
			data2 = line.split('\t')  # 把tab作为间隔符
			# print data2
			dataset.append(data2)  # 把这一行的结果作为元素加入列表dataset
		dataset = np.array(dataset)
		for i in dataset[:, 3]:
			i = i.strip('\n')
			temp.append(i)
		dataset[:, 3] = temp

		k0_Model = np.array(dataset[1:, 1], dtype='f4')
		k1_Model = np.array(dataset[1:, 2], dtype='f4')
		k2_Model = np.array(dataset[1:, 3], dtype='f4')

		# （3）计算slope；
		slope = k0_Model + k1_Model * DSL + k2_Model * (DSL ** 2)
		newSlope = slope[int(self.bandNum) - 2]
		# print('newSlope:',newSlope)
		newSlope_band3 = slope[2]
		newSlope_band4 = slope[3]

		# （4）计算反射率因子；
		svDnMean = h5File['/SV_DN_average'].value[int(self.bandNum) - 1]
		svMeanData = np.array(2048 * [svDnMean]).T
		# print("svMeanData[430][1212]:",svMeanData[430][1212])

		svDnMean_band3 = h5File['/SV_DN_average'].value[2]
		svMeanData_band3 = np.array(2048 * [svDnMean_band3]).T
		svDnMean_band4 = h5File['/SV_DN_average'].value[3]
		svMeanData_band4 = np.array(2048 * [svDnMean_band4]).T

		RefFactor = newSlope * (EV_DN - svMeanData)
		RefFactor_band3 = newSlope_band3 * (EV_DN_band3 - svMeanData_band3)
		RefFactor_band4 = newSlope_band4 * (EV_DN_band4 - svMeanData_band4)


		################################
		# band3和band4日地距离矫正
		condition = np.logical_not(SolZ <= 70) #滤除太阳天顶角大于70的区域
		# condition = np.logical_or(SolZ > 41, SolZ < 39)  # 只选择45+-1度区域

		index_SolZ = np.where(condition)  # 不要的区域

		cossza = np.cos(SolZ * PI / 180.0)


		# 计算ref值
		# =========================
		print("start Cal REF:")
		RefData_band3 = RefFactor_band3 / dss / cossza / 100

		RefData_band3[index] = 0
		RefData_band3[index_SolZ] = 0

		# 存RefFactor
		RefFactor[index] = 0
		RefFactor[index_SolZ] = 0

		# 保留校正后的band3 <0.08,band4<0.07
		RefData_band3[RefData_band3 > 0.08] = 0
		RefData_band3[RefData_band3 < 0] = 0


		RefData_band3[RefData_band3 > 0] = 1


		SolZ = SolZ * RefData_band3

		RefFactor_band3Mask = RefFactor * RefData_band3

		RefFactor = RefFactor_band3Mask

		RefFactor[RefFactor == -0.0] = 0

		return RefFactor, SolZ, RefData_band3, newSlope


	def filterData(self,):


		for L1File in self.HDF_list:

			print L1File
			band_6_20, band_1_4, LonLat_data, SunSat_data = self.readData(L1File)
			if self.bandNum >= 6:
				Band_DNDset = band_6_20[int(self.bandNum)-6] #获取对应通道的DN或者EV值
			else:
				Band_DNDset = band_1_4[int(self.bandNum)-1]
			band3_dn = band_1_4[2]
			band4_dn = band_1_4[3]

			if Band_DNDset.any():
				# GEO文件获取LonLat和角度信息
				HMS = L1File.split('_')[5]  # 时次
				# 1.深海区域经纬度筛选，经纬度0-1过滤矩阵：LonLatMask
				LonLatMask = LonLatFilter(LonLat_data).LonLatProcess()  # 0-1矩阵
				# print self.LonLatMask
				# if True:
				if LonLatMask.any():
					# 2.耀斑角筛选，耀斑角0-1过滤矩阵：SunSatMask   #35度
					SunSatMask = GlintFilter(SunSat_data).GlintProcess()  # 0-1矩阵
					# 3.过滤经纬度、耀斑角、云，计算反射率
					print 'SunSatMask is :', SunSatMask
					if SunSatMask.any():
						# 计算反射率之前 无效值都为0；
						RefFactor, SolZ, RefData_band3, newSlope = self.CalRef(Band_DNDset, L1File, band3_dn,
																			   band4_dn)  # RefFactor没有矫正
						print("Cal Ref Over;")

						RefData1 = RefFactor * LonLatMask
						# RefData1 = RefFactor
						RefData2 = RefData1 * SunSatMask

						# SolZ2 = SolZ * LonLatMask * SunSatMask
						SolZ2 = SolZ *  SunSatMask
						print("Filter Ref Over;")

						if RefData2.any():
							print "%s_%s:refData valid!!!!!" % (self.YYMMDD, HMS)
							validRefPath = '/RED1BDATA_A/SNR/XWW/file/Amer_West/3B/%s/Band%s/' % (self.YYMMDD, str(self.bandNum))
							if not os.path.exists(validRefPath):
								os.makedirs(validRefPath)

							# #Ref存中间文件
 							print 'Newslope:', newSlope
							f = File(
								validRefPath + '%s_%s_validRefFactor_Band%s.HDF' % (self.YYMMDD, HMS, str(self.bandNum)),
								'w')
							# f.create_dataset('LONLATMask', data=LonLatMask, compression='gzip')
							f.create_dataset('GlintMask', data=SunSatMask, compression='gzip')
							f.create_dataset('RefFactor_1', data=RefFactor, compression='gzip')
							f.create_dataset('SolZ_1', data=SolZ, compression='gzip')
							f.create_dataset('RefData_band3', data=RefData_band3, compression='gzip')
							f.create_dataset('newSlope', data=newSlope)

							f.create_dataset('RefFactor_2_LONLATMask', data=RefData1, compression='gzip')
							f.create_dataset('RefFactor_3_GlintMask', data=RefData2, compression='gzip')
							f.create_dataset('SolZ_2', data=SolZ2, compression='gzip')
							print "valid validRefFactor save over:", validRefPath


						else:
							print "%s_%s:validRefFactor invalid!!!!!" % (self.YYMMDD, HMS)