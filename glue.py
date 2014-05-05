import pandas as pd
import numpy as np
import swiftnav.dgnss_management as mgmt
import swiftnav.coord_system as cs
import analysis_io
import utils
import sd_analysis

__author__ = 'imh'

# load data

# process data:
#   for datum in data:
#     note time
#     note estimated baseline
#     attempt to use real baseline to get true ambiguity, note it
#     check convergence
#     if converged, note time, and whether converged correctly


def initialize_c_code(ecef, alm, data):

    first_data_pt = data.ix[0][~ (np.isnan(data.ix[0].L1) | np.isnan(data.ix[0].C1))]
    sats = list(first_data_pt.index)
    numeric_sats = map(lambda x: int(x[1:]), sats)
    t0 = utils.datetime2gpst(data.items[0])

    mgmt.dgnss_init([alm[j] for j in numeric_sats], t0,
                    np.concatenate(([first_data_pt.L1],
                                    [first_data_pt.C1]),
                                   axis=0).T,
                    ecef, 1)

    # sats_man = mgmt.get_sats_management()
    # kf = mgmt.get_dgnss_kf()
    # stupid_state= mgmt.get_stupid_state(len(sats)-1)


def analyze(b, ecef, data_filename, data_key, almanac_filename, analysis_filename):
    data = analysis_io.load_data(data_filename, data_key)
    alm = analysis_io.load_almanac(almanac_filename)

    # ecef = utils.get_ecef(data)  # TODO decide how we want to get this one

    point_analyses = {}
    aggregate_analysis = sd_analysis.Aggregator(ecef, b, data, alm)

    initialize_c_code(ecef, alm, data)

    for i, time in enumerate(data.items[1:]):
        point_analyses[time] = sd_analysis.analyze_datum(data.ix[time], i, time, aggregate_analysis)  #NOTE: this changes aggregate_analysis
    point_analyses = pd.DataFrame(point_analyses).T

    analysis_io.save_analysis(point_analyses, aggregate_analysis, analysis_filename)


if __name__ == "__main__":
    # b = np.array([-1.4861289,   0.84761746, -0.01029364])
    # b = np.array([ 0.22566864, -1.22651958, -1.1712659 ])
    b = np.array([15, 0, 0])
    llh = np.array([np.deg2rad(37.7798), np.deg2rad(-122.3923), 40])
    ecef = cs.wgsllh2ecef(*llh)
    data_filename = "/home/imh/software/swift/projects/integer-ambiguity/fake.hd5"
    data_key = 'sd'
    almanac_filename = "/home/imh/software/swift/projects/integer-ambiguity/001.ALM"
    analysis_filename = "home/imh/software/swift/analyses/fake.hd5"

    analyze(b, ecef, data_filename, data_key, almanac_filename, analysis_filename)