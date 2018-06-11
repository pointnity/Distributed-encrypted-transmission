
#!/usr/bin/env python

from setuptools import setup, find_packages

# to set __version__
exec(open('blockstack_file/version.py').read())

setup(
    name='blockstack-file',
    version=__version__,
    url='https://github.com/blockstack/blockstack-file',
    license='GPLv3',
    author='Blockstack.org',
    author_email='support@blockstack.org',
    description='Blockstack encrypted file sharing',
    keywords='blockchain git crypography name key value store data',
    packages=find_packages(),
    download_url='https://github.com/blockstack/blockstack-file/archive/master.zip',
    zip_safe=False,
    include_package_data=True,
    scripts=['bin/blockstack-file'],
    install_requires=[
        'blockstack>=0.14.1',
        'blockstack-gpg>=0.14.1'
    ],
