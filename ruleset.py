import xml.etree.ElementTree as ET
from datetime import date 
from datetime import timedelta

class Ruleset:

    def __init__(self): # TODO parametrize to accept filename
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
        """ populate the complete calendar """
        for year in self.options.years:
            self.populate_year(year)
            
    def populate_year(self,year):
        """ populate all liturgical days for all subsets for a single year """
        evaluate_daterules = Evaluate_daterules(year)
        for coordinates in self.liturgical_days.keys():
            date = evaluate_daterules(self.liturgical_days[coordinates].daterules)
            self.link(self.liturgical_days[coordinates], self.days[date])

    def link(self,liturgical_day,day):
        """ create a mutual link between a liturgical_day and a day """
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

class Evaluate_daterules:
    """ evaluation toolset to evaluate daterules in the context of a specific year """
    
    def __init__(self,year):
        self.year = year

    def evaluate_daterules(self,daterules):
        """ reads the element name and runs the according method """
        action = daterules.tag
        return self.rules[action](daterules)

    def date(self,daterules):
        day = daterules.get('day')
        month = daterules.get('month')
        previous_year = daterules.get('year-1')
        year = self.year if previous_year != 'true' else self.year - 1
        return date(year,month,day)
        
    def weekday_before(self,daterules):
        inputrules = daterules.find('*')
        date = self.evaluate_daterules(inputrules)
        day = daterules.get('day')
        # get the weekday index [0-6] of the date (r) and of the day (n)
        # e.g. r is a Wednesday (3) and n is a Monday (1), so 2 days must be counted backwards
        # e.g. r is a Wednesday (3) and n is a Saturday (6), so 4 days must be counted backwards
        # e.g. r and n are both Mondays (1), so 7 days mus be counted backwards 
        # in a simple formula, this is: (r-n-1) % 7 + 1
        r = date.weekday()
        count = (r - n - 1) % 7 + 1
        # inputrules = daterules.find('*')
        # inputdate = Library.evaluate_daterules(inputrules)
        # day = daterules.get('day')
        # calculate the output date and return

    @staticmethod
    def weekday():
        pass

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