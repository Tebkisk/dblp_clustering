class dblp_author:
    def __init__(self,author_id):
        self.id = author_id
        self.papers = {}
        self.confs = {}
    def addPaperYear(self,year):
        if year not in self.papers.keys():
            self.papers[year] = []
    def addPaper(self,year,paper_id):
        self.papers[year].append(paper_id)
    def addConfYear(self,year):
        if year not in self.confs.keys():
            self.confs[year] = set()
    def addConf(self,year,conf_id):
        self.confs[year].add(conf_id)
    def getInfo(self):
        papers_output = "Papers:\n"
        for year in self.papers.keys():
            papers_output += ("\t" + year + ":\n")
            for paper_id in self.papers[year]:
                papers_output += ("\t\t" + paper_id + "\n")
        confs_output = "Conferences:\n"
        for year in self.confs.keys():
            confs_output += ("\t" + year + ":\n")
            for conf_id in self.confs[year]:
                confs_output += ("\t\t" + conf_id + "\n")
        info = "ID:" + self.id + "\n" + confs_output + papers_output + "\n"
        return info
class dblp_conference:
    def __init__(self,conf_id):
        self.id = conf_id
        self.name = "N/A"
        self.years = set()
    def addYear(self,year):
        self.years.add(year)
    def setName(self,name):
        self.name = name
        # Use lxml/html, connect to dblp & retrieve name of conference
    def getInfo(self):
        info = "ID:" + str(self.id) + "\n" + "Name:" + str(self.name) + "\n" + "Years held:" + str(self.years) + "\n"
        return info
    def getYears(self):
        return list(self.years)
