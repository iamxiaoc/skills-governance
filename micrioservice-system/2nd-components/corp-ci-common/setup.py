from setuptools import setup, find_packages

setup(
    name="corp-ci-common",
    version="1.3.0",
    description="CI公共组件（其他部门提供）",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.28.0",
    ],
)
