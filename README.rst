Shlax: Beautiful Async Subprocess executor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Why?
====

In Python we now have async subprocesses which allows to execute several
subprocesses at the same time. The purpose of this library is to:

- provide an acceptable asyncio subprocess wrapper for my syntaxic taste,
- can stream stderr and stdout in real time while capturing it,
- real time output must be prefixed for when you execute several commands at
  the time so that you know which line is for which process, like with
  docker-compose logs,
- output coloration in real time with regexps to make even more readable.

This code was copy/pasted between projects and finally extracted on its own.

Demo
====

.. image:: https://yourlabs.io/oss/shlax/-/raw/master/demo.png

You will find the demo script in demo.py in this repository.

Usage
=====

Basics
------

Basic example, this will both stream output and capture it:

.. code-block:: python

    from shlax import Subprocess
    proc = await Subprocess('echo hi').wait()
    print(proc.rc, proc.out, proc.err, proc.out_raw, proc.err_raw)

Longer
------

If you want to start the command and wait for completion elsewhere then call
any of ``start()`` and ``wait()``, or both, explicitely:

.. code-block:: python

    proc = Subprocess('echo hi')
    await proc.start()  # start the process
    await proc.wait()   # wait for completion

Proc alias
----------

Note that shlax defines an alias ``Proc`` to ``Subprocess`` so this also works:

.. code-block:: python

    from shlax import Proc
    proc = await Proc('echo hi').wait()

Quiet
-----

To disable real time output streaming use the ``quiet`` argument:

.. code-block:: python

    proc = await Subprocess('echo hi', quiet=True).wait()

Prefix
------

Using prefixes, you can have real time outputs of parallel commands and at the
same time know which output belongs to which process:

.. code-block:: python

    proc0 = Subprocess('find /', prefix='first')
    proc1 = Subprocess('find /', prefix='second')
    await asyncio.gather(proc0.wait(), proc1.wait())

Coloration and output patching
------------------------------

You can add coloration or patch real time output with regexps, note that it
will be applied line by line:

.. code-block:: python

    import sys
    regexps = {
        '^(.*).py$': '{cyan}\\1',
    }
    await asyncio.gather(*[
        Subprocess(
            f'find {path}',
            regexps=regexps,
        ).wait()
        for path in sys.path
    ])

Where is the rest?
==================

Shlax used to be the name of a much more ambitious poc-project, that you can
still find in the ``OLD`` branch of this repository. It has been extracted in
two projects with clear boundaries, namely `sysplan
<https://yourlabs.io/oss/sysplan>`_ and `podplan
<https://yourlabs.io/oss/podplan>`_ which are still in alpha state, although
Shlax as it is feature complete and stable.
