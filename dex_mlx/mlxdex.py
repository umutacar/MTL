#!/usr/bin/python
import re
import sys
import os

import pervasives.syntax as syntax
import pervasives.os_utils as os_utils

## Some constants

PYTHON = 'python'
SPACE = ' '
PERIOD = '.'
DEX_EXTENSION = '.dex'
MLX_EXTENSION = '.mlx'

######################################################################
## BEGIN: Fix various files
## REQUIRES DIDEROT_HOME environment variable
## REQUIRES LATEX_PREAMBLE file, see below

MTL_HOME = os.environ['MTL_HOME']
DIDEROT_HOME = os.environ['DIDEROT_HOME']
DEX_DIR =  MTL_HOME + '/dex_mlx/'
MLX_DIR =  DIDEROT_HOME + '/mlx/'
LATEX_PREAMBLE_FILE =  '/Users/umut/teach/adps-diderot/latex_preamble/preamble.tex'

## END: Fix your username / path here.
######################################################################

# scripts
DEX_2_MLX = DEX_DIR + 'dex2mlx.py'
MLX_ELABORATE = MLX_DIR + 'elaborate.py'

def main(argv):
  print 'Executing:', sys.argv[0], str(sys.argv)
  if len(sys.argv) != 2: 
    print 'Usage: publish.py inputfile'
    sys.exit()


  # get current working directory
  root_dir = os.getcwd()

  # get the file and its path
  infile_name = sys.argv[1]
  (path, infile_name) = os.path.split(infile_name) 

  # cd to path
  os.chdir(path)

  # create the various file names
  (infile_name_first, infile_ext) = infile_name.split (syntax.PERIOD) 
  outfile_mlx = infile_name_first + MLX_EXTENSION
  outfile_mlx_elaborated = infile_name_first + MLX_EXTENSION + MLX_EXTENSION
  
  # convert dex to mlx
  command = PYTHON + syntax.SPACE + DEX_2_MLX + syntax.SPACE + infile_name + syntax.SPACE + LATEX_PREAMBLE_FILE
  print 'Executing command:', command
  os.system(command)

  # elaborate mlx
  command = PYTHON + syntax.SPACE + MLX_ELABORATE + syntax.SPACE + outfile_mlx + syntax.SPACE + outfile_mlx_elaborated
  print 'Executing command:', command
  os.system(command)

  # cp to Desktop
  os_utils.mv_file_to(outfile_mlx_elaborated, outfile_mlx)  

  # cd to starting directory
  os.chdir(root_dir)

if __name__ == "__main__":
    main(sys.argv)
