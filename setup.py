try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Ncl',
    'author': 'uboscolo',
    'url': 'file://Applications/ncl',
    'download_url': 'file://Applications/ncl',
    'author_email': 'uboscolo@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['ncl'],
    'scripts': [],
    'name': 'ncl'
}

setup(**config)
