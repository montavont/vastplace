
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

from .cell_utils import pointsToSegList, generateCells


class cell_utils_tests(TestCase):
    def test_pointsToSegList(self):
        """
        Tests that a list of points is converted to a list of segments
        """
        points = [(0, 0), (1, 1), (2, 1), (10, 2.5)]
        segments = pointsToSegList(points)

        assert(len(segments) == 3)
        assert(((0, 0), (1, 1)) in segments)
        assert(((1, 1), (2, 1)) in segments)
        assert(((2, 1), (10, 2.5)) in segments)

    def test_empty_pointsToSegList(self):
        """
        Tests that an empty list of points is converted to an empty list of segments
        """
        points = []
        segments = pointsToSegList(points)
        assert(len(segments) == 0)

    def test_generateCells(self):
        """
        Tests that cells are generated each meter between two points
        The following two test points are separated by ten meters.
            47.09749,-1.26681
            47.09748,-1.26666
        """

        start = (47.09749,-1.26681)
        stop = (47.09748,-1.26666)

        cells = generateCells((start, stop), 17)

        # Assert for one cell generated every meters (starting with meter 0)
        assert(len(cells)) == 11

        reverse_cells = generateCells((stop, start), 17)
        # Assert that point order does not impact the returned cells

        reverse_cells_gps = [u['gps'] for u in reverse_cells]
        cells_gps = [u['gps'] for u in cells]

        for cell in cells:
            assert cell['gps'] in reverse_cells_gps
        for cell in reverse_cells:
            assert cell['gps'] in cells_gps

    def test_empty_generateCells(self):
        null_cells = generateCells((), 17)
        assert(len(null_cells) == 0)


    def test_single_generateCells(self):
        start = (47.09749,-1.26681)
        single_cells = generateCells((start, start), 17)
        assert(len(single_cells) == 1)
        assert(single_cells[0]['gps'] == start)


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
