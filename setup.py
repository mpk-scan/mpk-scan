from setuptools import setup, find_packages

setup(
    name="capstoneLLMthing",
    version="0.1.0",
    author="Jeremy Neale",
    description="Semgrep analysis for vulnerabilities",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/omarnweashe/Sp25Capstone",
    packages=find_packages(where="src"),  # Look for packages in the "src" directory
    package_dir={"": "src"},  # Specify "src" as the root directory for packages
    include_package_data=True,
    install_requires=[
        "boto3",
        "semgrep",
        "bs4",
        "requests",
        "jsbeautifier",
        "tldextract",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "capstone-crawler=crawler.crawler:main",  # CLI command for crawler
            "capstone-semgrep=semgrep.semgrep:main",  # CLI command for semgrep
        ],
    },
)