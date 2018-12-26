"""setup.py for asn4sql"""

from setuptools import setup

install_requires = [
    'absl-py>=0.6.1',
'astroid>=2.1.0',
'cachetools>=3.0.0',
'certifi>=2018.11.29',
'google-api-python-client>=1.7.7',
'google-auth>=1.6.2',
'google-auth-httplib2>=0.0.3',
'httplib2>=0.12.0',
'isort>=4.3.4',
'lazy-object-proxy>=1.3.1',
'mccabe>=0.6.1',
'numpy>=1.15.4',
'oauth2client>=4.1.3',
'pandas>=0.23.4',
'pyasn1>=0.4.4',
'pyasn1-modules>=0.2.2',
'pylint>=2.2.2',
'python-dateutil>=2.7.5',
'pytz>=2018.7',
'rsa>=4.0',
'six>=1.12.0',
'typed-ast>=1.1.1',
'uritemplate>=3.0.0',
'wrapt>=1.10.11',
]
setup(name="timedime", author="Vladimir Feinberg",
      install_requires=install_requires)
