#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango, Brad McDonald, Mejbah ul Alam, Justin Gottschlich, Abdullah Muzahid
# *****************************************************************************/
import subprocess

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


class CustomInstall(install):
    """Custom handler for the 'install' command."""

    def run(self):
        print('[DEBUG] making perfpoint.so')
        subprocess.check_call('make', cwd='./autoperf/profiler/')
        super().run()


class CustomDevelop(develop):
    """Custom handler for the 'develop' command."""

    def run(self):
        print('[DEBUG] making perfpoint.so')
        subprocess.check_call('make', cwd='./autoperf/profiler/')
        super().run()


setup(name='autoperf',
      version='1.0',
      description='AutoPerf helps identify performance regressions in large codebases',
      long_description='AutoPerf is a tool for low-overhead, automated diagnosis \
                        of performance anomalies in multithreaded programs via \
                        hardware performance counters (HWPCs) in Intel CPUs',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: APL 2.0 License',
          'Programming Language :: Python :: 3.8',
          'Operating System :: POSIX :: Linux',
          'Topic :: Software Development :: Quality Assurance',
      ],
      keywords='autoperf performance regression monitoring',
      author='Intel Corporation',
      license='APL',
      packages=['autoperf'],
      zip_safe=False,
      entry_points={'console_scripts': ['autoperf=autoperf.__main__:main']},
      cmdclass={'install': CustomInstall, 'develop': CustomDevelop},
      package_dir={'autoperf': 'autoperf'},
      package_data={'autoperf': ['profiler/perfpoint.so']},
      include_package_data=True,
      platforms=['linux'],
      install_requires=['rich>=10.1.0',
                        'clang>=11.0',
                        'libclang>=11.1.0',
                        'numpy>=1.19.2',
                        'tensorflow>=2.4.0',
                        'pydot>=1.4.1',
                        'pandas>=1.2.4',
                        'matplotlib>=3.3.4',
                        'seaborn>=0.11.1',
                        'gitpython>=3.1.14',
                        'scikit-learn>=0.24.1',
                        'psutil>=5.8.0',
                        'transitions>=0.8.8',
                        'graphviz>=0.16',
                        'dill>=0.3.3',
                        'tqdm>=4.59.0'],  # external packages as dependencies
      # test_suite='autoperf.tests.get_suite'
      )
