from setuptools import find_packages, setup

setup(
    name="kenya_erp",
    version="0.1.0",
    description="Kenyan public-sector ERP extension for ERPNext",
    long_description=(
        "Consolidates the former Kenya HR (statutory leave, national identity "
        "fields, promotions), Kenya Procurement (E-GP supplier onboarding, "
        "tenders, bids) and Kenya Fleet (vehicles, drivers, fuel, maintenance, "
        "insurance, disposal) apps into one installable Frappe app with opt-in "
        "HRIS-K, E-GP and GVMS connectors."
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
        "requests",
    ],
)
