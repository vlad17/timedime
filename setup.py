"""setup.py for asn4sql"""

from setuptools import setup

install_requires = [
'absl-py>=0.6.1',
'cachetools>=3.0.0',
'certifi>=2018.11.29',
'google-api-python-client>=1.7.7',
'google-auth>=1.6.2',
'google-auth-httplib2>=0.0.3',
'httplib2>=0.12.0',
'isort>=4.3.4',
'numpy>=1.15.4',
'oauth2client>=4.1.3',
'pandas>=0.23.4',
'pyasn1>=0.4.4',
'pyasn1-modules>=0.2.2',
'python-dateutil>=2.7.5',
'pytz>=2018.7',
'rsa>=4.0',
'six>=1.12.0',
'uritemplate>=3.0.0',
]
setup(name="timedime", author="Vladimir Feinberg",
      install_requires=install_requires)
