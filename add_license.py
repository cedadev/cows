"""
# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

Insert a copywrite notice at the top of any python files given as arguments.

"""

import datetime
import os, re, sys
import optparse

license_text = """
# BSD Licence
# Copyright (c) %(year)s, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
%(msg)s

""".lstrip()

detect_rexp = re.compile(r'''^[#] BSD Licence''', re.M)

#[#] Copyright (c) \d+, Science & Technology Facilities Council (STFC)
#[#] All rights reserved.
#''', re.M)


default_message = """
See the LICENSE file in the source distribution of this software for
the full license text.
""".strip()

def add_license(filename, year=None, msg=None):
    """
    Add a license to a file
    
    """

    ext = os.path.splitext(filename)[1][1:]
    #!TODO: Add xml when fixme below complete
    if ext not in ['py']:
        raise ValueError('Extension %s not supported' % ext)
        
    if year is None:
        year = datetime.datetime.now().year
    if msg is None:
        msg = default_message

    msg = '\n'.join('# %s'%x for x in msg.split('\n'))

    license = license_text % dict(msg=msg, year=year)

    fh_in = open(filename)
    fh_out = open('%s.tmp' % filename, 'w')

    if ext == 'py':
        line = fh_in.readline()
        if line[:2] == '#!':
            fh_out.write(line)
            line = fh_in.readline()
            fh_out.write(license)
        else:
            fh_out.write(license)
            fh_out.write(line)

    #!FIXME: This bit is broken because it doesn't look for <!DOCTYPE!>
    #    declarations
    elif ext == 'xml':
        line = fh_in.readline()
        if re.match(r'<\?xml', line):
            fh_out.write(line)
            line = fh_in.readline()

        fh_out.write('<!--\n')
        fh_out.write(license)
        fh_out.write('-->\n')


    for line in fh_in:
        fh_out.write(line)

    fh_in.close()
    fh_out.close()
    os.system('mv %s %s.orig' % (filename, filename))
    os.system('mv %s.tmp %s' % (filename, filename))
    print 'Added license to %s, original is %s.orig' % (filename, filename)


def detect_license(filename):
    file_txt = open(filename).read()

    if detect_rexp.search(file_txt):
        return True
    else:
        return False

def main(argv=sys.argv[1:]):

    parser = optparse.OptionParser()
    parser.add_option('-d', '--detect', dest='detect', action='store_true',
                      default=False,
                      help='Detect whether each file has a license')

    options, args = parser.parse_args(argv)

    if options.detect:
        for filename in args:
            if not detect_license(filename):
                print filename
    else:
        for filename in args:
            add_license(filename)
    

if __name__ == '__main__':
    main()
