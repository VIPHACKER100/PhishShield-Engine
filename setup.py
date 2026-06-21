import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="phishshield-engine",
    version="3.1.0",
    author="VIPHACKER100 (Aryan Ahirwar)",
    author_email="[EMAIL_ADDRESS]",
    description="AI-powered email security platform for detecting spam, phishing, and identity spoofing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/viphacker100/PhishShield-Engine",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    install_requires=[
        "pandas>=2.1",
        "numpy==1.26.4",
        "scikit-learn>=1.4",
        "nltk>=3.8",
        "joblib>=1.3",
        "fastapi>=0.110",
        "uvicorn>=0.27",
        "python-multipart>=0.0.9",
        "jinja2>=3.1",
        "PyJWT>=2.8",
        "bcrypt>=4.1",
        "pytest>=8.0",
        "httpx>=0.27",
        "python-json-logger>=2.0",
        "PyYAML>=6.0",
        "google-api-python-client>=2.120",
        "google-auth-oauthlib>=1.2",
        "google-auth-httplib2>=0.2"
    ],
    entry_points={
        "console_scripts": [
            "phishshield=cli.manage:main",
        ],
    },
)
