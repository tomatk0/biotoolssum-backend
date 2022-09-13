from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Identity
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///sqlalchemy.sqlite', echo=True)

base = declarative_base()

class tools(base):
    __tablename__ = 'tools'

    bio_id = Column(String, primary_key=True)
    version = Column(String)
    bio_link = Column(String)
    homepage = Column(String)
    description = Column(String)
    total_citations = Column(Integer)
    maturity = Column(String)
    cost = Column(String)
    license = Column(String)

    def __init__(self, bio_id, version, bio_link, homepage, description, total_citations, maturity, cost, license):
        self.bio_id = bio_id
        self.version = version
        self.bio_link = bio_link
        self.homepage = homepage
        self.description = description
        self.total_citations = total_citations
        self.maturity = maturity
        self.cost = cost
        self.license = license

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'version': self.version,
                'bio_link': self.bio_link,
                'homepage': self.homepage,
                'description': self.description,
                'total_citations': self.total_citations,
                'maturity': self.maturity,
                'cost': self.cost,
                'license': self.license
               }

class publications(base):
    __tablename__ = 'publications'

    doi = Column(String, primary_key=True)
    bio_id = Column(String, primary_key=True)
    pmid = Column(String)
    pmcid = Column(String)

    def __init__(self, doi, bio_id, pmid, pmcid):
        self.doi = doi
        self.bio_id = bio_id
        self.pmid = pmid
        self.pmcid = pmcid

    def serialize(self):
        return {
                'doi': self.doi,
                'bio_id': self.bio_id,
                'pmid': self.pmid,
                'pmcid': self.pmcid,
               }

class years(base):
    __tablename__ = 'years'

    doi = Column(String, primary_key=True)
    year = Column(String, primary_key=True)
    count = Column(String)

    def __init__(self, doi, year, count):
        self.doi = doi,
        self.year = year,
        self.count = count

    def serialize(self):
        return {
                'doi': self.doi,
                'year': self.year,
                'count': self.count
               }

class functions(base):
    __tablename__ = 'functions'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)
    uri = Column(String)

    def __init__(self, bio_id, term, uri):
        self.bio_id = bio_id
        self.term = term
        self.uri = uri

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'term': self.term,
                'uri': self.uri
               }

class topics(base):
    __tablename__ = 'topics'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)
    uri = Column(String)

    def __init__(self, bio_id, term, uri):
        self.bio_id = bio_id
        self.term = term
        self.uri = uri

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'term': self.term,
                'uri': self.uri
               }

class institutes(base):
    __tablename__ = 'institutes'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def __init__(self, bio_id, name):
        self.bio_id = bio_id
        self.name = name

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'name': self.name
               }

class platforms(base):
    __tablename__ = 'platforms'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def __init__(self, bio_id, name):
        self.bio_id = bio_id
        self.name = name

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'name': self.name
               }

class tool_types(base):
    __tablename__ = 'tool_types'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def __init__(self, bio_id, name):
        self.bio_id = bio_id
        self.name = name

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'name': self.name
               }

class inputs(base):
    __tablename__ = 'inputs'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)

    def __init__(self, bio_id, term):
        self.bio_id = bio_id
        self.term = term

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'term': self.term
               }

class outputs(base):
    __tablename__ = 'outputs'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)

    def __init__(self, bio_id, term):
        self.bio_id = bio_id
        self.term = term

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'term': self.term
               }

class collection_ids(base):
    __tablename__ = 'collection_ids'

    bio_id = Column(String, primary_key=True)
    coll_id = Column(String, primary_key=True)

    def __init__(self, bio_id, coll_id):
        self.bio_id = bio_id
        self.coll_id = coll_id

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'coll_id': self.coll_id
        }


base.metadata.create_all(engine)