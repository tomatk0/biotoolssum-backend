from sqlalchemy import create_engine
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

engine = create_engine('sqlite:///sqlalchemy.sqlite', echo=True)

base = declarative_base()

class tools(base):
    __tablename__ = 'tools'

    bio_id = Column(String, primary_key=True)
    version = Column(String)
    bio_link = Column(String)
    homepage = Column(String)
    tool_type = Column(String)
    institute = Column(String)
    description = Column(String)
    total_citations = Column(Integer)
    topic = Column(String)
    function = Column(String)
    maturity = Column(String)
    platforms = Column(String)
    input = Column(String)
    output = Column(String)
    license = Column(String)

    def __init__(self, bio_id, version, bio_link, homepage, tool_type, institute, description, total_citations, topic, function, maturity, platforms, input, output, license):
        self.bio_id = bio_id
        self.version = version
        self.bio_link = bio_link
        self.homepage = homepage
        self.tool_type = tool_type
        self.institute = institute
        self.description = description
        self.total_citations = total_citations
        self.topic = topic
        self.function = function
        self.maturity = maturity
        self.platforms = platforms
        self.input = input
        self.output = output
        self.license = license

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'version': self.version,
                'bio_link': self.bio_link,
                'homepage': self.homepage,
                'tool_type': self.tool_type,
                'institute': self.institute,
                'description': self.description,
                'total_citations': self.total_citations,
                'topic': self.topic,
                'function': self.function,
                'maturity': self.maturity,
                'platforms': self.platforms,
                'input': self.input,
                'output': self.output,
                'license': self.license
               }

class publications(base):
    __tablename__ = 'publications'

    id = Column(Integer, primary_key=True)
    bio_id = Column(String)
    doi = Column(String)
    pmid = Column(String)
    pmcid = Column(String)
    years = Column(String)

    def __init__(self, id, bio_id, doi, pmid, pmcid, years):
        self.id = id
        self.bio_id = bio_id
        self.doi = doi
        self.pmid = pmid
        self.pmcid = pmcid
        self.years = years

    def serialize(self):
        return {
                'id': self.id,
                'bio_id': self.bio_id,
                'doi': self.doi,
                'pmid': self.pmid,
                'pmcid': self.pmcid,
                'years': self.years
               }

base.metadata.create_all(engine)