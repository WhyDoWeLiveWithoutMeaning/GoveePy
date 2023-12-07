from setuptools import setup

setup(
  name='GoveePy',
  version='0.2',
  description='A Govee API Wrapper for Python',
  url='https://github.com/WhyDoWeLiveWithoutMeaning/GoveePy',
  author="Meaning",
  license="MIT",
  packages=['govee'],
  install_requires=[
    "requests>=2.31.0"
  ],
  classifiers=[
    'Development Status :: 1 - Planning',
    'Intended Audience :: WEBSITE USERS',
    'License :: OSI Approved :: MIT License',  
    'Operating System :: WINDOWS',
    'Programming Language :: Python :: 3.12',
    'Typing :: Typed'
  ]
)