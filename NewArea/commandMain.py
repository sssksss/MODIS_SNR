#coding:utf-8
import os,datetime
import sys
import numpy as np
from multiprocessing import Pool

def mainProcess(day,band):
	CalCommand = "python main.py FY3B MERSI %s %s" % (day, band)
	os.system(CalCommand)

import traceback
def _mainProcess(args):
    try:
        mainProcess(*args)
        return args, 'success'
    except:
        traceback.print_exc()
        return args, 'fail'


if __name__ == "__main__":
	dayList = []
	begin = datetime.date(2015, 7, 29)
	end = datetime.date(2015, 7, 30)
	for i in range((end - begin).days + 1):
		day = begin + datetime.timedelta(days=i)
		day = str(day).split("-")
		day = "".join(day)
		dayList.append(day)
	BandList = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
	# BandList = [8, 9, 10]
	# BandList = [8]


	r = Pool(10)
	args = [(str(day),str(band)) for day in dayList for band in BandList]
	for i in r.imap_unordered(_mainProcess, args):
		print i


