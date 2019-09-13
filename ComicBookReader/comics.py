# ZIP and RAR imports to work with comic files
from zipfile import ZipFile  # To convert and read from later
from unrar.rarfile import RarFile  # To read from RAR files
# XML browsing for ComicRack metadata
from xml.etree import ElementTree as ET  # To parse through the ComicInfo.xml
# Python imports
import os  # To traverse the file system
from threading import Thread
from time import sleep
# django imports
from .models import *
from django.db import connection
from django import db

# folder = 'O:\\1872 (2015)'
# file = folder + '\\1872 1 (2015).cbr'

comic_path = os.path.abspath("O:\\1872 (2015)")

# comic_path = os.path.abspath(file)

# comicfile = ZipFile(file, "r")
# print(comic_path)
# print(os.path.dirname(comic_path))


class ComicScrape(Thread):
    def __init__(self, comic_dir):
        Thread.__init__(self)
        self.comic_dir = comic_dir

    def run(self):
        for root, dirs, files in os.walk(self.comic_dir, topdown=True):
            for file in files:
                if file.endswith('.cbr'):
                    file_name = file.split('.cbr')[0]
                    zip_file_name = file_name + '.cbz'
                    print(zip_file_name)

                    comic = RarFile(file)
                    comic.testrar()
                    print(zip_file_name)
                    zip_comic = ZipFile(zip_file_name, 'w')

                    self.convert_rar_to_zip(comic, zip_comic)

                if file.endswith('.cbz'):
                    zip_comic = ZipFile(file)
                    self.gather_comic_info(zip_comic)

    def convert_rar_to_zip(self, rar_file, zip_file):
        for member in rar_file.namelist():
            print(member)
            rar_file.extract(member, self.comic_dir)
            file_abs_path = os.path.abspath(self.comic_dir + "\\" + member)
            zip_file.write(file_abs_path, member)
            os.remove(file_abs_path)

            self.gather_comic_info(zip_file)

    def gather_comic_info(self, zip_file):
        if 'ComicInfo.xml' in zip_file.namelist():
            comic_data = ET.fromstring(zip_file.read('ComicInfo.xml'))
            # DB fields
            title = comic_data.find('Title')
            if ET.iselement(title):
                title = title.text

            series = comic_data.find('Series')
            if ET.iselement(series):
                series = series.text

            issue_num = comic_data.find('Number')
            if ET.iselement(issue_num):
                issue_num = issue_num.text

            story_arc = comic_data.find('StoryArc')
            if ET.iselement(story_arc):
                story_arc = story_arc.text

            summary = comic_data.find('Summary')
            if ET.iselement(summary):
                summary = summary.text

            notes = comic_data.find('Notes')
            if ET.iselement(notes):
                notes = notes.text

            issue_year = comic_data.find('Year')
            if ET.iselement(issue_year):
                issue_year = issue_year.text

            issue_month = comic_data.find('Month')
            if ET.iselement(issue_month):
                issue_month = issue_month.text

            issue_day = comic_data.find('Day')
            if ET.iselement(issue_day):
                issue_day = issue_day.text

            publisher = comic_data.find('Publisher')
            if ET.iselement(publisher):
                publisher = publisher.text

            web_link = comic_data.find('Web')
            if ET.iselement(web_link):
                web_link = web_link.text

            page_count = comic_data.find('PageCount')
            if ET.iselement(page_count):
                page_count = page_count.text

            characters = comic_data.find('Characters')
            if ET.iselement(characters):
                characters = characters.text

            locations = comic_data.find('Locations')
            if ET.iselement(locations):
                locations = locations.text

            zip_file_path = os.path.abspath(zip_file.filename)

            # get publisher for comic
            try:
                db_publisher = Publisher.objects.get(name=publisher)
            except Publisher.DoesNotExist:
                self.create_publisher(publisher)
                db_publisher = Publisher.objects.get(name=publisher)
            except Publisher.MultipleObjectsReturned:
                publisher_list = Publisher.objects.all().sort_by('id')
                prime_publisher = ""
                for pub in publisher_list:
                    if pub.name == publisher and prime_publisher == "":
                        prime_publisher = pub
                    elif pub.name == publisher and prime_publisher != "":
                        pub.delete()
                db_publisher = prime_publisher

            # get series for comic
            try:
                db_series = ComicSeries.objects.get(name=series)
            except ComicSeries.DoesNotExist:
                self.create_series(series, db_publisher)
                db_series = ComicSeries.objects.get(name=series, publisher=db_publisher)
            except ComicSeries.MultipleObjectsReturned:
                series_list = ComicSeries.objects.all().sort_by('id')
                prime_series = ""
                for cs in series_list:
                    if cs.name == series and prime_series == "":
                        prime_series = cs
                    elif cs.name == series and prime_series != "":
                        cs.delete()
                db_series = prime_series

            try:
                db_story_arc = StoryArc.objects.get(name=story_arc)
            except StoryArc.DoesNotExist:
                self.create_story_arc(name=story_arc)
                db_story_arc = StoryArc.objects.get(name=story_arc)

            try:
                db_comic = ComicBook.objects.get(file_path=zip_file_path)
                self.update_db_comic(db_comic, title, db_series, issue_num, db_story_arc, summary, notes, issue_year,
                                     issue_month, issue_day, db_publisher, web_link, page_count, characters, locations)
            except ComicBook.DoesNotExist:
                self.create_db_comic(title, series, issue_num, story_arc, summary, notes, issue_year, issue_month,
                                     issue_day, publisher, web_link, page_count, characters, locations, zip_file_path)

        zip_file.close()

    def create_db_comic(self, title, db_series, issue_num, db_story_arc, summary, notes, issue_year, issue_month,
                        issue_day, db_publisher, web_link, page_count, characters, locations, zip_file_path):
        print("Comic %s does not exist in database, creating entry" % title)
        while True:
            try:
                db_comic = ComicBook.objects.create(file_path=zip_file_path)
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        while True:
            try:
                db_comic.slug = title + "-" + issue_num + "-" + str(db_comic.slug)
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        self.update_db_comic(db_comic, title, db_series, issue_num, db_story_arc, summary, notes, issue_year,
                             issue_month, issue_day, db_publisher, web_link, page_count, characters, locations)

    def update_db_comic(self, db_comic, title, db_series, issue_num, db_story_arc, summary, notes, issue_year,
                        issue_month, issue_day, db_publisher, web_link, page_count, characters, locations):
        db_comic.title = title
        db_comic.series = db_series
        db_comic.issue_num = issue_num
        db_comic.story_arc = db_story_arc
        db_comic.summary = summary
        db_comic.notes = notes
        db_comic.year = issue_year
        db_comic.month = issue_month
        db_comic.day = issue_day
        db_comic.publisher = db_publisher
        db_comic.web_link = web_link
        db_comic.page_count = page_count
        db_comic.characters = characters
        db_comic.locations = locations

    def create_publisher(self, publisher):
        while True:
            try:
                db_publisher = Publisher.objects.create(name=publisher)
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        db_publisher.slug = publisher + "-" + str(db_publisher.id)

        while True:
            try:
                db_publisher.save()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        return db_publisher

    def create_series(self, name, publisher):
        try:
            db_publisher = Publisher.objects.get(name=publisher)
        except Publisher.DoesNotExist:
            db_publisher = self.create_publisher(publisher)
        except Publisher.MultipleObjectsReturned:
            publisher_list = Publisher.objects.all().sort_by('id')
            prime_publisher = ""
            for pub in publisher_list:
                if pub.name == publisher and prime_publisher == "":
                    prime_publisher = pub
                elif pub.name == publisher and prime_publisher != "":
                    pub.delete()
            db_publisher = prime_publisher

        while True:
            try:
                db_series = ComicSeries.objects.create(name=name,
                                                       publisher=db_publisher)
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        db_series.slug = name + "-" + str(db_series.id)

        while True:
            try:
                db_series.save()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        return db_series

    def create_character(self, name):
        while True:
            try:
                db_character = Character.objects.create(name=name)
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        db_character.slug = name + "-" + str(db_character.id)

        while True:
            try:
                db_character.save()
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        return db_character

    def create_location(self, name):
        while True:
            try:
                db_location = Location.objects.create(name=name)
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        db_location.slug = name + "-" + str(db_location.id)

        while True:
            try:
                db_location.save()
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        return db_location

    def create_story_arc(self, name):
        while True:
            try:
                db_story_arc = StoryArc.objects.create(name=name)
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        db_story_arc.slug = name + "-" - str(db_story_arc.id)

        while True:
            try:
                db_story_arc.save()
                connection.close()
                break
            except db.utils.OperationalError:
                print("DB is locked, will wait to try again")
                sleep(1)

        return db_story_arc
