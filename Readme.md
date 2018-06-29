[![Build Status](https://travis-ci.org/tkerdonc/vastplace.svg?branch=master)](https://travis-ci.org/tkerdonc/vastplace)[![Coverage Status](https://coveralls.io/repos/github/tkerdonc/vastplace/badge.svg?branch=master)](https://coveralls.io/github/tkerdonc/vastplace?branch=master)

# vastplace

vastplace stands for Visualizer Analyzer and STorage PLatform for Campaigns and Experiments. Its purpose is to help the handling of experiment files when running a warwalking measurement campaign. It provide tools to analyse a list of geolocalized sensor values from one or more experiments, using geographic features to correct imperfect device localization. It is based on the django framework in order to provide web access to its tools. It also interfaces with Spark in order to provide clustered computation.

## Getting Started

### Installing

This platform relies on a few python dependencies described in a requirements.txt file. We recommend using virtualenv in order to install this software.

```
virtualenv vastenv
cd vastenv
source bin/activate
git clone https://github.com/tkerdonc/vastplace.git
cd vastplace
pip install -r requirements.txt
```

### Running the tests

After install, tests can be ran as in any django project :
```
python manage.py test
```

### Running the platform

The platform is ran as any django project
```
python manage.py runserver
```

### Adding modules

This platform needs experiment specific modules in order to be of any use. Such modules specify the data format and what treatment they want to apply. Have a look at the [vastplace_example_module](https://github.com/tkerdonc/vastplace_example_module) for installation instruction, and details on implementing your own module.

## License

This project is licensed under the BSD 3 License - see the [LICENSE.md](LICENSE.md) file for details

