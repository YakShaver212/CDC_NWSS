import argparse
import csv
import datetime
import sys

from pdb import set_trace as bp

# these are the fields we expect to see in the input CDC NWSS file.
# input csv file and field definitions from here: 
# https://data.cdc.gov/Public-Health-Surveillance/NWSS-Public-SARS-CoV-2-Wastewater-Metric-Data/2ew6-ywp6
#
# 'wwtp_jurisdiction','wwtp_id','reporting_jurisdiction','sample_location','sample_location_specify', \
# 'key_plot_id','county_names','county_fips','population_served','date_start','date_end','ptc_15d',      \
# 'detect_prop_15d','percentile','sampling_prior','first_sample_date'

def handle_args():
    '''sets up the argument parser and returns a parsed argument object.'''

    def daterangeconv(daterangestr):
        '''helper function to turn date range string into a dictionary of datetime.date objects.'''
        [beginstr, endstr] = daterangestr.split(':')
        if endstr < beginstr:
           raise ValueError("ERROR: filter begin must be before filter end")
        return { 'begin': datetime.datetime.strptime(beginstr,"%Y-%m-%d").date(), \
                 'end': datetime.datetime.strptime(endstr,"%Y-%m-%d").date() }

    argparser = argparse.ArgumentParser(description="A tool to analyze CDC NWSS data files")
    # required positional parameters
    argparser.add_argument("cdc_nwss_csv_fname", type=str, help="filename of the CDC NWSS data file to analyze")
    argparser.add_argument("filter_dates", type=daterangeconv, help="look at rows with a sample end date within this range. Format: YYYY-MM-DD:YYYY-MM-DD")
    # optional parameters
    argparser.add_argument("--jurisdiction", help="filter by a specific recording jurisdiction. E.g. \"--jurisdiction Washington\"")
    argparser.add_argument("--wwtp_id", help="filter by a specific wwtp_id. E.g. \"--wwtp_id 1398\"")
    argparser.add_argument("--totals_only", action="store_true", help="output totals only")
    argparser.add_argument("--verbose", action="store_true", help="output matched rows for each site")

    myargs = argparser.parse_args()
    return myargs

def is_sample_data_invalid(r):
    '''tests to see if the row object contains actual data in its ptc_15d or percentile fields.'''
    return r['ptc_15d'] == '' or r['percentile'] == '' or r['percentile'] == '999.0'

def get_row_key(r):
    '''the CDC dataset sometimes changes the wwtp_id and/or key_plot_ids for a given sample site or service area.
    I need a single unique identifer for a site that spans the various id changes. Theory: the jurisdiction,
    county names, and population served numbers don't change and can be our unique identifier ("row key")'''
    return r['reporting_jurisdiction'] + ":" + r['county_names'] + ":" + r['population_served']

def get_ids( rowlist ):
    '''from a list of rows, compile a list of all the unique key_plot_ids in those rows and return as a single string.'''
    ids = [r['key_plot_id'] for r in rowlist ]
    return set(ids)

def is_row_in_filter_date_range(r,filter_begin,filter_end):
    '''is the row's sample end date within our filter range? filter's begin is inclusive, filter's end is exclusive'''
    row_sample_end  = datetime.datetime.strptime(r['date_end'], "%Y-%m-%d").date()
    return filter_begin <= row_sample_end and filter_end > row_sample_end

def format_site_data( site_rows, detailed_row_data = False ):
    '''print out detailed site data.'''
    id_array = get_ids(site_rows)
    print("== key_plot_ids = {}".format(', '.join(id_array)))
    print("reporting jurisdiction: {} county_names: {}".format( site_rows[0]['reporting_jurisdiction'], site_rows[0]['county_names']))

    if detailed_row_data:
       sorted_site_rows = sorted(site_rows, key=lambda x: x['date_end'])
       print("first filtered sample period: {} - {}".format(sorted_site_rows[0]['date_start'], sorted_site_rows[0]['date_end']))
       print("last filtered sample period: {} - {}".format(sorted_site_rows[-1]['date_start'], sorted_site_rows[-1]['date_end']))

       rows_with_valid_data = [r['got_valid_data'] for r in sorted_site_rows].count(True)
       rows_with_invalid_data = [r['got_valid_data'] for r in sorted_site_rows].count(False)
       print("{} filtered rows found. {} rows had valid data and {} rows had invalid data".format(len(sorted_site_rows), rows_with_valid_data,rows_with_invalid_data))

       for r in sorted_site_rows:
          print("\t{}".format(r))

if __name__ == "__main__":

    myargs = handle_args()

    print("input file name: {}".format(myargs.cdc_nwss_csv_fname))
    print("filter dates begin: {} end: {}".format(str(myargs.filter_dates['begin']),str(myargs.filter_dates['end'])))

    matched_rows = {} # key is row key, value is a list of rows for the key that match on our dates
    with open(myargs.cdc_nwss_csv_fname) as f:
        # turn every csv row into a dictionary
        for r in csv.DictReader(f):

            # if jurisdiction argument used, look only a rows from that jurisdiction
            if myargs.jurisdiction and myargs.jurisdiction != "":
                if r['reporting_jurisdiction'] not in myargs.jurisdiction:
                    continue

            # if wwtp_id argument used, look only a rows from that wwtp_id
            if myargs.wwtp_id and myargs.wwtp_id != "":
                if r['wwtp_id'] !=  myargs.wwtp_id:
                    continue

            # is this row in the filter date range we care about?
            if is_row_in_filter_date_range(r,myargs.filter_dates['begin'],myargs.filter_dates['end']):

                # yes, in range. does the row have valid data in it?
                r['got_valid_data'] = True
                if is_sample_data_invalid(r):
                    r['got_valid_data'] = False

                # get this row's unique site identifer and add the row to the matched_rows dictionary
                row_key = get_row_key(r)
                if row_key in matched_rows.keys():
                    matched_rows[row_key].append( r )
                else:
                    matched_rows[row_key] = [ r ]

    # if no matched rows, complain and quit
    if len(matched_rows) == 0:
       print("no matched rows!")
       sys.exit(1)

    # sort sites into ones that have at least one row of valid data and those that have no valid data
    sites = { 'updated': [], 'not_updated': [] }
    gvd_list = []
    for row_key in matched_rows.keys():
        gvd_list = [r['got_valid_data'] for r in matched_rows[row_key]]
        if any(gvd_list): 
            # got at least one row with valid data for this site
            sites['updated'].append( row_key )
        else:
            # nope, no valid data in any of the rows for this site
            sites['not_updated'].append( row_key )

    # report on the updated/not_updated results
    print("\n{} sites updated".format( len(sites['updated'])))
    if not myargs.totals_only:
       for row_key in sites['updated']:
          format_site_data( matched_rows[row_key], myargs.verbose )

    print("\n{} sites not updated".format( len(sites['not_updated'])))
    if not myargs.totals_only:
       for row_key in sites['not_updated']:
          format_site_data( matched_rows[row_key], myargs.verbose )

