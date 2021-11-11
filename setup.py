from setuptools import setup


setup(
    name='shlax',
    versioning='dev',
    setup_requires='setupmeta',
    extras_require=dict(
        test=[
            'pytest',
            'pytest-cov',
            'pytest-asyncio',
        ],
    ),
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/shlax',
    include_package_data=True,
    license='MIT',
    keywords='async subprocess',
    python_requires='>=3',
)
