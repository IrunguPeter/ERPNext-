from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="kenya_procurement",
    version="0.1.0",
    description="Kenya public-procurement extension for ERPNext integrated with the E-GP (Electronic Government Procurement) system.",
    author="IrunguPeter",
    author_email="irungupeter204@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)