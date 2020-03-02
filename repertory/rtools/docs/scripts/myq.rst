myq
===

Check the local queue on arthur for your jobs. The script will save a list with the jobs at the time you use it to */data/username/.pbs_jobs* and show you which jobs completed since you last looked.

Usage:
""""""

Option 1:
^^^^^^^^^
Just show your jobs::

    >> myq
    
    #  Job_ID    S     Job_Name                              Tick
    ----------------------------------------------------------------------------------------
    1  500300     R     a_test_job                            tick42

    No finished jobs since last qstat, be patient! 


Option 2:
^^^^^^^^^
Get the folder on the tick (via */net/tick/scratch*) to directly look at the calculation::
 
    >> myq 1

    cd /net/tick42/scratch/user/500300.arthur.theo.chemie.tu-muenchen.de


