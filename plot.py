#! /usr/bin/python3

import sys
from sys import argv,exit
from datetime import datetime,timedelta


# 引数の受け取り
# 実行フォーマットは
#
# ./plot 'start_datetime' 'stop_datetime'
#
# start_datetime : 表示開始日時
# stop_datetime : 表示終了日時
#
# 日時指定のフォーマットは
#
#  |-----------------年
#  |  |--------------月
#  |  |  |-----------日
#  |  |  |  |--------時
#  |  |  |  |  |-----分
#  |  |  |  |  |  |--秒
# '%Y/%m/%d %H:%M:%S'

try: # 引数のフォーマットが正しいか確認
	start_datetime = datetime.strptime(argv[1],'%Y/%m/%d %H:%M:%S')
	stop_datetime = datetime.strptime(argv[2],'%Y/%m/%d %H:%M:%S')
except (IndexError,ValueError) as err: # 入力がない、またはフォーマットが正しくないときエラーメッセージ
	print('\r\nError message : ' , err)
	print('\r\nex:\r\n>>> ./plot.py "2023/1/9 13:6:43" "2023/1/9 15:00:00"\r\n')
	exit(127)

from numpy import concatenate,nan,empty
from scipy.stats import trim_mean
from pandas import DataFrame,read_csv
from multiprocessing import Pool
from matplotlib.pyplot import subplots,show,legend

delta_datetime = stop_datetime - start_datetime
cnt_files = int(delta_datetime.total_seconds() / 60)

log_file_fmt = './DATA/%Y/%m-%d/%m-%d_%H-%M.log'
log_file_list = [(start_datetime + timedelta(minutes=i)).strftime(log_file_fmt) for i in range(cnt_files)]

data_names = ['datetime','CV0','CV1','CV2','MC']
data_raw_dtypes = {'datetime' : 'object' , 'CV0' : 'uint16' , 'CV1':'uint16' , 'CV2':'uint16' , 'MC':'uint16'}
data_dtypes = {'datetime' : 'datetime64','CV0' : 'float16' , 'CV1' : 'float16', 'CV2' : 'float16' , 'MC' : 'float16'}
data_raw_datetime_fmt = '%Y-%m-%d_%H:%M:%S.%f'

data = DataFrame(index=[],columns=data_names).astype(data_dtypes)

vpb = 3.3 / (2 ** 12)
bias = 3.3 / 2

def data_input(log_file_name):
	# 生データの読み込み
	try:
		data_raw = read_csv(log_file_name,sep=' ',names=data_names,parse_dates=True).astype(data_raw_dtypes)
	except FileNotFoundError:
		return DataFrame(index=[nan],columns=data_names)
	return data_raw

def gen_datetime(data_raw):
	if data_raw.index.isnull()[0]:
		data = empty(1)
		data[0] = nan
		return data
	return [(datetime.strptime(data_raw['datetime'][0],data_raw_datetime_fmt) + timedelta(seconds=i)).replace(microsecond=0) for i in range(60)]

def gen_data(data_raw):
	if data_raw.index.isnull()[0]:
		data = empty((1,4))
		data[:] = nan
		return data
	data = empty((60,4),dtype=float)
	cnt = 0
	for i in range(60):
		start_cnt = 0
		while datetime.strptime(data_raw['datetime'][cnt],data_raw_datetime_fmt) < datetime.strptime(data_raw['datetime'][i],data_raw_datetime_fmt) + timedelta(seconds=1):
			try:
				data_raw.datetime[cnt + 1]
			except (ValueError,KeyError):
				break
			cnt = cnt + 1
		data[i][0] = int(trim_mean(data_raw['CV0'][start_cnt:cnt],0.01)) * vpb - bias
		data[i][1] = int(trim_mean(data_raw['CV1'][start_cnt:cnt],0.01)) * vpb - bias
		data[i][2] = int(trim_mean(data_raw['CV2'][start_cnt:cnt],0.01)) * vpb - bias
		data[i][3] = (int(trim_mean(data_raw['MC'][start_cnt:cnt],0.01)) * vpb - bias) * 10
	return data

with Pool() as p:
	data_raw = p.map(data_input,log_file_list)
# print(data_raw[-1]) # デバッグ用表示

with Pool() as p:
	data['datetime'] = concatenate(p.map(gen_datetime,data_raw))
# print(data) # デバッグ用表示

with Pool() as p:
	data['CV0'],data['CV1'],data['CV2'],data['MC'] = concatenate(p.map(gen_data,data_raw)).T
# print(data) # デバッグ用表示

fig, pl_xV = subplots()
pl_xC = pl_xV.twinx()

pl_xV.set_ylim(-bias,bias)
pl_xC.set_ylim(-10,10)
pl_xV.set_ylabel('V')
pl_xC.set_ylabel('A')

pl_xV.plot(data['datetime'],data['CV0'],'b',label='Cell0 Vol')
pl_xV.plot(data['datetime'],data['CV1'],'g',label='Cell1 Vol')
pl_xV.plot(data['datetime'],data['CV2'],'c',label='Cell2 Vol')
pl_xV.plot(data['datetime'],data['CV0'] + data['CV1'] + data['CV2'],'m',label='All Cells Vol')

pl_xC.plot(data['datetime'],data['MC'],'r',label='Module Cur')


legend(pl_xV.get_legend_handles_labels()[0] + pl_xC.get_legend_handles_labels()[0] , pl_xV.get_legend_handles_labels()[1] + pl_xC.get_legend_handles_labels()[1])


show()