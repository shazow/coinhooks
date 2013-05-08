import os

from setuptools import setup, find_packages

def path_to(p):
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, p)

README = open(path_to('README.md')).read()
REQUIREMENTS = open(path_to('requirements.txt'))

setup(name='coinhooks',
      version='0.0',
      description='coinhooks',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='coinhooks',
      install_requires = REQUIREMENTS,
      entry_points = """\
      [paste.app_factory]
      main = coinhooks.web.environment:setup
      """,
      paster_plugins=['pyramid'],
      )
