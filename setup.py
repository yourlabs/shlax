from setuptools import setup


setup(
    name='shlax',
    versioning='dev',
    setup_requires='setupmeta',
    extras_require=dict(
        cli=[
            'cli2>=2.2.2',
        ],
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
    keywords='cli automation ansible',
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'shlax = shlax.cli:cli.entry_point',
        ],
    },
)
