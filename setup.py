from setuptools import setup, find_packages

setup(
    name="mpk-scan",
    version="1.0.0",
    author="Jeremy Neale, Claire Doody, Omar Nweashe, Aidan Cranfeld, Nabeel Merali",
    description="Web scraper and vulnerability scanner",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/omarnweashe/Sp25Capstone",
    packages=find_packages(where="src"),  
    package_dir={"": "src"},  
    include_package_data=True,
    install_requires=[
        "boto3==1.26.24",
        "semgrep==1.94.0",
        "bs4==0.0.2",
        "requests==2.32.0",
        "jsbeautifier==1.15.4",
        "tldextract==5.1.3",
    ]
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "mpk-scan=mpk_scan.mpk_scan:main",  
            "mpk-scan-crawler=crawler.crawler:main",  
        ],
    },
)