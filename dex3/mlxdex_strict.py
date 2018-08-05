#!/usr/bin/env python
#
# Translates dex to strict mlx, taking in a latex_preamble_file as an
# argument. latex_preamble_file can also be supplied by an environment
# variable.
#
# Note: in addition to the MeTaL environment, this alse requires
# the mlx package (of diderot) to be available in the pythonpath. 
#
# Note that diderot's beamer does not require strictification anymore.
# So this is mostly here for historical reasons.


import re
import sys
import os

import pervasives.syntax as syntax
import pervasives.os_utils as os_utils
import parser
import dex2mlx
import mlx.strictify

## Some constants

SPACE = ' '
PERIOD = '.'
DEX_EXTENSION = '.dex'
MLX_EXTENSION = '.mlx'


def main(infile_name, latex_preamble_file):
  # get current working directory
  root_dir = os.getcwd()

  # get the file and its path
  (path, infile_name_file) = os.path.split(infile_name) 

  # create the various file names
  (infile_name_first, infile_ext) = infile_name_file.split (syntax.PERIOD) 
  core_infile = os_utils.mk_file_name_derivative(infile_name, os_utils.CORE)
  core_infile_mlx = os_utils.mk_file_name_ext(core_infile, os_utils.MLX_EXTENSION)
  outfile_mlx = os_utils.mk_file_name_ext(infile_name, os_utils.MLX_EXTENSION)
  outfile_mlx_strict = os_utils.mk_file_name_derivative(core_infile_mlx, os_utils.STRICT)

   # convert dex to core dex by using the parser
  parser.main(infile_name, True, True)
  print 'Translating', infile_name, 'to core language.'

  # convert core dex to mlx
  print 'Translating to mlx'
  dex2mlx.main(core_infile, latex_preamble_file)

   # strictify mlx
  print 'Elaborating mlx', core_infile_mlx
  mlx.strictify.main(core_infile_mlx, outfile_mlx_strict)

  # rename and copy to Desktop
  os_utils.mv_file_to(outfile_mlx_strict, outfile_mlx)  
  print 'mlxdex completed.  Output is in', outfile_mlx

  # cd to starting directory
  os.chdir(root_dir)

if __name__ == "__main__":
  print 'Executing:', sys.argv[0], str(sys.argv)
  latex_preamble_file = None
  if len(sys.argv) != 3: 
    try: 
      latex_preamble_file = os.environ['DIDEROT_LATEX_PREAMBLE']
    except KeyError:
      print 'Usage: mlxdex.py inputfile latex_preamble_file'
      sys.exit()


  infile_name = sys.argv[1]
  if latex_preamble_file is None:
    latex_preamble_file = sys.argv[2]
  
  main(infile_name, latex_preamble_file)
