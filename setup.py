from setuptools import setup

setup(
    name="geetest_solver",
    version="1.0.9",
    author="kv",
    description="GeeTest v4 ICON CAPTCHA solver using YOLO + template matching",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/syncrain/geetest-solver",
    packages=["geetest_solver"],
    install_requires=[
        "requests>=2.31.0",
        "ultralytics>=8.0.0",
        "opencv-python>=4.8.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0",
        "pycryptodome>=3.19.0",
        "scipy>=1.11.0",
        "scikit-image>=0.21.0"
    ],
    extras_require={
        "interactive": ["matplotlib>=3.7.0"]
    },
    python_requires=">=3.8",
    package_data={"geetest_solver": ["best.pt"]},
    include_package_data=True,
)
