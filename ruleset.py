import xml.etree.ElementTree as ET
from datetime import date 
from datetime import timedelta

class Ruleset:

    def __init__(self): # TODO parametrize to accept filename
        """ load the xml data """
        self.tree = ET.parse('custom-ruleset-of.xml')
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
                'rankvalue' : int(liturgical_day.find('rank').get('nr')),
                'vigil' : liturgical_day.findtext('vigil'),
                'precedence' : int(liturgical_day.findtext('precedence')),
                'color' : liturgical_day.findtext('color')
            }
            liturgical_day_obj.daterules = liturgical_day.find('daterules')
            # add to dictionary
            dictionary[coordinates] = liturgical_day_obj
        return dictionary
        
    def get_coordinates_by_name(self,name):
        return self.tree.findtext('.//liturgicalday[name="' + name + '"]/coordinates')
        
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
        daterules_evaluator = Evaluate_daterules(self,year)
        for coordinates in self.liturgical_days.keys():
            self.evaluate_daterules(daterules_evaluator,coordinates)

    def evaluate_daterules(self,daterules_evaluator,coordinates):
        """ entry point for resolving the date for a liturgical day and
            storing the result in the liturgical_days and days dictionaries.
            the logic is not here, because the call is forwarded to a Daterules_evaluator,
            but this method takes care that
            - if the date has already been resolved, the daterules aren't evaluated again
            - no circular calls are made """
        liturgical_day = self.liturgical_days[coordinates]
        if liturgical_day.state == "evaluating":
            raise NameError("Circular call of evaluate_daterules")
        elif liturgical_day.state == "evaluated":
            return liturgical_day.days[daterules_evaluator.year].date
        else:
            liturgical_day.state = "evaluating"
            date = daterules_evaluator.evaluate_daterules(liturgical_day.daterules)
            liturgical_day.state = "evaluated"
            self.link(liturgical_day, self.days[date])
            return date

    def evaluate_daterules_by_name(self,daterules_evaluator,name):
        coordinates = self.ruleset.get_coordinates_by_name(name)
        return self.evaluate_daterules(daterules_evaluator, coordinates)

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
        self.coordinates = coordinates
        self.subset = subset
        self.attributes = {}
        self.daterules = None
        self.state = '' # set and gotten by Calendar.evaluate_daterules exclusively
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

    @staticmethod
    def weekday_index(day):
        index = {
            "Monday" : 0,
            "Tuesday" : 1,
            "Wednesday" : 2,
            "Thursday" : 3,
            "Friday" : 4,
            "Saturday" : 5,
            "Sunday" : 6
        }
        return index[day]

class Evaluate_daterules:
    """ evaluation toolset to evaluate daterules in the context of a specific year """
    
    def __init__(self,calendar,year):
        self.calendar = calendar
        self.year = year
        self.easter_date = None
        self.rules = {
            "date" : self.date,
            "daterules" : self.daterules,
            "days-after" : self.days_after,
            "days-before" : self.days_before,
            "easterdate" : self.easterdate,
            "equals" : self.equals,
            "if" : self.if_then_else,
            "not-after" : self.not_after,
            "or" : self.or_logic,
            "relative-to" : self.relative_to,
            "relative-to-next-years" : self.relative_to_next_years,
            "test-day" : self.test_day,
            "weekday-after" : self.weekday_after,
            "weekday-before" : self.weekday_before,
            "weekday-before-or-self" : self.weekday_before_or_self,
            "weeks-after" : self.weeks_after,
            "weeks-before" : self.weeks_before
        }
        
    def evaluate_daterules(self,daterules):
        """ reads the element name and runs the according method 
            this method should only be called from the method in Calendar with the same name """
        action = daterules.tag
        date = self.rules[action](daterules)
        return date

    def date(self,daterules):
        day = int(daterules.get('day'))
        month = int(daterules.get('month'))
        previous_year = daterules.get('year-1')
        year = self.year if previous_year != 'true' else self.year - 1
        return date(year,month,day)
        
    def daterules(self,daterules):
        inputrules = daterules.find('*')
        date = self.evaluate_daterules(inputrules)
        return date
        
    def days_after(self,daterules):
        inputrules = daterules.find('*')
        date = self.evaluate_daterules(inputrules)
        count = int(daterules.get('nr'))
        return date + timedelta(count)
        
    def days_before(self,daterules):
        inputrules = daterules.find('*')
        date = self.evaluate_daterules(inputrules)
        count = int(daterules.get('nr'))
        return date - timedelta(count)
        
    def easterdate(self,daterules):
        if self.easter_date is None:
            tree = ET.parse('liturgy.calendar.roman-rite.easterdates.xml')
            the_date = tree.find('.//easterdate[year="' + repr(self.year) + '"]')
            year = int(the_date.findtext("year"))
            month = int(the_date.findtext("month"))
            day = int(the_date.findtext("day"))
            self.easter_date = date(year,month,day)
        return self.easter_date
        
    def equals(self,daterules):
        rules = daterules.findall('*')
        firstrules = rules[0]
        first = self.evaluate_daterules(firstrules)
        secondrules = rules[1]
        second = self.evaluate_daterules(secondrules)
        return first == second
        
    def if_then_else(self,daterules):
        testrules = daterules.find('test/*')
        test = self.evaluate_daterules(testrules)
        if test:
            inputrules = daterules.find('then/*')
        else:
            inputrules = daterules.find('else/*')
        date = self.evaluate_daterules(inputrules)
        return date
        
    def not_after(self,daterules):
        rules = daterules.findall('*')
        firstrules = rules[0]
        first = self.evaluate_daterules(firstrules)
        secondrules = rules[1]
        second = self.evaluate_daterules(secondrules)
        return first <= second
        
    def or_logic(self,daterules):
        rules = daterules.findall('*')
        firstrules = rules[0]
        first = self.evaluate_daterules(firstrules)
        secondrules = rules[1]
        second = self.evaluate_daterules(secondrules)
        return first or second
        
    def relative_to(self,daterules):
        name = daterules.get('name')
        return self.calendar.evaluate_daterules_by_name(self,name)

    def relative_to_next_years(self,daterules):
        """ this daterule can only occur with "First Sunday of Advent" as name, 
            so we're not bothering about reading the attribute """
        return Library.first_day_of_liturgical_year(self.year + 1)
        
    def test_day(self,daterules):
        inputrules = daterules.find('*')
        date = self.evaluate_daterules(inputrules)
        day = daterules.get('day')
        actual_weekday = date.weekday()
        test_weekday = Library.weekday_index(day)
        return actual_weekday == test_weekday
        
    def weekday_after(self,daterules):
        inputrules = daterules.find('*')
        inputdate = self.evaluate_daterules(inputrules)
        day = daterules.get('day')
        # get the weekday index [0-6] of the date (r) and of the day (n)
        # e.g. r is a Wednesday (3) and n is a Monday (1), so 5 days must be counted forwards
        # e.g. r is a Wednesday (3) and n is a Saturday (6), so 3 days must be counted forwards
        # e.g. r and n are both Mondays (1), so 7 days mus be counted forwards 
        # in a simple formula, this is: (n-r-1) % 7 + 1
        r = inputdate.weekday()
        n = Library.weekday_index(day)
        count = (n - r - 1) % 7 + 1
        return inputdate + timedelta(count)

    def weekday_before(self,daterules):
        inputrules = daterules.find('*')
        inputdate = self.evaluate_daterules(inputrules)
        day = daterules.get('day')
        # get the weekday index [0-6] of the date (r) and of the day (n)
        # e.g. r is a Wednesday (3) and n is a Monday (1), so 2 days must be counted backwards
        # e.g. r is a Wednesday (3) and n is a Saturday (6), so 4 days must be counted backwards
        # e.g. r and n are both Mondays (1), so 7 days mus be counted backwards 
        # in a simple formula, this is: (r-n-1) % 7 + 1
        r = inputdate.weekday()
        n = Library.weekday_index(day)
        count = (r - n - 1) % 7 + 1
        return inputdate - timedelta(count)

    def weekday_before_or_self(self,daterules):
        inputrules = daterules.find('*')
        inputdate = self.evaluate_daterules(inputrules)
        day = daterules.get('day')
        # get the weekday index [0-6] of the date (r) and of the day (n)
        # e.g. r is a Wednesday (3) and n is a Monday (1), so 2 days must be counted backwards
        # e.g. r is a Wednesday (3) and n is a Saturday (6), so 4 days must be counted backwards
        # e.g. r and n are both Mondays (1), so 0 days mus be counted backwards 
        # in a simple formula, this is: (r-n) % 7 
        r = inputdate.weekday()
        n = Library.weekday_index(day)
        count = (r - n) % 7
        return inputdate - timedelta(count)

    def weeks_after(self,daterules):
        inputrules = daterules.find('*')
        inputdate = self.evaluate_daterules(inputrules)
        count = int(daterules.get('nr'))
        return inputdate + timedelta(7 * count)
        
    def weeks_before(self,daterules):
        inputrules = daterules.find('*')
        inputdate = self.evaluate_daterules(inputrules)
        count = int(daterules.get('nr'))
        return inputdate - timedelta(7 * count)
        

class Easter_dates:

    def __init__(self): 
        """ load the xml data """
        self.easterdates = {}
        tree = ET.parse('liturgy.calendar.roman-rite.easterdates.xml')
        easterdates = tree.findall('.//easterdate')
        for the_date in easterdates:
            year = the_date.find("year")
            month = the_date.find("month")
            day = the_date.find("day")
            self.easterdates[year] = date(year,month,day)

    def get(self,year):
        return self.easterdates[year]

if __name__ == '__main__':
    ruleset = Ruleset()
    options = Options()
    calendar = Calendar(ruleset,options)
    calendar.populate()
    for coordinaterules in ruleset.get_list_of_subsets():
        print(coordinaterules.attrib['set'])