from setuptools import setup, find_packages

setup(
    name="katakate",
    version="0.0.4-dev",
    description="Katakate Sandbox Management Python SDK",
    packages=find_packages(where="src", include=["katakate", "katakate.*"]),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "sdk-async": ["httpx>=0.27.0"],
    },
    python_requires=">=3.8",
)
