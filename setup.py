from distutils.core import setup

setup(
    name='charitycheck',
    version='1.0',
    author='Nicholas A. Lourie',
    author_email='developer.nick@kozbox.com',
    packages=['charitycheck',],
    license='MIT License',
    description=('a small module to verify information'
                 'about nonprofits using their EINs'),
    long_description=open('README.md').read(),
    include_package_data=True,
    keywords="nonprofit nonprofits EIN IRS verify",
    url="https://github.com/nalourie/charitycheck",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)
    
