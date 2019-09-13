from django.db import models


class Publisher(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default="")
    slug = models.CharField(max_length=110, default="", null=True, blank=True)

    def __str__(self):
        return self.name


class ComicSeries(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, default="", null=True, blank=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True)
    start_year = models.CharField(max_length=4, default="", null=True, blank=True)
    volume = models.CharField(max_length=5, default="", null=True, blank=True)
    folder_path = models.FilePathField(default="", allow_folders=True, null=True, blank=True)
    web_link = models.CharField(max_length=100, default="", null=True, blank=True)
    slug = models.CharField(max_length=225, default="", null=True, blank=True)

    def __str__(self):
        return self.name


class StoryArc(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, default="", null=True, blank=True)
    slug = models.CharField(max_length=225, default="", null=True, blank=True)

    def __str__(self):
        return self.name


class ComicBook(models.Model):
    id = models.AutoField(primary_key=True)
    series_name = models.CharField(max_length=200, default="", null=True, blank=True)
    issue_number = models.IntegerField(max_length=7, default=0, null=True, blank=True)
    series = models.ForeignKey(ComicSeries, on_delete=models.SET_NULL, null=True, blank=True)
    year = models.CharField(max_length=4, default="", null=True, blank=True)
    month = models.CharField(max_length=2, default="", null=True, blank=True)
    day = models.CharField(max_length=2, default="", null=True, blank=True)
    arc = models.ForeignKey(StoryArc, on_delete=models.SET_NULL, null=True, blank=True)
    comments = models.TextField(default="", null=True, blank=True)
    notes = models.TextField(default="", null=True, blank=True)
    web_link = models.TextField(default="", null=True, blank=True)
    page_count = models.IntegerField(max_length=7, null=True, blank=True)
    file_path = models.FilePathField(default="", allow_files=True, null=True, blank=True)
    is_read = models.BooleanField(default=False, null=True, blank=True)
    slug = models.CharField(max_length=225, default="", null=True, blank=True)

    def __str__(self):
        return self.series_name + "-" + str(self.issue_number)


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default="", null=True, blank=True)
    slug = models.CharField(max_length=125, default="", null=True, blank=True)
    issues = models.ManyToManyField(ComicBook, null=True, blank=True)

    def __str__(self):
        return self.name


class Character(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default="", null=True, blank=True)
    slug = models.CharField(max_length=125, default="", null=True, blank=True)
    issues = models.ManyToManyField(ComicBook, null=True, blank=True)

    def __str__(self):
        return self.name

