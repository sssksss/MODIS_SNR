# -*-coding=utf-8-*-
import os,sys,glob
import h5py
import numpy as np
import datetime
import time
from pyhdf.SD import SD,SDC

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


def SunZenCorrect(r, sunz):
    '''
    Solar zenith angle correction for VIS Channel
    '''
    for i in range(0, 20, 1):
        # print 'SunZenCorrect-ch:',i
        index = np.where(r[i] > 0)
        # print 'index[0]:',index[0],index[1]
        cossza = np.cos(sunz[index] * PI / 180.0)
        r[i, index[0], index[1]] = r[i, index[0], index[1]] / cossza


class FilterRef():
	def __init__(self,sat,sensor,YYMMDD,bandNUM):
		self.sat = sat
		self.sensor = sensor #FY3B
		self.year = YYMMDD[:4]
		self.month = YYMMDD[4:6]
		self.day = YYMMDD[6:]
		self.bandNum = bandNUM
		self.YYMMDD = YYMMDD

		self.L1BasePath = '/RED1BDATA_B/SNO/AQUA_MODIS_OneMonthOneDay/MYD021KM/%s/152/' % (self.year)
		# print self.L1BasePath
		# 获取HDF文件列表
		# for root, dirs, files in os.walk(self.L1BasePath):
		# 	self.HDF_list = [root + i for i in files if i.endswith(".hdf")]
		self.HDF_list = glob.glob(self.L1BasePath+'*.hdf')

		self.HDF_list.sort(key=lambda x: str(x[-34:-21]))  # 按时间顺序排列
		# print self.HDF_list
		# self.L1BasePath = '/RED1BDATA_A/SNR/XWW/file/MODIS/MYD021KM/2015/211/MYD021KM.A2015211.2025.061.2018051010821.hdf'

	def readData(self, fileName):
		LonLat_data = {}
		SunSat_data = {}
		try:
			h4File = SD(fileName, SDC.READ)
			# print h4File
			band_1_2 = h4File.select('EV_250_Aggr1km_RefSB').get()
			_, self.row, self.col = band_1_2.shape
			print 'self.row:', self.row
			band_3_7 = h4File.select("EV_500_Aggr1km_RefSB").get()  # band3 648.63nm对应modis666nm,band4 863.49nm对应modis 865nm
			band_8_26 = h4File.select("EV_1KM_RefSB").get()  # band3 648.63nm对应modis666nm,band4 863.49nm对应modis 865nm
 
			band_1_2_s = h4File.select('EV_250_Aggr1km_RefSB').attributes()['reflectance_scales']
			band_1_2_o = h4File.select('EV_250_Aggr1km_RefSB').attributes()['reflectance_offsets']
			band_3_7_s = h4File.select("EV_500_Aggr1km_RefSB").attributes()['reflectance_scales']
			band_3_7_0 = h4File.select("EV_500_Aggr1km_RefSB").attributes()['reflectance_offsets']
			band_8_26_s = h4File.select("EV_1KM_RefSB").attributes()['reflectance_scales']
			band_8_26_o = h4File.select("EV_1KM_RefSB").attributes()['reflectance_offsets']
			# print 'band_8_26_s is: ', band_8_26_s # 2*2030*1354
			# print band_1_2_o
			band_1_2_ref = np.array([[[np.nan] * self.col] * self.row] * 2)
			band_3_7_ref = np.array([[[np.nan] * self.col] * self.row] * 5)
			band_8_26_ref = np.array([[[np.nan] * self.col] * self.row] * 15)

			print band_1_2_ref.shape

			for i in range(0, 2):
				# print 'band_1_2 shape is: ', band_1_2[i].shape
				# band_1_2_ref[i] = (band_1_2[i] - band_1_2_o[i]) * band_1_2_s[i] * 0.01
				band_1_2_ref[i] = (band_1_2[i] - band_1_2_o[i]) * band_1_2_s[i]

			for i in range(0, 5):
				# band_3_7_ref[i] = (band_3_7[i] - band_3_7_0[i]) * band_3_7_s[i] * 0.01
				band_3_7_ref[i] = (band_3_7[i] - band_3_7_0[i]) * band_3_7_s[i]

			for i in range(0, 15):
				# band_8_26_ref[i] = (band_8_26[i] - band_8_26_o[i]) * band_8_26_s[i] * 0.01
				band_8_26_ref[i] = (band_8_26[i] - band_8_26_o[i]) * band_8_26_s[i]

			# sys.exit(-1)
			# LonLat_data['Lon'] = h5File.get('/Longitude')[:]
			# LonLat_data['Lat'] = h5File.get('/Latitude')[:]
			# SunSat_data['SolarA'] = h5File.get('/SolarAzimuth')[:]
			# SunSat_data['SolarZ'] = h5File.get('/SolarZenith')[:]
			# SunSat_data['SensorA'] = h5File.get('/SensorAzimuth')[:]
			# SunSat_data['SensorZ'] = h5File.get('/SensorZenith')[:]
		except Exception as e:
			print str(e)
			print "Modis L1 data open error."
			return -1


		# GEO
		try:
			# find geo file
			repalce_result = fileName.replace('MYD021KM', 'MYD03')[0:71]
			Geo_file = glob.glob(repalce_result+'*')
			print 'L1 file:', fileName
			# print 'GEO File :', Geo_file
			h4FileGeo = SD(Geo_file[0], SDC.READ)
			lon = h4FileGeo.select('Longitude').get()
			lat = h4FileGeo.select('Latitude').get()
			# 角度信息 需要加scale factor
			satz = h4FileGeo.select('SensorZenith').get()
			satz_s = h4FileGeo.select('SensorZenith').attributes()['scale_factor']
			sata = h4FileGeo.select('SensorAzimuth').get()
			sata_s = h4FileGeo.select('SensorAzimuth').attributes()['scale_factor']
			sunz = h4FileGeo.select('SolarZenith').get()
			sunz_s = h4FileGeo.select('SolarZenith').attributes()['scale_factor']
			suna = h4FileGeo.select('SolarAzimuth').get()
			suna_s = h4FileGeo.select('SolarAzimuth').attributes()['scale_factor']

			LonLat_data['Lon'] = lon
			LonLat_data['Lat'] = lat
			SunSat_data['SolarA'] = suna * suna_s
			SunSat_data['SolarZ'] = sunz * sunz_s
			SunSat_data['SensorA'] = sata * sata_s
			SunSat_data['SensorZ'] = satz * satz_s

		except Exception as e:
			print str(e)
			print "Modis GEO data open error."
			return -1


		return band_8_26_ref, band_3_7_ref, band_1_2_ref, LonLat_data, SunSat_data


	def CalRef(self, bandData, L1File, band13, band16, SolZ):  ###Band3(648.63nm)反射率阈值0.1过滤
		print '***********************'

		band_dict = {
			'1':0,
			'2':1,
			'3':2,
			'4':3,
			'5':4,
			'6':5,
			'7':6,
			'8':7,
			'9':8,
			'10':9,
			'11':10,
			'12':11,
			'13L':12,
			'13H':13,
			'14L':14,
			'14H':15,
			'15':16,
			'16':17,
			'17':18,
			'18':19,
			'19':20,
			'26':21,
		}


		bandData = bandData[band_dict[self.bandNum]]
		condition = np.logical_not(bandData > 0 )  # 无效值均为0
		index = np.where(condition)  # 无效值的index

		print("index:", index.__len__())  # 19个，band1-4,20-10

		# （4）计算反射率因子；
		RefFactor = bandData
		RefFactor_band3 = band13
		RefFactor_band4 = band16

		################################
		# print 'SolZ is :', SolZ
		print 'SolZ shape:', SolZ.shape
		condition = np.logical_not(SolZ <= 70) #滤除太阳天顶角大于70的区域
		# condition = np.logical_or(SolZ > 41, SolZ < 39)  # 只选择45+-1度区域
		index_SolZ = np.where(condition)  # 不要的区域
		cossza = np.cos(SolZ * PI / 180.0)

		# 计算ref值
		# ==================================================
		print("start Cal REF:")
		# RefData_band3 = RefFactor_band3 / dss / cossza / 100
		# 角度矫正（MODIS无DSS）
		RefData_band3 = RefFactor_band3 / cossza

		# 无效值
		RefData_band3[RefData_band3<0] = 0
		RefData_band3[index_SolZ] = 0

		# 存RefFactor
		RefFactor[index] = 0
		# n, _, _ = RefFactor.shape
		# index 数据纬度为2 RefF
		# for i in range(0, n):
		RefFactor[index_SolZ] = 0

		# 保留校正后的band3 <0.08,band4<0.07
		print RefData_band3.min()
		print RefData_band3.max()

		RefData_band3[RefData_band3 > 0.08] = 0
		RefData_band3[RefData_band3 < 0] = 0


		RefData_band3[RefData_band3 > 0] = 1


		SolZ = SolZ * RefData_band3

		RefFactor_band3Mask = RefFactor * RefData_band3

		RefFactor = RefFactor_band3Mask

		RefFactor[RefFactor == -0.0] = 0

		return RefFactor*100, SolZ, RefData_band3


	def filterData(self,):
		print self.HDF_list
		# self.HDF_list = ['/RED1BDATA_A/SNR/XWW/file/MODIS/MYD021KM/2015/211/MYD021KM.A2015211.2025.061.2018051010821.hdf ']
		for L1File in self.HDF_list:
			band_8_26, band_3_7, band_1_2, LonLat_data, SunSat_data = self.readData(L1File)
			# band_6_20, band_1_4, LonLat_data, SunSat_data = self.readData(L1File)
			print 'band_1_2.shape:', band_1_2.shape
			print 'band_3_7.shape:', band_3_7.shape
			print 'band_8_26.shape:', band_8_26.shape
			# buid band 1-26
			band_1_26 = np.concatenate((band_1_2, band_3_7, band_8_26))
			print 'create 8-26 band date ', band_1_26.shape

			# band_13 = band_1_26[12] #类似band3作用
			band_13 = band_1_26[0] #类似band3作用
			print'band13=65535', (band_13!=65535).any()
			band_16 = band_1_26[13] #类似band4作

			if band_1_26.any():
				# GEO文件获取LonLat和角度信息
				HMS = L1File.split('.')[2] + L1File.split('.')[3] # 时次2220061
				# 1.深海区域经纬度筛选，经纬度0-1过滤矩阵：LonLatMask
				try:
					LonLatMask = LonLatFilter(LonLat_data, self.row, self.col).LonLatProcess()  # 0-1矩阵
				except ValueError:
					# MODIS的有的数据纬度不一致
					pass
				print 'Lon Lat fitter result:', LonLatMask.any()
				if LonLatMask.any():
					# 2.耀斑角筛选，耀斑角0-1过滤矩阵：SunSatMask   #35度
					SunSatMask = GlintFilter(SunSat_data).GlintProcess()  # 0-1矩阵
					# print "SunSat_data", SunSat_data
					print "SUNsatMASK", SunSatMask.any()

					# 3.过滤经纬度、耀斑角、云，计算反射率
					if SunSatMask.any():
						print 'cal refFactor'
						# 计算反射率之前 无效值都为0；

						RefFactor, SolZ, RefData_band3  = self.CalRef(band_1_26, L1File, band_13, band_16, SunSat_data['SolarZ'])  # RefFactor没有矫正


						RefData1 = RefFactor * LonLatMask
						# RefData1 = RefFactor
						RefData2 = RefData1 * SunSatMask

						# SolZ2 = SolZ * LonLatMask * SunSatMask
						SolZ2 = SolZ * SunSatMask
						print("Filter Ref Over;")

						if RefData2.any():
							print "%s_%s:refData valid!!!!!" % (self.YYMMDD, HMS)
							validRefPath = '/RED1BDATA_A/SNR/XWW/file/MODIS/result152/%s/Band%s/' % (self.YYMMDD, str(self.bandNum))
							if not os.path.exists(validRefPath):
								os.makedirs(validRefPath)

							# #Ref存中间文件
 							# print 'Newslope:', newSlope
							f = File(
								validRefPath + '%s_%s_validRefFactor_Band%s.HDF' % (self.YYMMDD, HMS, str(self.bandNum)),
								'w')
							# f.create_dataset('LONLATMask', data=LonLatMask, compression='gzip')
							f.create_dataset('GlintMask', data=SunSatMask, compression='gzip')
							f.create_dataset('RefFactor_1', data=RefFactor, compression='gzip')
							f.create_dataset('SolZ_1', data=SolZ, compression='gzip')
							f.create_dataset('RefData_band3', data=RefData_band3, compression='gzip')
							# f.create_dataset('newSlope', data=newSlope)

							f.create_dataset('RefFactor_2_LONLATMask', data=RefData1, compression='gzip')
							f.create_dataset('RefFactor_3_GlintMask', data=RefData2, compression='gzip')
							f.create_dataset('SolZ_2', data=SolZ2, compression='gzip')
							print "valid validRefFactor save over:", validRefPath


						else:
							print "%s_%s:validRefFactor invalid!!!!!" % (self.YYMMDD, HMS)
					# else:
					#
					# 	print 'no Lon Lat data'
					# 	pass