
## NWSS_reporter

### What is NWSS_reporter?

NWSS_reporter is a Python script that takes the U.S. Centers for Disease Control's SARS-CoV2's wastewater metric data and a date range and reports which surveillance sites have been updated in that time period.

### Using NWSS_reporter

This command line:

```python3 NWSS_reporter.py NWSS_Public_SARS-CoV-2_Wastewater_Metric_Data_20231022.csv 2023-10-01:2023-10-02```

will produce output like this:

```input file name: NWSS_Public_SARS-CoV-2_Wastewater_Metric_Data_20231022.csv
filter dates begin: 2023-10-01 end: 2023-10-02

1032 sites updated
== key_plot_ids = CDC_BIOBOT_in_1162_Treatment plant_raw wastewater, CDC_BIOBOT_in_1162_Treatment plant_post grit removal, NWSS_in_2357_Treatment plant_raw wastewater
reporting jurisdiction: Indiana county_names: Hamilton
== key_plot_ids = NWSS_il_675_Before treatment plant_21_raw wastewater
reporting jurisdiction: Chicago county_names: Cook
== key_plot_ids = NWSS_mi_1086_Treatment plant_raw wastewater
reporting jurisdiction: Michigan county_names: Ottawa
== key_plot_ids = NWSS_mi_1136_Treatment plant_post grit removal
reporting jurisdiction: Michigan county_names: Clare
== key_plot_ids = NWSS_mn_1048_Treatment plant_raw wastewater
reporting jurisdiction: Minnesota county_names: Lyon
== key_plot_ids = NWSS_nc_2033_Treatment plant_raw wastewater
[....]
528 sites not updated
== key_plot_ids = CDC_BIOBOT_ar_1548_Treatment plant_raw wastewater
reporting jurisdiction: Arkansas county_names: Jefferson
== key_plot_ids = NWSS_mi_1087_Treatment plant_raw wastewater
reporting jurisdiction: Michigan county_names: Genesee
== key_plot_ids = NWSS_oh_395_Treatment plant_raw wastewater
reporting jurisdiction: Ohio county_names: Hamilton
[....]
```

In this example, NWSS_reporter consumed NWSS_Public_SARS-CoV-2_Wastewater_Metric_Data_20231022.csv and looked at all the rows for the 15-day sample intervals that (a) ended on October 1, 2023 or later and (b) before October 2, 2023 and calculated how many sites had at least some valid sample data and how many did not have valid sample data in this data file.

#### More about the sample data input file

In the CDC's dataset, each row has a wwtp_id (The CDC's unique identifier for wastewater treatment plants); a reporting_jurisdiction (generally a U.S. State); a key_plot_id (a unique string identifier for the geographic area served by the treatment plant; county_names; population_served (an estimate of the number of people served by this treatment plant); date_start (the start date for the reported sample interval); date_end (the end date for the reported sample interval, which is 15 days after the start_date); pct_15d (the percentage change in SARS-CoV 2 levels from the start date to the end date); and percentile (how the current SARS-CoV 2 levels compare the site's historical numbers, expressed as a percent scaled from 0 to 100).

This dataset has a row for each monitored site, regardless if it has reported sample data for a given date or not. It doesn't have a "not updated" flag, so if
NWSS_reporter finds an empty pct_15d field, an empty percentile field, or a percentile field value of 999.9, it treats that row as not updated.

You can download the current dataset at https://data.cdc.gov/Public-Health-Surveillance/NWSS-Public-SARS-CoV-2-Wastewater-Metric-Data/2ew6-ywp6; look for the export button on the upper right hand side of the page. Column defintions are documented on this page too. The graphical interface to the data is at: https://covid.cdc.gov/covid-data-tracker/#wastewater-surveillance.

#### The filter ranges

The filter ranges tailor the search for rows with a sample interval end date at or after the first date and also before the second date. The format for this parameter is YYYY-MM-DD:YYYY-MM-DD.

#### The output

NWSS_report's output lists the input file name, the filter begin and end dates, the number of sites that were updated at some point in the filter date range, plus information about each site in that set, and the number of sites that weren't updated at some point in the filter date range, plus information about each site in that set.

Adding a --jurisdiction argument matches on sites within the given reporting_jurisdiction column only:

```python3 NWSS_reporter.py --jurisdiction Washington NWSS_Public_SARS-CoV-2_Wastewater_Metric_Data_20231022.csv 2023-10-01:2023-10-02```

Adding a --wwpt_id argument matched on a site with a given wwtp_id only:

```python3 NWSS_reporter.py --wwtp_id 1398 NWSS_Public_SARS-CoV-2_Wastewater_Metric_Data_20231022.csv 2023-10-01:2023-10-02```

Adding the --totals_only argument leaves out individual site information, and adding the --verbose argument prints every matched row for every site.

### About sites with multiple identifiers

In this dataset, you will come across sites that have been listed under multiple identifiers at different times. A good example of this is wwtp_ids 2419 and 1139, with associated key plot ids "NWSS_wa_2419_Treatment plant_post grit removal" and "CDC_BIOBOT_wa_1139_Treatment plant_post grit removal". They both seem to refer to the King County South Treatment Plant in Washington State. As the CDC has transitioned away from Biobot to Verily as a sample data provider for some of its sites, it has created a completely new wwtp_id to track it. This is confusing, because the CDC doesn't use a unifying identifier. NWSS_reporter works around this by assuming all sites in the same state and the same counties and with the same population_served numbers are the same site.

### Picking good filter dates

Remember, NWSS_reporter only reports updates/not updates based on the input file, which is a snapshot on a given day. You could download a csv data file using filter dates of the previous week and find that a given site was not being updated. Then the reporting could come in for that site the next day, and if you ran the tool again with that next day's snapshot but the same filter dates as before, you'd find the site is being updated.

This is a plea for using filter dates that give the dataset a chance to get updated before you draw strong conclusions about whether a given site is being updated or not. So if I'm looking at a snapshot from October 22nd, I'm going to use a filter date range of 2023-10-01:2023-10-08. That gives the dataset a weeks' worth of data to look at (in case the site does its sampling once a week) and two weeks for the sample data to make it into the database.

### Requirements

Any reasonably modern version of Python3 should work.
