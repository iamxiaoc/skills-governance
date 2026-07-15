from setuptools import setup, find_packages

setup(
    name="corp-ci-registry",
    version="2.0.3",
    description="镜像仓库客户端（其他部门提供）",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
)
