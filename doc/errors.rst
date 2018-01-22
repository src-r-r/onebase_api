==========
Exceptions
==========

Overview
========

1Base exceptions are managed by a key/message pair found in
``<data_dir>/assets/erros.csv``.

Brief Syntax
============

This is the syntax for each error pair in the CSV file::

  Error -> Key,Message
  Key -> Level "-" Code
  Level -> "E" | "W" | "F"

Detailed Syntax
===============

Error Key
---------

Each error key is specified by ``<Level>-<Code>`` where ``<Level>`` is one of:

.. table::

  =====   =======
  Level   Meaning
  =====   =======
  E       Error
  W       Warning
  F       Fatal
  =====   =======

And each ``<Level>`` can be any number. Each number is a 3-digit sequence,
where the frist digit specifies an error class.

.. table:: Error code Class

    ======      ======================================
    Class       Meaning
    ======      ======================================
    100         Document Field error (e.g. wrong type)
    200         Model error
    300         API-related error
    400         Other classes (unexpecteds)
    ======      ======================================
