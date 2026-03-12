# Copyright 2012-2015 by Alex Holehouse - see LICENSE for more info
# Contact at alex.holehouse@wustl.edu

""" This is the backend module which facilitates data structures, utility functions and other stuff the user shouldn't deal with. Everything here isn't designed to be used as part of the geeneus API - the only functions which should be used there are the public ones in the geeneus.
"""
from proteomescout_worker.geeneus.backend import GeneObject
from proteomescout_worker.geeneus.backend import GeneParser
from proteomescout_worker.geeneus.backend import ProteinObject
from proteomescout_worker.geeneus.backend import ProteinParser
