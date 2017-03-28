import setuptools

setup_params = dict(
    name='sqlitis',
    version='0.0.1',
    license='MIT',
    author='Paul Glass',
    author_email='pnglass@gmail.com',
    url='https://github.com/pglass/sqlitis',
    keywords='sql sqlalchemy convert sqlitis',
    packages=['sqlitis'],
    package_data={'': ['LICENSE']},
    package_dir={'sqlitis': 'sqlitis'},
    include_package_data=True,
    description='convert sql to sqlalchemy expressions',
    install_requires=[
        'sqlparse==0.2.0',
    ],
    entry_points={
        'console_scripts': [
            'sqlitis = sqlitis.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
