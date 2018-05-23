
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
from django.test import TestCase

class cell_utils_tests(TestCase):
    def test_pointsToSegList(self):
        """
        Tests that a list of points is converted to a list of segments
        """
    def test_generateCells(self):
        """
        Tests that cells are generated between two points
        """
    def test_sensorValueToTile(self):
        """
        Tests that a sensor value is associated to a tile based on its gps data
        """
    def test_shareCellWithNeighbours(self):
        """
        Tests that a sensor value associated to a tile is reformated to be associated to all neighbouring tiles
        """
    def test_place_datapoint_on_cell(self):
        """
        Tests that a datapoint is associated to the closest cell of a list
        """
    def test_segment_equality(self):
        """
        Tests that segment equality is able to compare two segments
        """
    def test_averageCell(self):
        """
        Tests that average_cell average the sensor values in a cell and returns the value
        """
    def test_generateInterpolatedCells(self):
        """
        Tests that generate_interpolated_cells generates interpolated sensor data between two points of the same segment
        Tests that generate_interpolated_cells generates interpolated sensor data between two points of neighbouring segments
        """
    def test_get_cells_for_source(self):
        """
        Tests that this extractes cells for a target source
        """
    def test_getMergedCells(self):
        """
        Tests that this generates merged cells for all sources of a type
        """
