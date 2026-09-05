from setuptools import find_packages, setup

setup(
    name="kenya_hr",
    version="0.1.0",
    description="Kenya-specific Human Resources extension for ERPNext",
    long_description=(
        "Adds statutory leave types, national identity fields, and a "
        "multi-stage Staff Promotion workflow to ERPNext's HR module."
    ),
    author="IrunguPeter",
    author_email="irungupeter204@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "frappe",
        "erpnext",
        "hrms",
    ],
)