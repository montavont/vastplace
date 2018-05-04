import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import multiprocessing

from statsmodels.distributions.empirical_distribution import ECDF



#This is mainly a wrapper around matplotlib functions, in order to spawn them into processes and avoid multithreading conflicts when plotting on the fly

def plotBarGraph_impl(return_dict, bars, xlabel, ylabel, x_ticks, y_ticks, x_tick_labels, y_tick_labels, legend):
	#plot the image and send it in the response
	plt.figure()
	for bar in bars:
		plt.bar(bar['X'], bar['Y'], label = bar['label'], width = bar['width'], color = bar['color'])
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)

        if x_ticks is not None and x_tick_labels is not None:
            plt.xticks(x_ticks, x_tick_labels, rotation = 45)

	if legend:
		plt.legend()

	buf = io.BytesIO()
	plt.savefig(buf, format='svg')

	plt.close()
	buf.seek(0)

	return_dict['graph'] = buf

def plotBarGraph(bars, xlabel = "", ylabel = '', x_ticks = None, y_ticks = None, x_tick_labels=None, y_tick_labels=None, legend = False):
	manager = multiprocessing.Manager()
	return_dict = manager.dict()
	jobs = []
        p = multiprocessing.Process(target=plotBarGraph_impl, args=(return_dict, bars, xlabel, ylabel, x_ticks, y_ticks, x_tick_labels, y_tick_labels, legend))
        p.start()
       	p.join()

	return return_dict['graph']



def plotCDF_impl(return_dict, data, xlabel, ylabel, legend, log_x):
	#plot the image and send it in the response
	plt.figure()

	for d in data:
  		cdf = ECDF(d['data'])
                plt.step(cdf.x, cdf.y, color=d['color'], label = d['label'])


        if log_x:
            plt.xscale("log", nonposx='clip')
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	if legend:
		plt.legend()

	buf = io.BytesIO()
	plt.savefig(buf, format='svg')

	plt.close()
	buf.seek(0)

	return_dict['graph'] = buf


def plotCDF(data, xlabel = "", ylabel = '', legend = False, log_x = False):
	manager = multiprocessing.Manager()
	return_dict = manager.dict()
	jobs = []
        p = multiprocessing.Process(target=plotCDF_impl, args=(return_dict, data, xlabel, ylabel, legend, log_x))
        p.start()
       	p.join()

	return return_dict['graph']

def plotStep_impl(return_dict, data, xlabel, ylabel, legend):
	#plot the image and send it in the response
	plt.figure()

	for d in data:
                plt.step(d['x'], d['y'], color=d['color'], label = d['label'])
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	if legend:
		plt.legend()

	buf = io.BytesIO()
	plt.savefig(buf, format='svg')

	plt.close()
	buf.seek(0)

	return_dict['graph'] = buf


def plotStep(data, xlabel = "", ylabel = '', legend = False):
	manager = multiprocessing.Manager()
	return_dict = manager.dict()
	jobs = []
        p = multiprocessing.Process(target=plotStep_impl, args=(return_dict, data, xlabel, ylabel, legend))
        p.start()
       	p.join()

	return return_dict['graph']
