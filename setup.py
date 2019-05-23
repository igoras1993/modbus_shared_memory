import setuptools

with open("README.md", "r") as f:
    l_descr = f.read()

# usage:>python setup.py sdist bdist_wheel

setuptools.setup(
    name="ModbusSharedMemory",
    version="0.1.1",
    author="Igor Kantorski",
    author_email="igor.kantorski@gmail.com",
    description="Shared memory concept known from PLC manner implemented over uModbus framework.",
    long_description=l_descr,
    long_description_content_type="text/markdown",
    url="https://github.com/igoras1993/modbus_shared_memory",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Home Automation",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
