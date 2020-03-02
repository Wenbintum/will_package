get_compute_nodes.py
====================

This script can be used to generate a list of compute nodes on Arthur in the TWiki format (`http://fs/twiki4/bin/view/Theochem/ArthurCluster`). 

Usage:
""""""

.. code-block:: bash

   >> python get_compute_nodes.py

And the result:: 

    | *Node Name* | *cores* | *CPU* | *os_version* | *RAM* | *state* |
    | tick1 | 8 | !XeonX5482 | lenny | ??? | down,offline |
    | tick2 | 8 | !XeonX5482 | lenny | ??? | down,offline |
    | tick3 | 8 | !XeonX5482 | lenny | ??? | down,offline |
    | tick4 | 8 | !XeonE5640 | lenny | ??? | down,offline |
    | tick5 | 8 | !cc | no os_flag | ??? | down,offline |
    | tick6 | 2 | !MP1900 | no os_flag | ??? | down,offline |
    .....
    
    Currently online: 19 / 50 compute nodes.


