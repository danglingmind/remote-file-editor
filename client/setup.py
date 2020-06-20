import setuptools

setuptools.setup(
    name='editor-client',
    version='1.0.0.0',
    packages=setuptools.find_packages(),
    url='',
    license='',
    author='Prateek Reddy',
    author_email='',
    description='Remote client to edit files',
    python_requires='>=3.6',
    install_requires=['PyInstaller'],
    entry_points={"console_scripts":["realpython=clinet.client:main"]}
)
