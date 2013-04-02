import xml.etree.ElementTree as ET
from datetime import date 
from datetime import timedelta

class Ruleset:

    def __init__(self):
        """ load the xml data """
        self.tree = ET.parse('custom-ruleset-of.parametrized.xml-file.xml')
        self.list_of_coordinaterules = self.tree.findall('.//coordinaterules')

    def get_list_of_subsets(self):
        """ returns a list containing the names of all subsets """
        return self.list_of_coordinaterules
    
    def get_list_of_liturgical_days(self,subset):
        """ returns a list containing XML fragments of all liturgical days in a subset """
        pass
        
class Options:
    
    language = "en"
    form = "of"
    years = [2013,2014,2015,2016]
        
class Calendar:
    """ liturgical calendar for a series of liturgical years """
        
    def __init__(self,ruleset,options):
        self.ruleset = ruleset
        self.options = options
        self.years = {}
        for year in self.options.years:
            self.years[year] = Year(year,self)

    def populate(self):
        for year in self.years.keys():
            self.years[year].populate()

class Year:
    """ liturgical calendar for a single liturgical year """
    
    def __init__(self,year,calendar):
        self.subsets = {}
        for subset in calendar.ruleset.get_list_of_subsets():
            self.subsets[subset] = Subset(year,subset)

    def populate(self):
        for subset in self.subsets.keys():
            self.subsets[subset].populate()
            
class Subset:
    """ liturgical calendar for a subset (e.g. Advent) """
    
    def __init__(self,year,subset):
        start_date = Library.first_day_of_liturgical_year(year)
        end_date_exclusive = Library.first_day_of_liturgical_year(year + 1)
        day_count = (end_date_exclusive - start_date + timedelta(1)).days
        self.days_by_date = {}
        for i in range(0,day_count - 1):
            date = start_date + timedelta(i)
            self.days_by_date[date] = Day(date)
    
    def populate(self):
        """ get a list of all liturgical days in the ruleset and for each
            liturgical day evaluate the daterules and store the result
            in the dictionaries days_by_date and days_by_coordinates """
        pass
    
class Day:
    """ liturgical day """
    
    def __init__(self,date):
        self.date = date
    
class Library:
    
    """ contains functions for resolving daterules and coordinaterules
        and auxiliary functions """
    
    @staticmethod
    def first_day_of_liturgical_year(year):
        """" return the first Sunday of Advent as a date 
             note that if you ask the first day of 2018, the returned date will be end of 2017 !!"""
        christmas = date(year - 1, 12, 25)
        days_since_sunday = timedelta(christmas.weekday() + 1)
        sunday_before_christmas = christmas - days_since_sunday
        four_weeks = timedelta(4*7)
        first_sunday_of_advent = sunday_before_christmas - four_weeks
        return first_sunday_of_advent
    
if __name__ == '__main__':
    ruleset = Ruleset()
    options = Options()
    calendar = Calendar(ruleset,options)
    calendar.populate()
    for coordinaterules in ruleset.get_list_of_subsets():
        print(coordinaterules.attrib['set'])