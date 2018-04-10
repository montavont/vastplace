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
