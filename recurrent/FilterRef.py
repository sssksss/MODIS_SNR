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


def LandSeaFilter(data):
	"""
	0
	1
	2
	3
	4
	5
	6
	7 深海

	:param LandSeaMask:
	:return:
	"""
	result = np.zeros_like(data)
	result[data==7]=1.
	return result

def SolarZFilter(data):
	result = np.zeros_like(data)
	index = (data<46.0)&(data>45.0)
	result[index]=1
	return result

def chlorFilter(data):
	result = np.zeros_like(data)
	index = (data>0)&(data<0.07)
	result[index]=1
	return result


class FilterRef():
	def __init__(self,sat,year,day,bandNUM):
		self.sat = sat
		self.year =year
		self.day = day
		self.bandNum = bandNUM


		self.L1BasePath = '/RED1BDATA_B/SNO/AQUA_MODIS_OneMonthOneDay/MYD021KM/%s/%s/' % (self.year,self.day)
		# print self.L1BasePath
		# 获取HDF文件列表
		# for root, dirs, files in os.walk(self.L1BasePath):
		# 	self.HDF_list = [root + i for i in files if i.endswith(".hdf")]
		self.HDF_list = glob.glob(self.L1BasePath+'*.hdf')

		self.HDF_list.sort(key=lambda x: str(x[-34:-21]))  # 按时间顺序排列

		self.HDF_RandanceL = 'R(L).hdf'



	def readData(self, fileName,bandNUM):
		LonLat_data = {}
		SunSat_data = {}

		bandNUM = int(bandNUM)

		h4File = SD(fileName, SDC.READ)
		# print h4File
		band = h4File.select('EV_1KM_RefSB').get()[bandNUM-8]
		self.row, self.col = band.shape
		print 'self.row:', self.row
		band_S = h4File.select("EV_1KM_RefSB").attributes()['radiance_scales'][bandNUM-8]
		band_O = h4File.select("EV_1KM_RefSB").attributes()['radiance_offsets'][bandNUM-8]
		band_data = (band-band_O)*band_S
		# 不知道 为啥为啥0.1 cm m 0.01？ Ltypical
		Rltypical = band_data*0.1
		# 这个方法应该还不对，后续找孙老师确认看看
		# bb = band_data*(1906.19)*0.01

		# match GEO file
		print ' match geo file: ',fileName.replace('MYD021KM','MYD03')[:-18]
		geo_filename_indedx = fileName.replace('MYD021KM','MYD03')[:-18]
		geo_filename = glob.glob(geo_filename_indedx+'*')[0]
		print geo_filename
		geo_file = SD(geo_filename, SDC.READ)
		# read data
		Latitude = geo_file.select('Latitude').get()
		Longitude = geo_file.select('Longitude').get()

		SensorZenith = geo_file.select('SensorZenith').get()
		SensorZenith_S = geo_file.select("SensorZenith").attributes()['scale_factor']
		SensorZ = SensorZenith * SensorZenith_S
		SensorAzimuth = geo_file.select('SensorAzimuth').get()
		SensorAzimuth_S = geo_file.select("SensorAzimuth").attributes()['scale_factor']
		SensorA = SensorAzimuth * SensorAzimuth_S
		SolarZenith = geo_file.select('SolarZenith').get()
		SolarZenith_S = geo_file.select("SolarZenith").attributes()['scale_factor']
		SolarZ = SolarZenith * SolarZenith_S
		SolarAzimuth = geo_file.select('SolarAzimuth').get()
		SolarAzimuth_S = geo_file.select("SolarAzimuth").attributes()['scale_factor']
		SolarA = SolarAzimuth* SolarAzimuth_S
		LandSeaMask = geo_file.select('Land/SeaMask').get()

		# match
		chlor_path = '/RED1BDATA_A/SNR/XWW/code/Recurrent/data/2019/121/'

		partname = os.path.basename(geo_filename)
		# print partname[7:11] #2019
		# print partname[11:14] #121
		# print partname[15:19] #0000

		# 匹配叶绿素a的数据，读取数据集
		# 如果匹配失败，停止执行后续操作。
		chlor_name = glob.glob(chlor_path + 'AQUA_MODIS.'+partname[7:11]+'*T'+partname[15:19]+'*.L2.OC.nc')

		if chlor_name:
			chlor_file = chlor_name[0]
			chlor_data = h5py.File(chlor_file,'r')
			# 注意叶绿素 当中的填充-32767 为无效的数据值，需要过滤掉
			chlor_a = chlor_data['geophysical_data/chlor_a'][()]
			readsave = h5py.File('/RED1BDATA_A/SNR/XWW/code/Recurrent/data/ReadSave/'+partname[7:11]+'_'+partname[11:14]+'_'+partname[15:19]+'.hdf','w')
			readsave['Latitude'] = Latitude
			readsave['Longitude'] = Longitude
			readsave['band_data'] = band_data
			readsave['Rltypical'] = Rltypical
			readsave['SensorZ'] = SensorZ
			readsave['SensorA'] = SensorA
			readsave['SolarZ'] = SolarZ
			readsave['SolarA'] = SolarA
			readsave['LandSeaMask'] = LandSeaMask
			readsave['chlor_a'] = chlor_a

			return [band_data, Rltypical, Latitude, Longitude, SensorZ, SensorA, SolarZ, SolarA, LandSeaMask, chlor_a]
		else:
			print 'no chlor-a file!'
			pass
			return None



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

		 
		for L1File in self.HDF_list:
			# 读取MODIS的EV_1KM_RefSB 9 通道
			# 天顶角 海陆掩码

			L1File = '/RED1BDATA_B/SNO/AQUA_MODIS_OneMonthOneDay/MYD021KM/2019/121/MYD021KM.A2019121.2145.061.2019122151635.hdf'
			print L1File

			result = self.readData(L1File,self.bandNum)
			if result:
				[band_data, Rltypical, Latitude, Longitude, SensorZ, SensorA, SolarZ, SolarA, LandSeaMask, chlor_a] = result

				L1_basename = os.path.basename(L1File)
				year = L1_basename[10:14]
				day =  L1_basename[14:17]
				tt = L1_basename[18:22]
				print year,day,tt

				if Rltypical.any():
					LonLat_data ={}
					LonLat_data['Lon'] = Longitude
					LonLat_data['Lat'] = Latitude

					# 1.深海区域经纬度筛选，经纬度0-1过滤矩阵：LonLatMask
					LonLatMask = LonLatFilter(LonLat_data, self.row, self.col).LonLatProcess()  # 0-1矩阵
					if LonLatMask.any()==1:
						fittersave = h5py.File('/RED1BDATA_A/SNR/XWW/code/Recurrent/data/FilterSave/{}_{}_{}_fitter.hdf'.format(year,day,tt), 'w')
						# 经纬度过滤
						fittersave['LonLatMask'] = LonLatMask
						# 海陆掩码过滤
						LandSeaMaskFilter = LandSeaFilter(LandSeaMask)
						print (LandSeaMaskFilter).dtype

						# 太阳天顶角过滤
						SolarZMask = SolarZFilter(SolarZ)

						# 叶绿素a过滤
						chlormask = chlorFilter(chlor_a)
						print chlormask


						fittersave['LandSeaMask'] = LandSeaMask
						fittersave['chlormask'] = chlormask

						fittersave['LandSeaMaskfilter'] = LandSeaMaskFilter
						fittersave['Rtypical_LandSeaMask'] = Rltypical*LandSeaMaskFilter
						fittersave['Rtypical_LandSeaMask_LonLat'] = Rltypical*LandSeaMaskFilter*LonLatMask
						fittersave['Rtypical_LandSeaMask_LonLat_Sol'] = Rltypical*LandSeaMaskFilter*LonLatMask*SolarZMask
						fittersave['Rtypical_LandSeaMask_LonLat_Sol_chlor'] = Rltypical*LandSeaMaskFilter*LonLatMask*SolarZMask*chlormask
						fittersave['Rtypical'] = Rltypical
						fittersave['SolarZMask'] = SolarZMask


						print 'Lon Lat fitter result:', LonLatMask
						fittersave.close()
			else:
				pass

			exit(0)

