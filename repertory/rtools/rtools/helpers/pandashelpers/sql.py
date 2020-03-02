# This file is part of rtools.
#
#    rtools is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    rtools is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with rtools.  If not, see <http://www.gnu.org/licenses/>.
"""
Pandas helpers for SQL storage

Author: Christoph Schober, 2015

"""
import pandas as pd
from sqlalchemy import create_engine
from rtools.misc import get_close_matches


def _return_engine(sqlpath):
    """Test if sqlpath is direct path or path to file with database path and
    return engine."""
    if "sqlite:////" in sqlpath:
        engine = create_engine(sqlpath)
    else:
        with open(sqlpath) as f:
            engine = create_engine(f.readline().strip())
    return engine


def list_tables(sqlpath):
    """
    List all tables in SQLite database.

    Parameters
    ----------
    sqlpath : str
        SQLite path to the database file ('sqlite:///...') or path to a
        textfile with the SQLite path in the first line (this can be used to
        place the database path in the root folder of a project).

    Returns
    -------
    tables : list
        All table names found in the SQLite database.
    """
    engine = _return_engine(sqlpath)
    tables = engine.table_names()
    return tables


def load_table(sqlpath, table):
    """
    Load a table from a SQLite database file.

    Parameters
    ----------
    sqlpath : str
        SQLite path to the database file ('sqlite:///...') or path to a
        textfile with the SQLite path in the first line (this can be used to
        place the database path in the root folder of a project).
    table : str
        The name of the table to be loaded.

    Returns
    -------
    pdf : Pandas.DataFrame
        The Pandas DataFrame for 'table'.
    """
    engine = _return_engine(sqlpath)
    pdf = pd.read_sql_table(table, engine)
    return pdf


def save_table(pdf, table, sqlpath, drop=[], **kwargs):
    """
    Save a Pandas dataframe to a SQLite database file.

    Parameters
    ----------
    pdf : pd.DataFrame
        The pandas dataframe to be saved.
    table : str
        The table name for the DataFrame in the SQL database.
    sqlpath : str
        SQLite path to the database file ('sqlite:///...') or path to a
        textfile with the SQLite path in the first line (this can be used to
        place the database path in the root folder of a project).
    drop : list of str
        A list of column name to be dropped before saving the DataFrame to the
        database.
    **kwargs :
        Any additional kwargs are passed to pd.DataFrame.to_sql()
    """
    engine = _return_engine(sqlpath)
    for col in drop:
        try:
            pdf.drop(col, axis=1, inplace=True)
        except ValueError:
            alt = get_close_matches(col, pdf.columns.tolist())
            print('Could not find column {}.'.format(col))
            print(alt)

    try:
        oldtable = pd.read_sql_table(table, engine)
    except ValueError:
        oldtable = None

    try:
        pdf.to_sql(table, engine, **kwargs)
    except:
        if oldtable is not None:
            oldtable.to_sql(table, engine, **kwargs)
            print("Error: Restoring old table!")
        raise
