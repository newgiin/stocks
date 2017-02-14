"""Prints US stocks analysts rated "Buy" on http://quotes.wsj.com/company-list.

usage: wsj.py SECTOR [MIN_RATINGS]
  SECTOR: A sector as listed under the sector browse page, e.g.
  "basic materials/resources". Case insensitive.

  MIN_RATINGS: Skip stocks with less than this number of ratings. 
"""
import pyquery
import sys
import urllib


def main(argv):
  min_ratings = None
  if len(argv) < 2:
    print 'usage: wsj.py SECTOR [MIN_RATINGS]'
    sys.exit(1)
  if len(argv) > 2:
    min_ratings = int(argv[2])

  page = get_dom('http://quotes.wsj.com/company-list')
  target_sector = argv[1].title()

  sectors = page('.cl-tree')[0]
  for sector in sectors:
    children = sector.getchildren()
    sector_title = children[0].text
    if sector_title == target_sector:
      for subsectors in children[1]:
        subsector_href = subsectors.getchildren()[0].attrib['href']
        for name, href, country, exchange in get_companies(subsector_href):
          analysis_url = href + '/research-ratings'
          if (country == 'United States' and
              get_consensus(analysis_url, min_ratings) == 'Buy'):
            print (name, analysis_url)
      break
  else:
    print "No sector was found matching '%s'." % target_sector


def get_dom(url):
  return pyquery.PyQuery(url=url,
                         opener=lambda url, **kw: urllib.urlopen(url).read())


def get_companies(subsector_href):
  page = get_dom(subsector_href)

  companies = page('.cl-table tbody')[0]
  # get all for current page
  for company in companies:
    children = company.getchildren()
    name = children[0].getchildren()[0].getchildren()[0].text
    href = children[0].getchildren()[0].attrib['href']
    country = children[1].text
    exchange = children[2].text
    yield (name, href, country, exchange)

  # call for next page if any
  try:
    next_btn = page('.cl-pagination .next')[0]
  except IndexError:
    pass
  else:
    if 'disabled' not in next_btn.classes:
      next_btn_href = next_btn.getchildren()[0].attrib['href']
      for result in get_companies(next_btn_href):
        yield result


def get_consensus(href, min_ratings):
  page = get_dom(href)
  try:
    consensus_table = page('.cr_analystRatings .cr_dataTable tbody')[0]
  except IndexError:  # Stock has no analysis
    return None
  num_ratings = get_total_ratings(consensus_table)
  if min_ratings is not None and num_ratings < min_ratings:
    return None
  consensus_row = consensus_table.getchildren()[5]
  curr_consensus = consensus_row.getchildren()[3]
  return curr_consensus.cssselect('.numValue-content')[0].text.strip()


def get_total_ratings(consensus_table):
  total = 0
  for i in xrange(5):
    row = consensus_table[i]
    total += int(row.getchildren()[3].cssselect('.data_data')[0].text)
  return total


main(sys.argv)
