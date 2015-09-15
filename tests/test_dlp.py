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
#     Neither the name of the <ORGANIZATION> nor the names of its contributors
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
import unittest
import sys

import dirlistproc


class MyTestCase(unittest.TestCase):
    def test_single_in_out(self):
        def t1proc(ifn, ofn, _):
            self.assertEqual('inp.txt', ifn)
            self.assertEqual('out.txt', ofn)
            return True

        args = "-i inp.txt -o out.txt"
        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test Processor", '', '')
        self.assertEqual((1, 1), dlp.run(t1proc))

    def test_no_return(self):
        def t1proc(ifn, ofn, _):
            self.assertEqual('inp.txt', ifn)
            self.assertEqual('out.txt', ofn)

        args = "-i inp.txt -o out.txt"
        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test Processor", '', '')
        self.assertEqual((1, 1), dlp.run(t1proc))

    def test_simple_dir(self):
        def t2proc(ifn, ofn, _):
            self.assertTrue((ifn == 'testfiles/f1.txt' and ofn == 'testout/f1.xtx') or
                            (ifn == 'testfiles/f2.txt' and ofn == 'testout/f2.xtx'))
            return True
        args = "-id testfiles -od testout"
        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test Processor", '.txt', '.xtx')
        self.assertEqual((2, 2), dlp.run(t2proc))

        def t2proc2(ifn, _, __):
            return 'f1' in ifn

        self.assertEqual((2, 1), dlp.run(t2proc2))

    def test_args_tweak(self):
        args = "-i inp.txt -o out.txt -id inputdir -od outputdir -x foo -t"

        def add2args(args_: argparse.ArgumentParser):
            args_.add_argument('-x', '--special', help="A really special argument")
            args_.add_argument('-t', '--two', help="Another argument", action="store_true")

        def addparm(opts: argparse.Namespace):
            opts.bag = "HERE"

        def t3proc(_, __, opts):
            self.assertEqual("HERE", opts.bag)
            self.assertTrue(opts.two)
            self.assertEqual("foo", opts.special)

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Special Processor", '.txt', '.xtx', add2args, addparm)
        dlp.run(t3proc)

    def test_recursive(self):
        args = "-id testfiles -od testout"
        expected_names = {'testfiles/f1.xml': 'testout/f1.foo',
                          'testfiles/f2.xml': 'testout/f2.foo',
                          'testfiles/d1/f3.xml': 'testout/d1/f3.foo',
                          'testfiles/d1/d2/f4.xml': 'testout/d1/d2/f4.foo',
                          }

        def tproc(ifn, ofn, _):
            self.assertTrue(ifn in expected_names)
            self.assertEqual(expected_names[ifn], ofn)
            return True

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".foo")
        self.assertEqual((4, 4), dlp.run(tproc))

    def test_no_inout(self):

        def tproc(ifn, ofn, _):
            self.assertIsNone(ifn)
            self.assertIsNone(ofn)

        dlp = dirlistproc.DirectoryListProcessor([], "", ".xml", ".foo")
        self.assertEqual((1, 1), dlp.run(tproc))

    def test_diff_prefix_length(self):

        def t2proc(ifn, ofn, _):
            if ifn == 'testfiles/f1.txt':
                self.assertEqual('testout/f1.2222', ofn)
            elif ifn == 'testfiles/f2.txt':
                self.assertEqual('testout/f2.2222', ofn)
            else:
                self.assertTrue(False, "Unknown input file %s" % ifn)
            return True

        args = "-id testfiles -od testout"
        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test Processor", '.txt', '.2222')
        self.assertEqual((2, 2), dlp.run(t2proc))

        def t2proc2(ifn, ofn, _):
            if ifn == 'testfiles/f1.txt':
                self.assertEqual('testout/f1.2', ofn)
            elif ifn == 'testfiles/f2.txt':
                self.assertEqual('testout/f2.2', ofn)
            else:
                self.assertTrue(False, "Unknown input file %s" % ifn)
            return True

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test Processor", '.txt', '.2')
        self.assertEqual((2, 2), dlp.run(t2proc2))

    def test_stop_on_error(self):
        args = "-id testfiles -od testout -s"

        def tproc(ifn, ofn, _):
            return "f1" in ifn

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".foo")
        self.assertEqual((2, 1), dlp.run(tproc))

        args = "-id testfiles -od testout"
        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".foo")
        self.assertEqual((4, 1), dlp.run(tproc))

    def test_od_and_file(self):
        args = "-i foo.xml -o foo.txt -od another/dir"

        def tproc(ifn, ofn, _):
            return ifn == "foo.xml" and ofn == "another/dir/foo.txt"

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")
        self.assertEqual((1, 1), dlp.run(tproc))

    class MemFile:
        def write(self, txt):
            pass

    def test_multiple_files(self):
        # Ground sys.stderr
        glob_sys_stderr = sys.stderr
        sys.stderr = self.MemFile()

        # Input and output matches
        args = "-i foo.xml bar.xml -o foo.txt bar.txt"

        def tproc(ifn, ofn, _):
            return (ifn == "foo.xml" and ofn == "foo.txt") or (ifn == "bar.xml" and ofn == "bar.txt")

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")
        self.assertEqual((2, 2), dlp.run(tproc))

        # More output than input -- not allowed
        args = "-i foo.xml -o foo.txt bar.txt"
        with self.assertRaises(SystemExit):
            dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")

        # More input than output -- not allowed
        args = "-i foo.xml bar.xml -o foo.txt"
        with self.assertRaises(SystemExit):
            dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")

        # Two outputs with no inputs -- not allowed
        args = "-o foo.txt bar.txt"
        with self.assertRaises(SystemExit):
            dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")

        # One input, no outputs -- ok
        args = "-i foo.xml"

        def tproc2(ifn, ofn, _):
            return ifn == "foo.xml" and ofn is None

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")
        self.assertEqual((1, 1), dlp.run(tproc2))

        # One output, no inputs -- ok
        args = "-o foo.txt"

        def tproc3(ifn, ofn, _):
            return ifn is None and ofn == "foo.txt"

        dlp = dirlistproc.DirectoryListProcessor(args.split(), "Test", '.xml', ".txt")
        self.assertEqual((1, 1), dlp.run(tproc3))

        sys.stderr = glob_sys_stderr


if __name__ == '__main__':
    unittest.main()
