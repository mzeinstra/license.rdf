"""
license.py

Maintenance script for license RDF.

Original script developed by Will Frank;
* updated by Nathan Yergler to use new XML schema and explicit options.
* updated by Nathan Yergler to generate RDF files.

(c) 2005-2007, Creative Commons, Will Frank, Nathan R. Yergler
licensed to the public under the GNU GPL version 2.
"""

import pkg_resources
import sys
import os
import urlparse
from argparse import ArgumentParser

from support import *

# *******************************************************************
# * command line option support

def get_add_option_parser():
    """Define an option parser for the add_license tool and return it."""
    
    usage = "usage: %prog [options] <new_uri>"
    parser = OptionParser(usage)


    # source options
    parser.add_option( '--rdf_dir', dest='rdf_dir', action='store',
                       help='Directory containing the license RDF files; '
                       'defaults to ./cc/licenserdf/licenses/')

    # license properties
    parser.add_option( '-b', '--based-on', dest='based_on',
                       help='URI of the license the new one is based on.')
    parser.add_option( '-l', '--legalcode', dest='legalcode',
                       help='URI of the legalcode; defaults to the license '
                       'URI + "/legalcode".')
    parser.add_option( '-j', '--jurisdiction', dest='jurisdiction',
                       help='URI of the jurisdiction for the new license; '
                       'defaults to Unported.')
    parser.add_option( '-v', '--version', dest='version',
                       help='Version number to add; defaults to 3.0.'
                       )
    
    parser.set_defaults(
        rdf_dir=pkg_resources.resource_filename(
            'cc.licenserdf', 'licenses'),
        version='3.0', 
        legalcode=None,
        jurisdiction=None)
    
    return parser


def get_addall_option_parser():

    parser = get_add_option_parser()
    parser.set_usage("usage: %prog [options]")

    parser.add_option( '--jc', '--jurisdiction-code', dest='jurisdiction_code',
                       help='Short code of the jurisdiction to add.')
    parser.add_option( '-c', '--codes', dest='codes',
                       help='License codes to add, comma delimited '
                       '(defaults to primary six)',
                       )

    parser.set_defaults(codes="by-nc,by,by-nc-nd,by-nc-sa,by-sa,by-nd")

    return parser

# * 
# *******************************************************************

def _license_rdf_filename(rdf_dir, license_uri):
    """Map a license URI to the filesystem filename containing the RDF."""

    url_pieces = urlparse.urlparse(license_uri)
    filename = os.path.join(rdf_dir, 
                            "_".join([url_pieces[1]] +
                                     url_pieces[2].split('/')[1:]
                                     ) + '.rdf'
                            )

    return os.path.abspath(filename)

def replace_predicate(graph, s, p, new_value):
    """If (s, p, *) exists in graph, remove it; add (s, p, new_value) 
    to the graph."""

    if (p in graph.predicates(s)):
        graph.remove((s, p, None))

    graph.add((s, p, new_value))

def add_license(license_uri, based_on_uri, version, jurisdiction, 
                legalcode_uri, rdf_dir):
    """Create a new license based on an existing one.  Write the resulting
    graph to the rdf_dir."""

    # make sure the license_uri ends with a slash
    if license_uri[-1] != '/':
        license_uri += '/'

    # create the graph for the new license
    license = graph()

    if based_on_uri:
        # we're starting from an existing license

        # load the based on graph
        based_on = load_graph(_license_rdf_filename(rdf_dir, based_on_uri))

        # copy base assertions
        for (p, o) in based_on.predicate_objects(URIRef(based_on_uri)):
            license.add((URIRef(license_uri), p, o))

        replace_predicate(license, URIRef(license_uri), NS_DC.source, 
                          URIRef(based_on_uri))

    else:
        # add the basic framework -- this is a license
        license.add((URIRef(license_uri), NS_RDF.type, NS_CC.License))

    # add the jurisdiction, version, source
    if jurisdiction is not None:
        replace_predicate(license, URIRef(license_uri), NS_CC.jurisdiction,
                          URIRef(jurisdiction))
    else:
        # unported; remove any jurisdiction assertion
        license.remove((URIRef(license_uri), NS_CC.jurisdiction, None))

    # set/replace the version
    replace_predicate(license, URIRef(license_uri), NS_DCQ.hasVersion, 
                      Literal(version))

    # determine the legalcode URI
    if legalcode_uri is None:
        legalcode_uri = license_uri + "legalcode"

    # add the legalcode predicate
    replace_predicate(license, URIRef(license_uri), NS_CC.legalcode,
                      URIRef(legalcode_uri))

    # write the graph out
    save_graph(license, _license_rdf_filename(rdf_dir, license_uri))

def add_all_cli():
    """Run add for the core six licenses."""

    parser = get_addall_option_parser()
    opts, args = parser.parse_args()

    for code in opts.codes.split(','):
        base_url = "http://creativecommons.org/licenses/%s/%s/" % (code, 
                                                                   opts.version)

        license_url = "%s%s/" % (base_url, opts.jurisdiction_code)

        add_license(license_url, base_url, opts.version, opts.jurisdiction,
                    None, opts.rdf_dir)


def add_cli():
    """Run the add_license tool."""
    parser = get_add_option_parser()
    opts, args = parser.parse_args()

    add_license(args[0], opts.based_on, opts.version, opts.jurisdiction,
                opts.legalcode, opts.rdf_dir)


def get_args():
    """Get all args taken by this app"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")

    add_subparser = subparsers.add_parser(
        'add', help="Add one or more licenses.")
    legalcode_subparser = subparsers.add_parser(
        'legalcode', help="Add one or more licenses.")

    def add_common_args(subparser):
        # source options
        subparser.add_argument(
            '--rdf_dir', dest='rdf_dir', action='store',
            help='Directory containing the license RDF files; '
            'defaults to ./cc/licenserdf/licenses/')

    ## Add subparser options
    add_common_args(add_subparser)
    add_subparser.add_argument(
        '--all', action="store_true",
        help="Run add for the core six licenses")
    add_subparser.add_argument(
        '--launched', action="store_true",
        help="Mark these licenses as launched")
        
    # license properties
    add_subparser.add_argument(
        '-b', '--based-on', dest='based_on',
        help='URI of the license the new one is based on.')
    add_subparser.add_argument(
        '-l', '--legalcode', dest='legalcode',
        help='URI of the legalcode; defaults to the license '
        'URI + "/legalcode".')
    add_subparser.add_argument(
        '--jurisdiction', dest='jurisdiction',
        help='URI of the jurisdiction for the new license; '
        'defaults to Unported.')
    add_subparser.add_argument(
        '-j', '--jurisdiction-code', dest='jurisdiction_code', required=True,
        help='Short code of the jurisdiction to add.')
    add_subparser.add_argument(
        '-v', '--version', dest='version',
        help='Version number to add; defaults to 3.0.')
    add_subparser.add_argument(
        '-c', '--codes', dest='codes',
        help=('License codes to add, comma delimited '
              '(defaults to primary six)'))

    add_subparser.add_argument(
        'codes', nargs='*',
        help=('list of license codes to add '
              '(if --all is not specified)'))

    parser.set_defaults(
        rdf_dir=pkg_resources.resource_filename(
            'cc.licenserdf', 'licenses'),
        version='3.0', 
        legalcode=None,
        jurisdiction=None)

    return parser.parse_args()


def cli():
    opts = get_args()
    
    if opts.all:
        license_codes = (
            'by-nc', 'by', 'by-nc-nd', 'by-nc-sa', 'by-sa', 'by-nd')
    else:
        license_codes = opts.codes

    if not license_codes:
        print "Either a list of codes must be provided as arguments,"
        print "or else the --all flag must be used.  (Did you mean --all?)"
        return 1

    import pdb
    pdb.set_trace()
    for license_code in license_codes:
        base_url = "http://creativecommons.org/licenses/%s/%s/" % (
            license_code, opts.version)

        license_url = "%s%s/" % (base_url, opts.jurisdiction_code)

        add_license(
            license_url, opts.based_on, opts.version, opts.jurisdiction,
            opts.legalcode, opts.rdf_dir)

