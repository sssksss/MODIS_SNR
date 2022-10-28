# -*-coding=utf-8-*-

from pathlib import Path
from datetime import datetime
import os,glob

from pyhdf.SD import SD, SDC
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import h5py


def readmsk():
    filea = h5py.File(r'D:\Work\SNR\file\American_West\MODIS\2019_121_2145_fitter.hdf','r')
    landseamask = filea['LandSeaMaskfilter'][()]
    lonlatmask = filea['LonLatMask'][()]
    solzmask = filea['SolarZMask'][()]
    chlormask = file021km['chlormask'][()]

    return [landseamask,lonlatmask,solzmask,chlormask]


def to_reflectance(sds):
    '''将反射率的SDS变为浮点型数组.'''
    ref = sds[:]
    attrs = sds.attributes()
    scales = np.array(attrs['reflectance_scales'])
    offsets = np.array(attrs['reflectance_offsets'])
    index = np.s_[:, np.newaxis, np.newaxis]
    ref = np.where(
        ref > 32767, np.nan,
        (ref - offsets[index]) * scales[index]
    )

    return ref

def scale_modis(rgb):
    '''增亮MODIS的彩色图.'''
    x = np.array([0, 30, 60, 120, 190, 255]) / 255
    y = np.array([0, 110, 160, 210, 240, 255]) / 255
    f = interp1d(x, y, bounds_error=False, fill_value=1)

    return f(rgb)


def draw_main(dirpath_pics,filepath_MYD02,filepath_MYD03):
    # filepath_MYD02 = filepath_MYD02
    # filepath_MYD03 = filepath_MYD03
    filepath_MYD02 = r'D:\Work\SNR\file\American_West\MODIS\MYD021KM\2019\121\MYD021KM.A2019121.2145.061.2019122151635.hdf'
    filepath_MYD03 = r"D:\Work\SNR\file\American_West\MODIS\MYD03\2019\121\MYD03.A2019121.2145.061.2019122150853.hdf"
    # 提取文件名中的时间.
    parts = filepath_MYD02.split('.')
    print parts
    date = datetime.strptime(parts[1] + parts[2], 'A%Y%j%H%M')

    # 读取1km经纬度.
    sd = SD(str(filepath_MYD03), SDC.READ)
    lon = sd.select('Longitude')[:]
    lat = sd.select('Latitude')[:]
    sd.end()
    # 地图范围由granule的范围决定.
    extents = [lon.min(), lon.max(), lat.min(), lat.max()]
    print extents

    # 读取反射率.
    sd = SD(str(filepath_MYD02), SDC.READ)
    ref250 = to_reflectance(sd.select('EV_250_Aggr1km_RefSB'))
    ref500 = to_reflectance(sd.select('EV_500_Aggr1km_RefSB'))
    sd.end()
    ref1 = ref250[0, :, :]
    ref3 = ref500[0, :, :]
    ref4 = ref500[1, :, :]

    # 合并RGB数组, 处理缺测部分.
    rgb = np.dstack((ref1, ref4, ref3))
    rgb[np.any(np.isnan(rgb), axis=-1)] = 1
    rgb = np.clip(rgb, 0, 1)
    # -------------------
    [landseamask, lonlatmask, solzmask,chlormask] = readmsk()
    rgb[(landseamask*lonlatmask*solzmask)==0]=1
    # -------------------

    # 三种处理的图像.
    rgb1 = rgb
    rgb2 = np.power(rgb, 1 / 2.2)
    rgb3 = scale_modis(rgb)

    # 组图形状为(1, 3).
    proj = ccrs.PlateCarree()
    subplot_kw = {'projection': proj}
    fig, axes = plt.subplots(1, 3, figsize=(16, 9), subplot_kw=subplot_kw)
    fig.subplots_adjust(wspace=0.2)
    # 画出地图.
    for ax in axes:
        ax.coastlines(resolution='50m', lw=0.5)
        ax.add_feature(cfeature.BORDERS, lw=0.5)
        ax.set_xticks(np.arange(-180, 181, 10), crs=proj)
        ax.set_yticks(np.arange(-90, 91, 10), crs=proj)
        ax.xaxis.set_minor_locator(mticker.AutoMinorLocator(2))
        ax.yaxis.set_minor_locator(mticker.AutoMinorLocator(2))
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.set_extent(extents, crs=proj)
        ax.tick_params(labelsize='small')

    # 画出三种图像.
    rgbs = [rgb1, rgb2, rgb3]
    titles = ['Original', 'Gamma Correction', 'Enhancement']
    for i, ax in enumerate(axes):
        colors = rgbs[i][:-1, :-1].reshape(-1, 3)
        ax.pcolormesh(
            lon, lat, lon[:-1, :-1], color=colors,
            shading='flat', transform=proj
        )
        ax.set_title(titles[i], fontsize='medium')

    # 设置图片标题.
    t = date.strftime('%Y-%m-%d %H:%M')
    # fig.suptitle(t, fontsize='large')

    # 保存图片.
    filepath_output = r'D:\Work\SNR\code\calABCD\MODIS\MODIS_SNR\recurrent\pics\{}_true_color.png'.format(date.strftime('%Y%m%d_%H%M'))
    print filepath_output
    fig.savefig((filepath_output), dpi=500, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    # 输入和输出目录.
    dirpath_data = Path('./data')
    dirpath_pics = Path('./pics')
    if not dirpath_pics.exists():
        dirpath_pics.mkdir()

    # 输入文件.
    file021km = os.listdir(r"D:\Work\SNR\file\American_West\MODIS\MYD021KM\2019\121")

    for name in file021km:
        abs_file_path = os.path.join(r"D:\Work\SNR\file\American_West\MODIS\MYD021KM\2019\121",name)
        print abs_file_path

        geofilepath = glob.glob(abs_file_path.replace('MYD021KM','MYD03')[:-18]+'*')[0]
        print geofilepath

        draw_main(dirpath_pics,abs_file_path,geofilepath)

        exit(0)


