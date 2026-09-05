from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="kenya_fleet",
    version="0.1.0",
    description="Government-aligned fleet management for ERPNext (vehicles, drivers, fuel, maintenance, insurance, disposal) with an opt-in GVMS connector.",
    author="IrunguPeter",
    author_email="irungupeter204@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)