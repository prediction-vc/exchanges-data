# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Exchanges',
    version='0.1.0',
    description='PredictionVC Exchanges Scraper',
    long_description=readme,
    author='Igor Zdrnja',
    author_email='igor@prediction.vc',
    url='https://github.com/prediction-vc/exchanges',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

