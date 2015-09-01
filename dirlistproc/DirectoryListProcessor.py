# -*- coding: utf-8 -*-
# Copyright (c) 2015, Mayo Clinic
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#     Neither the name of the Mayo Clinic nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
import argparse
import os
import sys
import traceback


class DirectoryListProcessor:
    def __init__(self, args: list, description: str, infile_suffix: str, outfile_suffix: str, addargs=None,
                 postparse=None):
        """ Build a directory list processor
        :param args: Input arguments such as supplied from main
        :param description: Description of the function.  Appears in a help string
        :param infile_suffix: Suffix filter on input file.  If absent, all files not starting with "." pass
        :param outfile_suffix: Suffix to add to output file.  If absent, name is same as input
        :param addargs: Function to add arguments before parsing.  Signature: addargs(parser: argparse.ArgumentParser)
        :param postparse: Function to review arguments post parsing.  Signature: postparse(opts: argparse.Namespace)
        """
        self.infile_suffix = infile_suffix
        self.outfile_suffix = outfile_suffix
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("-i", "--infile", help="Input file")
        parser.add_argument("-id", "--indir", help="Input directory")
        parser.add_argument("-o", "--outfile", help="Output file")
        parser.add_argument("-od", "--outdir", help="Output directory")
        parser.add_argument("-f", "--flatten", help="Flatten output directory", action="store_true")
        parser.add_argument("-s", "--stoponerror", help="Stop on processing error", action="store_true")
        if addargs:
            addargs(parser)
        self.opts = parser.parse_args(args)
        if postparse:
            postparse(self.opts)

    @staticmethod
    def _proc_error(ifn, e):
        type_, value_, traceback_ = sys.exc_info()
        traceback.print_tb(traceback_, file=sys.stderr)
        print(file=sys.stderr)
        print("***** ERROR: %s" % ifn, file=sys.stderr)
        print(str(e), file=sys.stderr)

    def _call_proc(self, proc, ifn: str, ofn: str):
        rslt = False
        try:
            rslt = proc(ifn, ofn, self.opts)
        except Exception as e:
            self._proc_error(ifn, e)
        return rslt or rslt is None

    def run(self, proc, file_filter=None) -> tuple:
        """ Run the directory list processor calling a function per file.
        :param proc: Process to invoke
        :param file_filter: Additional filter for testing file names, types, etc.
        :return: tuple - (num_files_processed: int, num_files_passed)
        """
        if self.opts.infile:
            fn = os.path.join(self.opts.indir, self.opts.infile) if self.opts.indir else self.opts.infile
            if file_filter and not file_filter(fn):
                return 1, 0
            return 1, 1 if self._call_proc(proc, fn, self._outfile_name('', fn)) else 0
        elif not self.opts.indir:
            return 1, 1 if self._call_proc(proc, None, self._outfile_name('', '')) else 0
        else:
            nfiles = 0
            nsuccess = 0
            for dirpath, _, filenames in os.walk(self.opts.indir):
                for fn in filenames:
                    if (not file_filter or file_filter(fn)) and \
                            not fn.startswith('.') and fn.endswith(self.infile_suffix):
                        nfiles += 1
                        if self._call_proc(proc, os.path.join(dirpath, fn), self._outfile_name(dirpath, fn)):
                            nsuccess += 1
                        elif self.opts.stoponerror:
                            return nfiles, nsuccess

            return nfiles, nsuccess

    def _outfile_name(self, dirpath: str, infile: str) -> str:
        """ Construct the output file name from the input file.  If a single output file was named and there isn't a
        directory, return the output file.
        :param dirpath: Directory path to infile
        :param infile: Name of input file
        :return: Full name of output file
        """
        if self.opts.outfile or not self.opts.outdir:
            return self.opts.outfile
        else:
            relpath = dirpath[len(self.opts.indir) + 1:] if not self.opts.flatten and self.opts.indir else ''
            return os.path.join(self.opts.outdir, relpath,
                                os.path.split(infile)[1][:-len(self.infile_suffix)] + self.outfile_suffix)
