import csv
import simplejson as json
import os
from typing import Any, Dict, List
import datetime as dt
import click
import hearing
import fetch_page
import persist


def get_days_between_dates(afterdate, beforedate):
    "return a list of individual days between two dates"

    #convert to datetime objects
    beforedate = dt.datetime.strptime(beforedate, '%m-%d-%Y')
    afterdate = dt.datetime.strptime(afterdate, '%m-%d-%Y')

    #get days between as int
    n_days = (beforedate - afterdate).days

    #return each individual day, including the last one
    return [(afterdate + dt.timedelta(days=i)).strftime('%m/%d/%Y') for i in range(n_days + 1)]

def make_setting_list(days_to_pull: List[str]) -> List[Dict[str, Any]]:
    #pull all settings, one day at a time
    pulled_settings = []
    for setting_day in days_to_pull:
        day_settings = hearing.fetch_settings(afterdate=setting_day, beforedate=setting_day)
        pulled_settings.extend(day_settings)
    return pulled_settings



@click.command()
@click.argument(
    "afterdate", nargs=1
)
@click.argument("beforedate", nargs=1)

@click.argument("outfile", type=click.File(mode="w"), default="result.json")
@click.option('--showbrowser / --headless', default=False, help='whether to operate in headless mode or not')

def parse_settings(afterdate, beforedate, outfile, showbrowser=False):
    # If showbrowser is True, use the default selenium driver
    if showbrowser: 
        from selenium import webdriver
        fetch_page.driver = webdriver.Firefox()

    days_to_pull = get_days_between_dates(afterdate=afterdate, beforedate=beforedate)
    pulled_settings = make_setting_list(days_to_pull)
    for setting in pulled_settings:
        persist.rest_setting(setting)
    json.dump(pulled_settings, outfile)


if __name__ == "__main__":
    parse_settings()
