Installation
============

Here's how you can get started using AutoPerf on your software repository!

.. tip::
    For AutoPerf works seamlessly with Linux Ubuntu 20.04 x86_64 LTS). Users are required to have the ability to `sudo` with a non-virtualized Intel CPU (though you can use :ref:`Docker<🐳 Use Docker (Optional)>`!)
.. tip::
    Behavior for x86_64 AMD processors is unknown please visit http://developer.amd.com/amd-uprof/
.. tip::
    For x86_64 Windows, a developer will need to modify the library
    https://docs.microsoft.com/en-us/previous-versions/windows/desktop/hcp/hardware-counter-profiling-portal
    https://docs.microsoft.com/en-us/windows/win32/perfctrs/providing-counter-data-using-version-2-0
    .. code-block:: console
        // https://docs.microsoft.com/en-us/cpp/intrinsics/readpmc
        #include <intrin.h>
        unsigned __int64 __readpmc(
           unsigned long counter
        );

👥 Clone Repository
*******************

Clone the `GitHub repository` to your local machine.

.. code-block:: console
    $ git clone git@github.com:intel/raad.git

⏱️ Install PAPI
***************

Use your preferred package manager to install the performance application programming interface (PAPI) libraries.
At a minimum, you need the base library (`libpapi`) and the development headers `libpapi-dev`. The preferred
version is 5.7.

Some repositories also include `papi-tools`, which exposes helpful utilities like `papi-avail`. This particular
executable lists all available performance counter events for your particular hardware.

All of this can be done via Aptitude:

.. code-block:: console
    $ sudo apt install build-essential apt-transport-https aptitude ca-certificates cscope valgrind gdb -y
    $ sudo apt install wget tar unzip p7zip-full p7zip-rar dtrx a2ps enscript python3 libncurses5-dev libipt-dev -y
    $ sudo apt install fakeroot msr-tools linux-tools linux-tools-common linux-tools-virtual -y
    $ sudo apt install libpapi-dev libpapi-dev papi-examples papi-tools libpthread-stubs0-dev -y
    $ sudo modprobe msr

🐍 Install Conda
****************

Install `Anaconda <https://docs.anaconda.com/anaconda/install/index.html>`_ or
`Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_.

Next, clone the AutoPerf Conda environment:

.. code-block:: console

    $ conda env create -f environment_ubuntu.yml

If you're not using Ubuntu, you can try using the base `environment.yml` file,
but it will take longer to solve the environment, sometimes up to 10 minutes.

Once the environment is created, activate it by typing:

.. code-block:: console

    $ conda activate ap

📦 Install AutoPerf
*******************

AutoPerf is not yet available on the Python Package Index, so it must be installed
manually at this time. You can do so by entering the base of the repository and typing:

.. code-block:: console

    $ python setup.py install

This will build the required C dynamic library and place AutoPerf in your `PYTHONPATH`.

Once installed, the AutoPerf CLI can be accessed by typing:

.. code-block:: console

    $ autoperf --help

⚙️ Configure System
*******************

Before AutoPerf can analyze your code, you need to allow unprivileged users access to performance counter events.
By default, the value is 2 which you cannot take any measurements.

The codes are:
* kernel.perf_event_paranoid = 2: Cannot take any measurements. The perf utility might still be useful to analyse existing records with perf ls, perf report, perf timechart or perf trace.
* kernel.perf_event_paranoid = 1: Can trace a command with perf stat or perf record, and get kernel profiling data.
* kernel.perf_event_paranoid = 0: Can trace a command with perf stat or perf record, and get CPU event data.
* kernel.perf_event_paranoid = -1: Get raw access to kernel trace points (specifically, you can mmap the file created by perf_event_open, I don't know what the implications are).

To check the status:
.. code-block:: console
    $ cat /proc/sys/kernel/perf_event_paranoid

To check performance monitor:
.. code-block:: console
    $ perf stat sleep 1

To enable for this boot cycle.
.. code-block:: console
    $ sudo sh -c 'echo  -1 >/proc/sys/kernel/perf_event_paranoid'

Persist across reboots.
.. code-block:: console
    $ sudo sh -c 'echo kernel.perf_event_paranoid=-1 >> /etc/sysctl.d/local.conf'
    $ grep kernel.perf_event_paranoid /etc/sysctl.d/local.conf
    $ sudo sh -c 'echo kernel.perf_event_paranoid=-1 >> /etc/sysctl.d/perf.conf'
    $ grep kernel.perf_event_paranoid /etc/sysctl.d/perf.conf

To check for perf_events module:
.. code-block:: console
    $ grep _PERF_ /boot/config-`uname -r`
    $ ls -l /lib/modules/`uname -r`/kernel/arch/x86/events/intel

For automatic instrumentation, you will need to have a makefile similar to the unit test repo using the Makefile rules.
https://www.gnu.org/software/make/manual/make.html#index-ARFLAGS

🐳 Use Docker (Optional)
************************
.. tip::
    Not recommended.

At the base level of the repository, type:

.. code-block:: console
    $ docker build

Interacting with the container itself is out of scope for this installation guide, but there
is one aspect that should be discussed here.

As mentioned previously, the kernel's `perf_event_paranoid` flag must be set to -1 for AutoPerf to
interact with the hardware performance counters. By default, Docker has disabled this behavior due
to a potential security risk (tracing/profiling syscalls can leak information about the host).

There are two options to get around this:
1. Follow the advice given `here <https://stackoverflow.com/a/44748260>`_ regarding a custom seccomp file that allows only the `perf_event_open` syscall.
2. Run the container with the `\-\-privileged` flag, which opens up further security vulnerabilities.
