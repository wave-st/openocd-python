import setuptools


if (__name__ == "__main__"):
    setuptools.setup(
        name="openocd-python",
        description="openOCD RPC Wrapper",
        author="",
        author_email="",
        url="",
        packages=setuptools.find_packages(where="src"),
        package_dir={"": "src"}
    )

