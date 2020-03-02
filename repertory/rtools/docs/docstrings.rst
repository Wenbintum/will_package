Docstrings template
===================

We encourage all people to use the following template when writing docstrings. When used together with Sphinx and the numpydoc addon, this allows the creation of nice web and pdf documentation. The docstring itself is still easy to read when used for example directly in ``ipython``

See https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt for a very good explanation and many more possible formatting options.

Minimal example
---------------

.. code-block:: python

    def exp_x(b, n)
        """   
        What does this function do? Example: 
        n'th exponentiation of input b.

        Parameters
        ----------
        b : float
            Base value for the exponentiation
        n : int
            Exponent to calculate.
     
        Returns
        -------
        nb : float
            The exponentiated value.
        """

        nb = b**n
        return nb

..with Exception and Example
----------------------------
.. code-block:: python

    def exp_x(b, n)
        """   
        What does this function do? Example: 
        n'th exponentiation of input b.

        Parameters
        ----------
        b : float
            Base value for the exponentiation
        n : int
            Exponent to calculate.
     
        Returns
        -------
        nb : float
            The exponentiated value.

        Raises
        ------
        NoDevilException
            When the base number is 666.

        See Also
        --------
        numpy.power

        Examples
        --------
        >>> exp_x(3, 3)
        ... 27
        """
        if b == 666:
            raise NoDevilException

        nb = b**n
        return nb
