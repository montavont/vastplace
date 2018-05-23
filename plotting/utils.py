
# -*- coding: utf-8 -*-
"""
BSD 3-Clause License

Copyright (c) 2018, IMT Atlantique
All rights reserved.

This file is part of vastplace

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

@author Tanguy Kerdoncuff
"""
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
