#!/usr/bin/env python
# encoding: utf-8
'''
@author:     user_name

@copyright:  2019 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os
import logging
import traceback  # , datetime

from optparse import OptionParser
from lib.moenm import MoENM

__all__ = []
__version__ = 0.1
__date__ = '2019-02-26'
__updated__ = '2019-02-26'

DEBUG = 0
TESTRUN = 0
PROFILE = 0


def extract_value(output, val):
    return map(lambda x: x[len(val)+3:], filter(lambda x: x.startswith(val), output))


def tee(c, s):
    logging.info("^%s^" % c)
    print c
    print "\n".join(s)
    return s


def pack_output(output):
    return {lst[0]:lst[1] for lst in map(lambda s: s.split(" : "), filter(lambda x: x.find(":") != -1, output))}


def main(argv=None):
    '''Command line options.'''

    program_name = os.path.basename(sys.argv[0])
    program_version = "v0.1"
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    #program_usage = '''usage: spam two eggs''' # optional - will be autogenerated by optparse
    program_longdesc = '''''' # optional - give further explanation about what the program does
    program_license = "Copyright 2019 user_name (organization_name)                                            \
                Licensed under the Apache License 2.0\nhttp://www.apache.org/licenses/LICENSE-2.0"

    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version=program_version_string, epilog=program_longdesc, description=program_license)
        parser.add_option("-i", "--in", dest="infile", help="set input path for data file [default: %default]", metavar="FILE")
        parser.add_option("-o", "--out", dest="outfile", help="set output path for log file [default: %default]", metavar="FILE")
        parser.add_option("-s", "--suffix", dest="suffix", help="set configs name suffix [default: %default]", metavar="SFX")
        parser.add_option("-c", "--configs", dest="configs", help="read elements for copy to configs [default: %default]", metavar="SFX", default=False, action="store_false")
        parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]")

        # set defaults
        parser.set_defaults(outfile="./gsm_ren_enm.log", infile="./data.csv", suffix="gsm_rename_1704")

        # process options
        (opts, args) = parser.parse_args(argv)  # @UnusedVariable

        logging.basicConfig(format='%(levelname)-8s [%(asctime)s] %(message)s', level=logging.INFO, filename=opts.outfile)
        if opts.verbose > 0:
            print("verbosity level = %d" % opts.verbose)
        if opts.infile:
            print("infile = %s" % opts.infile)
        if opts.outfile:
            print("outfile = %s" % opts.outfile)
        if opts.suffix:
            print("suffix = %s" % opts.suffix)
        if opts.configs:
            print("configs = %s" % opts.configs)

        # MAIN BODY #
        dt = opts.suffix  # datetime.datetime.now().strftime('%m%d%I%M%S')
        plans3G = ["%02d_%s_%s" % (i, s, dt) for i, s in enumerate(["3G_create_ext", "3G_create_rel", "3G_delete_rel", "3G_delete_ext"])]
        plans4G = ["%02d_%s_%s" % (i, s, dt) for i, s in enumerate(["4G_create_ext", "4G_create_rel", "4G_delete_rel", "4G_delete_ext"])]
        nodes3G = set()
        nodes4G = set()
        coll_3G = "coll_3G_%s" % dt
        coll_4G = "coll_4G_%s" % dt

        with MoENM("", "", "") as moe, open(opts.infile, "r") as datafile:
            if opts.configs:
                for line in datafile:
                    lac, ci, newname = line.strip().split(",")
                #   ^--- csv file format ---^

                    # 3G
                    for fdn in extract_value(tee(" ======= 3G STARTED: ======= ", \
                                                 moe.get("* ExternalGsmCell.(cellIdentity==%s,lac==%s)" % (ci, lac), None)), "FDN"):
                        nodes3G.add(fdn.split(",")[2].split("=")[1])
                    # 4G
                    for fdn in extract_value(tee(" ======= 4G STARTED: ======= ", \
                                                 moe.get("* ExternalGeranCell.(cellIdentity==%s,lac==%s)" % (ci, lac), None)), "FDN"):
                        nodes4G.add(fdn.split(",")[2].split("=")[1])
                with open("%s.txt" % coll_3G, "wb") as f:
                    f.write("\n".join(nodes3G))
                with open("%s.txt" % coll_4G, "wb") as f:
                    f.write("\n".join(nodes4G))
                print 'collection create "{0}" -f file:"{0}.txt"'.format(coll_3G)
                print 'collection create "{0}" -f file:"{0}.txt"'.format(coll_4G)
                for cfg in plans3G:
                    print "config create %s" % cfg
                    print "config copy --collection %s --source Live --target %s" % (coll_3G, cfg)
                for cfg in plans4G:
                    print "config create %s" % cfg
                    print "config copy --collection %s --source Live --target %s" % (coll_4G, cfg)

            else:
                for line in datafile:
                    lac, ci, newname = line.strip().split(",")
                #   ^--- csv file format ---^
                    # 3G
                    for fdn in extract_value(tee(" ======= 3G STARTED: ======= ", \
                                                 moe.get("* ExternalGsmCell.(cellIdentity==%s,lac==%s)" % (ci, lac), None)), "FDN"):
                        ExternalGsmCell_data = pack_output(tee(" ======= Previous values request: ======= ", \
                            moe.get(fdn, "")))
                        ExternalGsmCellFDN_old = ExternalGsmCell_data.pop("FDN")
                        ExternalGsmCellFDN_new = ",".join(ExternalGsmCellFDN_old.split(",")[:-1]+["ExternalGsmCell=%s" % newname])
                        ExternalGsmCell_data["cellIdentity"] = ci[:-1] + newname[-1]
                        ExternalGsmCell_data["userLabel"]='"%s"' % newname
                        ExternalGsmCell_data["ExternalGsmCellId"]='"%s"' % newname
                        ExternalGsmCell_data["bandIndicator"]='"%s"' % ExternalGsmCell_data["bandIndicator"]
                        reservedBy = ExternalGsmCell_data.pop("reservedBy")
                        tee(" ======= Create ExternalGsmCell: ======= ", \
                            moe.create(ExternalGsmCellFDN_new, "--config=%s" % plans3G[0], **ExternalGsmCell_data))
                        tee(" ======= Delete ExternalGsmCell: ======= ", \
                            moe.delete(ExternalGsmCellFDN_old, "--config=%s" % plans3G[3]))
                        for rel in filter(lambda s: s.find("GsmRelation") != -1, reservedBy[1:-1].split(", ")):
                            GsmRelation_data = pack_output(tee(" ======= Previous values request: ======= ", \
                            moe.get(rel, "")))
                            GsmRelationFDN_new = ",".join(rel.split(",")[:-1]+["GsmRelation=%s" % newname])
                            GsmRelation_data["mobilityRelationType"]='"%s"' % GsmRelation_data["mobilityRelationType"]
                            GsmRelation_data["GsmRelationId"]='"%s"' % newname
                            GsmRelation_data["externalGsmCellRef"]='"%s"' % ExternalGsmCellFDN_new
                            GsmRelation_data.pop("FDN")
                            tee(" ======= Create GsmRelation: ======= ", \
                                moe.create(GsmRelationFDN_new, "--config=%s" % plans3G[1], **GsmRelation_data))
                            tee(" ======= Delete GsmRelation: ======= ", \
                                moe.delete(rel, "--config=%s" % plans3G[2]))
                        for drt in filter(lambda s: s.find("GsmRelation") == -1, reservedBy[1:-1].split(", ")):
                            tee(" ======= Set directedRetryTarget: ======= ", \
                                moe.set(drt, "--config=%s" % plans3G[1], directedRetryTarget='"%s"' % ExternalGsmCellFDN_new))

                    # 4G
                    for fdn in extract_value(tee(" ======= 4G STARTED: ======= ", \
                                                 moe.get("* ExternalGeranCell.(cellIdentity==%s,lac==%s)" % (ci, lac), None)), "FDN"):
                        ExternalGeranCell_data = pack_output(tee(" ======= Previous values request: ======= ", \
                            moe.get(fdn, "")))
                        for par in ["lastModification", "timeOfCreation", "timeOfLastModification", "rimAssociationStatus"] + ["zzzTemporary%d" % x for x in range(1,6) + range(8,13)]:
                            ExternalGeranCell_data.pop(par)
                        for par in ["dtmSupport", "geranFrequencyRef", "isRemoveAllowed", "rimCapable"]:
                            ExternalGeranCell_data[par] = '"%s"' % ExternalGeranCell_data.pop(par)
                        for par in ["externalGeranCellId", "ExternalGeranCellId", "masterGeranCellId", "userLabel"]:
                            if par in ExternalGeranCell_data.keys():
                                ExternalGeranCell_data[par] = '"%s"' % newname
                        ExternalGeranCellFDN_old = ExternalGeranCell_data.pop("FDN")
                        ExternalGeranCellFDN_new = ",".join(ExternalGeranCellFDN_old.split(",")[:-1]+["ExternalGeranCell=%s" % newname])
                        ExternalGeranCell_data["cellIdentity"] = ci[:-1] + newname[-1]
                        reservedBy = ExternalGeranCell_data.pop("reservedBy")
                        tee(" ======= Create ExternalGeranCell: ======= ", \
                            moe.create(ExternalGeranCellFDN_new, "--config=%s" % plans4G[0], **ExternalGeranCell_data))
                        tee(" ======= Delete ExternalGeranCell: ======= ", \
                            moe.delete(ExternalGeranCellFDN_old, "--config=%s" % plans4G[3]))
                        for rel in reservedBy[1:-1].split(", "):
                            GeranCellRelation_data = pack_output(tee(" ======= Previous values request: ======= ", \
                                                                     moe.get(rel, "")))
                            GeranCellRelationFDN_new = ",".join(rel.split(",")[:-1]+["GeranCellRelation=%s" % newname])
                            for par in ["lastModification", "timeOfCreation", "timeOfLastModification", "createdBy", "mobilityStatus"]:
                                GeranCellRelation_data.pop(par)
                            for par in ["coverageIndicator", "isHoAllowed", "isRemoveAllowed"]:
                                GeranCellRelation_data[par] = '"%s"' % GeranCellRelation_data.pop(par)
                            GeranCellRelationFDN_old = GeranCellRelation_data.pop("FDN")
                            GeranCellRelationFDN_new = ",".join(GeranCellRelationFDN_old.split(",")[:-1]+["GeranCellRelation=%s" % newname])
                            GeranCellRelation_data["extGeranCellRef"] = '"%s"' % ExternalGeranCellFDN_new
                            for par in ["geranCellRelationId", "GeranCellRelationId"]:
                                if par in GeranCellRelation_data.keys():
                                    GeranCellRelation_data[par] = '"%s"' % newname
                            tee(" ======= Create GeranCellRelation: ======= ", \
                                moe.create(GeranCellRelationFDN_new, "--config=%s" % plans4G[1], **GeranCellRelation_data))
                            tee(" ======= Delete GeranCellRelation: ======= ", \
                                moe.delete(rel, "--config=%s" % plans4G[2]))

    except Exception, e:
        logging.critical(traceback.format_exc())
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'moenm.moenm.gfp_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())