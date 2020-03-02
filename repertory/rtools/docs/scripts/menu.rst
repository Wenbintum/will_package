menu
====

Python script to query the menu for today. Can be used for mensa and Max Planck mensa.

Usage:
""""""
Executing the script::

   >> ./menu
   
will show you the complete menu for today::

    Today they try to poison you with:
    ------------------------------------------------------------------------------
    Tagesgericht 1            | Feuriger Eintopf von weißen Bohnen mit Gemüse (v)
    Tagesgericht 3            | Spaghetti in Sauce Bolognese (R)
    ------------------------------------------------------------------------------
    Good luck!

    Less poisonous but more expensive is Max Planck with..
    ------------------------------------------------------------------------------
    1.V Gebratene Mohnschupfnudeln mit Apfelmus*
    2.“Asiafish“ mit Curry und Gemüse oder Seelachs gebacken mit Sauerrahm-Kräuter-Dip,
    dazu Reis oder B.n.W.
    3.Pastastation: V „Pasta con funghi e fagioli“, Orecchiette mit Champignons, weißen Bohnen und Tomaten,
    dazu frisch geriebener Grana 1,5
    4.Grillstation: S „Virginiasteak“, Halsgratsteak vom Grill, mit Virginia-Pfeffer gewürzt,
    dazu Kräuterbutter, Buttermais und Pommes frites oder B.n.W.
    ------------------------------------------------------------------------------

You can also choose to view only the menu for the mensa or the Max Planck mensa::

   >> ./menu --mensa
   >> ./menu --mpi
   
or shorter::

   >> ./menu -m
   >> ./menu -p
