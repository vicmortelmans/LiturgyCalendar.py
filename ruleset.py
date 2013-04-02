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
        """ returns a list containing all liturgical days in a subset """
        return self.tree.findall('.//liturgicalday[' + subset + ']')

    def get_liturgical_days_as_dictionary(self):
        """ returns a dictionary containing all liturgical days by coordinates """
        dictionary = {}
        for liturgical_day in self.tree.findall('.//liturgicalday'):
            coordinates = liturgical_day.findtext('coordinates')
            subset = liturgical_day.findtext('set')
            liturgical_day_obj = Liturgical_day(coordinates,subset)
            liturgical_day_obj.attributes = {
                'name' : liturgical_day.findtext('name'),
                'season' : liturgical_day.findtext('season'),
                'rankname' : liturgical_day.findtext('rank'),
                'rankvalue' : liturgical_day.find('rank').get('nr'),
                'vigil' : liturgical_day.findtext('vigil'),
                'precedence' : liturgical_day.findtext('precedence'),
                'color' : liturgical_day.findtext('color')
            }
            liturgical_day_obj.daterules = liturgical_day.find('daterules')
            # add to dictionary
            dictionary[coordinates] = liturgical_day_obj
        return dictionary
        
class Options:
    
    language = "en"
    years = [2013,2014,2015,2016]
        
class Calendar:
    """ use a ruleset to compose the liturgical calendar for a series of liturgical years """
        
    def __init__(self,ruleset,options):
        self.ruleset = ruleset
        self.options = options
        self.liturgical_days = self.ruleset.get_liturgical_days_as_dictionary()
        for coordinates in self.liturgical_days.keys():
            self.liturgical_days[coordinates].set_calendar(self)
        self.days = {}
        for year in self.options.years:
            for date in Library.all_days_of_liturgical_year(year):
                self.days[date] = Day(date,year)
                self.days[date].set_calendar(self)
                
    def populate(self):
        for year in self.options.years:
            self.populate_year(year)
            
    def populate_year(self,year):
        for coordinates in self.liturgical_days.keys():
            self.liturgical_days[coordinates].evaluate(year)

    def link(self,liturgical_day,day):
        coordinates = liturgical_day.coordinates
        subset = liturgical_day.subset
        date = day.date
        year = day.year
        self.liturgical_days[coordinates].days[year] = self.days[date]
        self.days[date].liturgical_days[subset] = self.liturgical_days[coordinates]

class Liturgical_day:
    
    def __init__(self,coordinates,subset):
        self.calendar = None
        self.coordinates = ''
        self.subset = ''
        self.attributes = {}
        self.daterules = None
        self.days = {} # references to days by year

    def set_calendar(self,calendar):
        self.calendar = calendar

    def evaluate(year):
        # date = evaluate daterules for this year
        # self.calendar.link(self,self.calendar.days[date])
        
class Day:
    
    def __init__(self,date,year):
        self.calendar = None
        self.date = date
        self.year = year
        self.liturgical_days = {} # references to liturgical days by subset
    
    def set_calendar(self,calendar):
        self.calendar = calendar

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

    @staticmethod
    def all_days_of_liturgical_year(year):
        """ returns a list of all days as a date """
        start = Library.first_day_of_liturgical_year(year)
        end = Library.first_day_of_liturgical_year(year + 1)
        count = (end - start).days
        return [start + timedelta(days = x) for x in range(0,count)]

    @staticmethod
    def evaluate_daterules(daterules):
        # TODO action = daterules.tagname()
        # TODO return Library.rules[action](daterules)

    @staticmethod
    def date(daterules):
        # day = daterules.get('day')
        # month = daterules.get('month')
        # year = daterules.get('year')
        # return Date(day,month,year)
        
    @staticmethod
    def weekday_before(daterules):
        # inputrules = daterules.find('*')
        # inputdate = Library.evaluate_daterules(inputrules)
        # day = daterules.get('day')
        # calculate the output date and return

    rules = {
        "date" : Library.date,
        "weekday-before" : Library.weekday_before
    }

if __name__ == '__main__':
    ruleset = Ruleset()
    options = Options()
    calendar = Calendar(ruleset,options)
    calendar.populate()
    for coordinaterules in ruleset.get_list_of_subsets():
        print(coordinaterules.attrib['set'])