# dirlistproc
``dirlistproc`` is a command line driven directory processing framework that allows the specification of a set of input files, a target directory and a transformation process.

It accepts command line arguments that allow the specification of:

* One or more input files
* An input directory
* An output file
* An output directory
* An option that determines whether input directory structure should be preserved in the output directory
* An option that determines whether processing should stop if an error is encountered or continue

## Use
The `DirectoryListProcessor` constructor takes 6 input arguments:

1. the argument list -- if `None`, `sys.argv[1:]` is used
2. the name of the program for the `argparse` help function
3. the input file suffix filter.  If `None`, no filter is applied
4. the output file suffix.
5. process to add arguments before parse (optional) -- signature: `addargs(parser:argparse.ArgumentParser):`
6. process to valid and process parsed argument (optional) -- signature: `postparse(opts:argparse.Namespace)`

(Note that file names that begin with "." are always ignored)

The run function takes two arguments:
1. the file processor -- signature: `proc(input_file_name: str, output_file_name: str, opts: argparse.Namespace) -> bool:`
2. the input file filter (optional) -- signature: `filter(input_file_name) -> bool:`

## Examples

### TestSimpleExample.py
    import dirlistproc
    
    def proc_xml(input_fn: str, output_fn: str, _) -> bool:
        print("Converting %s to %s" % (input_fn, output_fn))
        return True
    
    def main():
        dlp = dirlistproc.DirectoryListProcessor(None, "Convert XML to Text", ".xml", ".txt")
        nfiles, nsuccess = dlp.run(proc_xml)
        print("Total=%d Successful=%d" % (nfiles, nsuccess))
    
    if __name__ == '__main__':
        main()

        
### Execution
    > cd tests
    > export PYTHONPATH=..
    > python TestSimpleExample.py -id testfiles -od ../output
    Converting testfiles/f1.xml to ../output/f1.txt
    Converting testfiles/f2.xml to ../output/f2.txt
    Converting testfiles/d1/f3.xml to ../output/d1/f3.txt
    Converting testfiles/d1/d2/f4.xml to ../output/d1/d2/f4.txt
    Total=4 Successful=4 
    >
    >  python TestSimpleExample.py -i foo.xml -o foo.txt
    Converting foo.xml to foo.txt
    Total=1 Successful=1
    > 
    > python TestSimpleExample.py -i foo.xml -od another/dir
    Converting foo.xml to another/dir/foo.txt
    Total=1 Successful=1
    >

    
### Flattening the output directory
The "-f" parameter indicates that the input directory structure should not be preserved in the output:

    > python TestSimpleExample.py -id testfiles -od ../output -f
    Converting testfiles/f1.xml to ../output/f1.txt
    Converting testfiles/f2.xml to ../output/f2.txt
    Converting testfiles/d1/f3.xml to ../output/f3.txt
    Converting testfiles/d1/d2/f4.xml to ../output/f4.txt
    Total=4 Successful=4
    
## Stop on error argument
The  "-s" parameter controls whether processing continues or stops when the processing function returns *False*:
 
### TestStopOnError.py
	    ...    
    def proc_xml(input_fn: str, output_fn: str, _) -> bool:
            if input_fn.startswith("E"):
                print("Fail on %s" % input_fn)
                return False
            print("Converting %s to %s" % (input_fn, output_fn))
            return True
      	...
###

    > python TestStopOnError.py -id testfiles -od ../output
    Converting testfiles/f1.xml to ../output/f1.txt
    Fail on testfiles/f2.xml
    Converting testfiles/d1/f3.xml to ../output/d1/f3.txt
    Converting testfiles/d1/d2/f4.xml to ../output/d1/d2/f4.txt
    Total=4 Successful=3
    >
    > python TestStopOnError.py -id testfiles -od ../output -s
    Converting testfiles/f1.xml to ../output/f1.txt
    Fail on testfiles/f2.xml
    Total=2 Successful=1
    >


## Input File Filters

     
### TestInputFilter.py
      ...
    def inp_filtr(input_fn):
        print("Filtr %s" % input_fn)
        return "f4" not in input_fn
      ...
              
       nfiles, nsuccess = dlp.run(proc_xml, inp_filtr)
        
### 

    > python TestInputFilter.py -id testfiles
    Filtr .nosee.txt
    Filtr f1.txt
    Filtr f1.xml
    Converting testfiles/f1.xml to None
    Filtr f2.txt
    Filtr f2.xml
    Converting testfiles/f2.xml to None
    Filtr f3.xml
    Converting testfiles/d1/f3.xml to None
    Filtr f4.xml
    Total=3 Successful=3
    >

## Argument processing
The `addargs` process allows additional arguments to be added to the argument parser.

The `postparse` process allows the validation and processing of the parsed input arguments

### TestOptions.py
    import dirlistproc
    import argparse
    
    def proc_xml(input_fn: str, output_fn: str, opts: argparse.Namespace) -> bool:
        print("Converting %s to %s" % (input_fn, output_fn))
        return opts.noconvert
    
    def addargs(args: argparse.ArgumentParser):
        args.add_arg("-n", "--noconvert", help="Just print instead of converting", action="store_true")
    
    def procargs(opts: argparse.Namespace):
        if opts.noconvert:
            print("WARNING: no processing is occuring")
    
    def main():
        dlp = dirlistproc.DirectoryListProcessor(None, "Convert XML to Text", ".xml", ".txt", 
                                                 addargs=addargs, postparse=procargs)
        nfiles, nsuccess = dlp.run(proc_xml)
        print("Total=%d Successful=%d" % (nfiles, nsuccess))
    
    if __name__ == '__main__':
        main()
        
### Execution

    > python TestOptions.py -id testfiles -od foo
    Converting testfiles/f1.xml to foo/f1.txt
    Converting testfiles/f2.xml to foo/f2.txt
    Converting testfiles/d1/f3.xml to foo/d1/f3.txt
    Converting testfiles/d1/d2/f4.xml to foo/d1/d2/f4.txt
    Total=4 Successful=4
    >
    >python TestOptions.py -id testfiles -od foo -n
    WARNING: no processing is occurring 
    Converting testfiles/f1.xml to foo/f1.txt
    Converting testfiles/f2.xml to foo/f2.txt
    Converting testfiles/d1/f3.xml to foo/d1/f3.txt
    Converting testfiles/d1/d2/f4.xml to foo/d1/d2/f4.txt
    Total=4 Successful=0