import setuptools

from sqlitis.version import VERSION

long_description = open("README.md").read()

setup_params = dict(
    name="sqlitis",
    version=VERSION,
    license="MIT",
    author="Paul Glass",
    author_email="pnglass@gmail.com",
    url="https://github.com/pglass/sqlitis",
    keywords="sql sqlalchemy convert sqlitis",
    packages=["sqlitis"],
    package_data={"": ["LICENSE"]},
    package_dir={"sqlitis": "sqlitis"},
    include_package_data=True,
    description="convert sql to sqlalchemy expressions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["sqlparse==0.3.0"],
    entry_points={"console_scripts": ["sqlitis = sqlitis.cli:main"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)

if __name__ == "__main__":
    setuptools.setup(**setup_params)
