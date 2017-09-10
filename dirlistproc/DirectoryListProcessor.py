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
import shlex
from typing import List, Optional, Callable, Tuple


def _parser_exit(parser: argparse.ArgumentParser, proc: "DirectoryListProcessor", _=0,
                 message: Optional[str]=None) -> None:
    """
    Override the default exit in the parser.
    :param parser:
    :param _: exit code.  Unused because we don't exit
    :param message: Optional message
    """
    if message:
        parser._print_message(message, sys.stderr)
    proc.successful_parse = False


class DirectoryListProcessor:
    def __init__(self, args: Optional[List[str]], description: str, infile_suffix: Optional[str],
                 outfile_suffix: Optional[str], addargs: Optional[Callable[[argparse.ArgumentParser], None]]=None,
                 postparse: Optional[Callable[[argparse.Namespace], None]]=None,
                 noexit: bool=False, fromfile_prefix_chars: Optional[str]=None):
        """ Build a directory list processor
        :param args: Input arguments such as supplied from sys.argv.  None means use sys.argv
        :param description: Description of the function.  Appears in a help string
        :param infile_suffix: Suffix filter on input file.  If absent, all files not starting with "." pass
        :param outfile_suffix: Suffix to add to output file.  If absent, name is same as input
        :param addargs: Function to add arguments before parsing.  Signature: addargs(parser: argparse.ArgumentParser)
        :param postparse: Function to review arguments post parsing.  Signature: postparse(opts: argparse.Namespace)
        :param noexit: Do not exit the parser on error. Primarily for testing.  If an exitable error occurs,
        succesful_parse is set to False
        :param fromfile_prefix_chars: parser file prefix characters
        """
        self.infile_suffix = infile_suffix
        self.outfile_suffix = outfile_suffix
        self.successful_parse = True
        self.fromfile_prefix_chars = fromfile_prefix_chars if fromfile_prefix_chars else ""
        self.parser = argparse.ArgumentParser(description=description, fromfile_prefix_chars=fromfile_prefix_chars)
        self.parser.add_argument("-i", "--infile", help="Input file(s)", nargs="*")
        self.parser.add_argument("-id", "--indir", help="Input directory")
        self.parser.add_argument("-o", "--outfile", help="Output file(s)", nargs="*")
        self.parser.add_argument("-od", "--outdir", help="Output directory")
        self.parser.add_argument("-f", "--flatten", help="Flatten output directory", action="store_true")
        self.parser.add_argument("-s", "--stoponerror", help="Stop on processing error", action="store_true")
        if addargs is not None:
            addargs(self.parser)
        if noexit:
            self.parser.exit = lambda *args: _parser_exit(self.parser, self, *args)
        self.opts = self.parser.parse_args(self.decode_file_args(args if args is not None else sys.argv[1:]))
        if self.successful_parse:
            n_infiles = len(self.opts.infile) if self.opts.infile else 0
            n_outfiles = len(self.opts.outfile) if self.opts.outfile else 0
            if (n_infiles > 1 or n_outfiles > 1) and n_infiles != n_outfiles and n_outfiles > 1:
                self.parser.error("Number of input and output files must match")
            if postparse is not None:
                postparse(self.opts)

    def decode_file_args(self, argv: List[str]) -> List[str]:
        """
        Preprocess any arguments that begin with the fromfile prefix char(s).
        This replaces the one in Argparse because it
            a) doesn't process "-x y" correctly and
            b) ignores bad files
        :param argv: raw options list
        :return: options list with file references replaced
        """
        for arg in [arg for arg in argv if arg[0] in self.fromfile_prefix_chars]:
            argv.remove(arg)
            with open(arg[1:]) as config_file:
                argv += shlex.split(config_file.read())
                return self.decode_file_args(argv)
        return argv

    @staticmethod
    def _proc_error(ifn: str, e: Exception) -> None:
        """ Report an error
        :param ifn: Input file name
        :param e: Exception to report
        """
        type_, value_, traceback_ = sys.exc_info()
        traceback.print_tb(traceback_, file=sys.stderr)
        print(file=sys.stderr)
        print("***** ERROR: %s" % ifn, file=sys.stderr)
        print(str(e), file=sys.stderr)

    def _call_proc(self,
                   proc: Callable[[Optional[str], Optional[str], argparse.Namespace], bool],
                   ifn: Optional[str],
                   ofn: Optional[str]) -> bool:
        """ Call the actual processor and intercept anything that goes wrong
        :param proc: Process to call
        :param ifn: Input file name to process.  If absent, typical use is stdin
        :param ofn: Output file name. If absent, typical use is stdout
        :return: true means process was successful
        """
        rslt = False
        try:
            rslt = proc(ifn, ofn, self.opts)
        except Exception as e:
            self._proc_error(ifn, e)
        return True if rslt or rslt is None else False

    def _check_filter(self,
                      fn: Optional[str],
                      dirpath: Optional[str],
                      file_filter: Optional[Callable[[str], bool]],
                      file_filter_2: Optional[Callable[[Optional[str], str, argparse.Namespace], bool]]) -> bool:
        rval = (fn is None or ('://' in fn or fn.endswith(self.infile_suffix))) and \
           (not file_filter or file_filter(fn)) and \
           (not file_filter_2 or file_filter_2(fn, dirpath if dirpath is not None else '', self.opts)) and \
           (file_filter or file_filter_2 or fn is None or not fn.startswith('.'))
        return rval

    def run(self,
            proc: Callable[[Optional[str], Optional[str], argparse.Namespace], Optional[bool]],
            file_filter: Optional[Callable[[str], bool]]=None,
            file_filter_2: Optional[Callable[[Optional[str], str, argparse.Namespace], bool]]=None) \
            -> Tuple[int, int]:
        """ Run the directory list processor calling a function per file.
        :param proc: Process to invoke. Args: input_file_name, output_file_name, argparse options. Return pass or fail.
                     No return also means pass
        :param file_filter: Additional filter for testing file names, types, etc.
        :param file_filter_2: File filter that includes directory, filename and opts
                        (separate for backwards compatibility)
        :return: tuple - (number of files passed to proc: int, number of files that passed proc)
        """
        nfiles = 0
        nsuccess = 0

        # List of one or more input and output files
        if self.opts.infile:
            for file_idx in range(len(self.opts.infile)):
                in_f = self.opts.infile[file_idx]
                if self._check_filter(in_f, self.opts.indir, file_filter, file_filter_2):
                    fn = os.path.join(self.opts.indir, in_f) if self.opts.indir else in_f
                    nfiles += 1
                    if self._call_proc(proc, fn, self._outfile_name('', fn, outfile_idx=file_idx)):
                        nsuccess += 1
                    elif self.opts.stoponerror:
                        return nfiles, nsuccess

        # Single input from the command line
        elif not self.opts.indir:
            if self._check_filter(None, None, file_filter, file_filter_2):
                nfiles += 1
                if self._call_proc(proc, None, self._outfile_name('', '')):
                    nsuccess += 1

        # Input directory that needs to be navigated
        else:
            for dirpath, _, filenames in os.walk(self.opts.indir):
                for fn in filenames:
                    if self._check_filter(fn, dirpath, file_filter, file_filter_2):
                        nfiles += 1
                        if self._call_proc(proc, os.path.join(dirpath, fn), self._outfile_name(dirpath, fn)):
                            nsuccess += 1
                        elif self.opts.stoponerror:
                            return nfiles, nsuccess

        return nfiles, nsuccess

    def _outfile_name(self, dirpath: str, infile: str, outfile_idx: int=0) -> Optional[str]:
        """ Construct the output file name from the input file.  If a single output file was named and there isn't a
        directory, return the output file.
        :param dirpath: Directory path to infile
        :param infile: Name of input file
        :param outfile_idx: Index into output file list (for multiple input/output files)
        :return: Full name of output file or None if output is not otherwise supplied
        """
        if not self.opts.outfile and not self.opts.outdir:
            # Up to the process itself to decide what do do with it
            return None

        if self.opts.outfile:
            # Output file specified - either one aggregate file or a 1 to 1 list
            outfile_element = self.opts.outfile[0] if len(self.opts.outfile) == 1 else self.opts.outfile[outfile_idx]

        elif self.opts.infile:
            # Input file name(s) have been supplied
            if '://' in infile:
                # Input file is a URL -- generate an output file of the form "_url[n]"
                outfile_element = "_url{}".format(outfile_idx + 1)
            else:
                outfile_element = os.path.basename(infile).rsplit('.', 1)[0]

        else:
            # Doing an input directory to an output directory
            relpath = dirpath[len(self.opts.indir) + 1:] if not self.opts.flatten and self.opts.indir else ''
            outfile_element = os.path.join(relpath, os.path.split(infile)[1][:-len(self.infile_suffix)])
        return (os.path.join(self.opts.outdir, outfile_element) if self.opts.outdir else outfile_element) + \
               (self.outfile_suffix if not self.opts.outfile and self.outfile_suffix else '')


def default_proc(ifn: Optional[str], ofn: Optional[str], _: argparse.Namespace) -> bool:
    print("Input file name: %s -- Output file name: %s" % (ifn if ifn is not None else "stdin",
                                                           ofn if ofn is not None else "stdout"))
    return True

if __name__ == '__main__':
    DirectoryListProcessor(None, "DLP Framework", "", "").run(default_proc)
