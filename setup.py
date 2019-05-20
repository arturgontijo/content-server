from setuptools import setup, find_packages
import re


with open('content_server/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setup(
    name='content-server',
    version=version,
    packages=find_packages(),
    url='https://github.com/arturgontijo/content-server',
    license='MIT',
    author='SingularityNET Foundation',
    author_email='info@singularitynet.io',
    description='SingularityNET Content Server',
    python_requires='>=3.5',
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy'
    ],
    include_package_data=True
)
