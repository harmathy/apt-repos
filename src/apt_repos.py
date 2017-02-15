#!/usr/bin/python3 -Es
# -*- coding: utf-8 -*-
"""
   Display information about binary PACKAGE(s) in diverse apt-repositories and suites.
   This tool uses apt-mechanisms to scan for repositories/suites that are registered in
   a suites-file. For each repository/suite combination a local caching folder
   is created in which downloaded Packages files are stored, similar to the cache
   known from apt-cache which lives in /var/lib/apt/lists.
"""

import os
import sys
import argparse
import logging
import re

import apt_pkg
import apt.progress
import functools

#sys.path.append("./tqdm-4.11.2-py2.7.egg")
#from tqdm import tqdm

from lib_apt_repos import getSuites, RepoSuite, PackageField, QueryResult

def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("-d", "--debug", action="store_true", help="""
                                            Switch on debugging message printed to stderr.""")
    args.add_argument("-a", "--architecture", help="""
                                            Only show info for ARCH(s). The list of ARCHs is specified comma-separated.""")
    args.add_argument("-c", "--component", help="""
                                            Only show info for COMPONENT(s). The list of COMPONENTs is specified comma-separated.
                                            Note: component and section fields are not exactly the same. A component is only the first part
                                            of a section (everything before the '/'). There is also a special treatment for sections
                                            in the component 'main', in which case 'main/' is typically not named in a section-field.
                                            For this switch -c we have to specify 'main' to see packages from the component 'main'.""")
    args.add_argument("-r", "--regex", action="store_true", help="""
                                            Treat PACKAGE as a regex. Searches for binary package-names or
                                            binary packages that were built from a source prefixed with 'src:'.
                                            Examples:
                                            Use regex '.' to show all packages.
                                            Use regex '^pkg' to show all packages starting with 'pkg'.
                                            Use regex '^src:source' to show packages that were built from a source starting with 'source'.""")
    args.add_argument("-s", "--suite", default=None, help="""
                                            Only show info for this SUITE(s). The list of SUITEs is specified comma-separated.
                                            The default value differs for the called sub-command: 
                                            default value for 'ls' is 'default:';
                                            default value for 'list' is ':'""")
    args.add_argument("-nu", "--no-update", action="store_true", default=False, help="Skip downloading of packages list.")
    args.add_argument("-nh", "--no-header", action="store_true", default=False, help="Don't print the column header.")
    args.add_argument("-col", "--columns", type=str, required=False, default='pvSasC', help="""
                                            Specify the columns that should be printed. Default is 'pvSasC'. Possible characters are:
                                            (p)=Package, (v)=Version, (S)=Suite, (a)=Architecture, (s)=Section, (C)=SourCe.""")
    args.add_argument("-f", "--format", type=str, choices=['table', 'list'], required=False, default='table', help="""
                                            Specifies the output-format of the package list. Default is 'table'.
                                            Possible values: 'table' to pretty print a nice table; 'list' to print a
                                            space separated list of columns that can easily be processed with bash tools.""")

    args.add_argument('subcommand', nargs=1, choices=['ls', 'show', 'sourcesList', 'list'], help='The following sub-commands are available: ls. Planned for later: show, sourcesList, ...')
    args.add_argument('package', nargs='+', help='Name of a binary PACKAGE or source-package name prefixed as src:SOURCENAME')

    args = args.parse_args()

    setupLogging(logging.DEBUG if args.debug else logging.WARN)
    logger = logging.getLogger('main')

    if args.subcommand[0] == 'ls':
        listPkgs(args)
    elif args.subcommand[0] == 'list':
        listRepos(args)
    else:
        print("Provided subcommand '{}' is not yet implemented!".format(args.subcommand[0]))
        sys.exit(1)


def setupLogging(loglevel):
    '''Initializing logging and set log-level'''
    kwargs = {
        'format': '%(asctime)s %(levelname)-8s %(message)s',
        'datefmt':'%Y-%m-%d,%H:%M:%S',
        'level': loglevel,
        'stream': sys.stderr
    }
    logging.basicConfig(**kwargs)


def listRepos(args):
    '''Implementation of subcommand list'''
    suitesStr = args.suite if args.suite else ':'
    suites = getSuites(suitesStr.split(','))
    for s in sorted(suites):
        print(s.getSuiteName())


def listPkgs(args):
    '''Implementation of subcommand ls'''
    logger = logging.getLogger('listPkgs')

    suitesStr = args.suite if args.suite else 'default:'
    suites = getSuites(suitesStr.split(','))
    
    requestPackages = { p for p in args.package }

    requestArchs = { a for a in args.architecture.split(',') } if args.architecture else {}

    requestComponents = { c for c in args.component.split(',') } if args.component else {}

    requestFields = PackageField.getByFieldsString(args.col)

    result = set()
    for suite in suites:
        if not args.no_update: 
            suite.updateCache()
        result.extend(suite.queryPackages(self, requestPackages, args.regex, requestArchs, requestComponents, requestFields))

    # calculate max col_widths
    col_width = [max(len(x) for x in col) for col in zip(*result)]

    if args.format == 'table':
        if not args.no_header:
            col_width = [max(len(h), col_width[i]) for i, h in enumerate(header)]
            result = (header, ["="*w for w in col_width], result)
        for r in result:
            print (" | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(r)))

    elif args.format == 'list':
        if not args.no_header:
            result = (header, result)
        for r in result:
            print (" ".join(r))


if __name__ == "__main__":
    main()