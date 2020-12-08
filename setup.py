import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xdtransform",
    version="0.0.1",
    author="Peter Peshev",
    author_email="peshev@gmail.com",
    description="Library implementing the Microsoft XML Document Transform (XDT) transformation process",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/peshev/python-xdtransform",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "lxml"
    ],
    scripts=[
        'scripts/xdtransform'
    ]
)
