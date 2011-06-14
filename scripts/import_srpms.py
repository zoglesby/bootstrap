#!/usr/bin/python

import os
import sys
import time
import shutil
import argparse
import subprocess

# import our basic settings
from goose_settings import *

# import the rpm parsing stuff
import rpm

# import github creation 
from create_gh_repo import *

# import git repo creation
from create_git_repo import *

def import_srpms(args):

    # rpm.ts is an alias for rpm.TransactionSet
    ts = rpm.ts()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)

    path = args.path
    srpms = os.listdir(path)

    for srpm in srpms:
        print "SRPM: %s" % srpm
        fdno = os.open(u"%s/%s" % (path, srpm), os.O_RDONLY)
        try:
            hdr = ts.hdrFromFdno(fdno)
        except rpm.error, e:
            if str(e) == "public key not available":
                print str(e)
        os.close(fdno)
    
        name = hdr[rpm.RPMTAG_NAME]
        version = hdr[rpm.RPMTAG_VERSION]
        release = hdr[rpm.RPMTAG_RELEASE]
        sources = hdr[rpm.RPMTAG_SOURCE]
        # print sources
        patches = hdr[rpm.RPMTAG_PATCH]
        # print patches

        if not os.path.isdir(u"%s/%s" % (install_root, name)):
            os.makedirs(u"%s/%s" % (install_root, name), 0775)

        args = ["/bin/rpm", "-i", "--root=%s/%s" % (install_root, name), "%s/%s" % (path, srpm)]
        p = subprocess.Popen(args)

        time.sleep(2)

        path_to_sources = u"%s/%s%s/%s" % (install_root, name, home, 'rpmbuild/SOURCES')
        dest_to_sources = u"%s/%s" % (lookaside_dir, name)

        path_to_spec = u"%s/%s%s/%s/%s.spec" % (install_root, name, home, 'rpmbuild/SPECS', name)
        dest_to_spec = u"%s/%s" % (git_dir, name)

#        print "\npath_to_sources %s" % path_to_sources
#        print "path_to_spec %s" % path_to_spec
#        print "\n"
#        print "lookaside_dir %s" % lookaside_dir
#        print "dest_to_sources %s" % dest_to_sources
#        print "dest_to_spec %s" % dest_to_spec
#        print "\n"

        if not os.path.isdir(u"%s" % (dest_to_sources)):
            os.makedirs(u"%s" % (dest_to_sources), 0775)

        if not os.path.isdir(u"%s" % (dest_to_spec)):
            os.makedirs(u"%s" % (dest_to_spec), 0775)

        # create the github repo

        create_gh_repo(name, github_org)

        # initialize dest_to_sources as a git repo
        # before copying the data over

        create_git_repo(dest_to_spec, u"%s/%s.git" %(github_base, name))

        # copy the spec file
        shutil.copy2(path_to_spec, dest_to_spec)

        # copy the source files
        for source in sources:
            shutil.copy2("%s/%s" % (path_to_sources, source), dest_to_sources)

        # copy the patch files
        for patch in patches:
            shutil.copy2("%s/%s" % (path_to_sources, patch), dest_to_spec)


def main():
    p = argparse.ArgumentParser(
            description='''Imports all src.rpms into git and lookaside cache''',
        )

    p.add_argument('path', help='path to src.rpms')
    p.set_defaults(func=import_srpms)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    sys.exit(main())