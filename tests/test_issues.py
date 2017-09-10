# Copyright (c) 2017, Mayo Clinic
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

import unittest


class Issue1TestCase(unittest.TestCase):
    def test_url_input(self):
        from dirlistproc import DirectoryListProcessor

        def t1proc(ifn: str, ofn, _):
            self.assertEqual('http://fhirtest.uhn.ca/baseDstu3/Patient?_format=json\&gender=male', ifn)
            self.assertEqual('test/patients/_url1', ofn)
            return True

        def t2proc(ifn: str, ofn: str, _):
            if '://' in ifn:
                self.assertEqual('http://fhirtest.uhn.ca/baseDstu3/Patient?_format=json\&gender=male', ifn)
                self.assertEqual('test/patients/_url1.ttl', ofn)
            else:
                self.assertEqual('x.json', ifn)
                self.assertEqual('test/patients/x.ttl', ofn)
            return True

        def t3proc(ifn: str, ofn: str, _):
            return (ifn == 'http://ex.org/item1' and ofn == 'test/dir/_url1.ttl') or \
                   (ifn == 'x.json' and ofn == 'test/dir/x.ttl') or \
                   (ifn == 'http://ex.org/item2' and ofn == 'test/dir/_url4.ttl')


        args = "-i http://fhirtest.uhn.ca/baseDstu3/Patient?_format=json\&gender=male -od test/patients"
        dlp = DirectoryListProcessor(args.split(), "Test Processor", '', '')
        self.assertEqual((1, 1), dlp.run(t1proc))

        args = "-i http://fhirtest.uhn.ca/baseDstu3/Patient?_format=json\&gender=male x.json -od test/patients"
        dlp = DirectoryListProcessor(args.split(), "Test Processor", '.json', '.ttl')
        self.assertEqual((2, 2), dlp.run(t2proc))

        args = "-i http://ex.org/item1 x.json x.foo http://ex.org/item2 -od test/dir"
        dlp = DirectoryListProcessor(args.split(), "Test Processor", ".json", ".ttl")
        self.assertEqual((3, 3), dlp.run(t3proc))

    def test_invalid_indir(self):
        # Issue 2 - invalid input directory not detected
        from dirlistproc import DirectoryListProcessor

        args = "-id foo"
        with self.assertRaises(SystemExit):
            DirectoryListProcessor(args.split(), "Test Processor", ".json", ".ttl")

        args = "-id testfiles/f1.txt"
        with self.assertRaises(SystemExit):
            DirectoryListProcessor(args.split(), "Test Processor", ".json", ".ttl")




if __name__ == '__main__':
    unittest.main()
