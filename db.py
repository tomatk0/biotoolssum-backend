from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

# engine = create_engine('sqlite:////home/ubuntu/flaskapp/sqlalchemy.sqlite', # For ubuntu
#                         connect_args={'check_same_thread': False})
engine = create_engine('sqlite:///sqlalchemy.sqlite', # For windows
                        connect_args={'check_same_thread': False})

base = declarative_base()

class tools(base):
    __tablename__ = 'tools'

    bio_id = Column(String, primary_key=True)
    version = Column(String)
    bio_link = Column(String)
    homepage = Column(String)
    description = Column(String)
    maturity = Column(String)
    license = Column(String)
    publications = []
    functions = []
    topics = []
    institutes = []
    platforms = []
    tool_types = []
    inputs = []
    outputs = []
    collection_ids = []
    elixir_platforms = []
    elixir_nodes = []
    elixir_communities = []

    def serialize(self):
        return {
                'bio_id': self.bio_id,
                'version': self.version,
                'bio_link': self.bio_link,
                'homepage': self.homepage,
                'description': self.description,
                'maturity': self.maturity,
                'license': self.license,
                'publications': self.publications,
                'functions': self.functions,
                'topics': self.topics,
                'institutes': self.institutes,
                'platforms': self.platforms,
                'tool_types': self.tool_types,
                'inputs': self.inputs,
                'outputs': self.outputs,
                'collection_ids': self.collection_ids,
                'elixir_platforms': self.elixir_platforms,
                'elixir_nodes': self.elixir_nodes,
                'elixir_communities': self.elixir_communities
               }

    def serialize_name_only(self):
        return {
            'bio_id': self.bio_id
        }

class publications(base):
    __tablename__ = 'publications'

    doi = Column(String, primary_key=True)
    bio_id = Column(String, primary_key=True)
    pmid = Column(String)
    pmcid = Column(String)
    citations_list = []

    def serialize(self):
        return {
                'doi': self.doi,
                'pmid': self.pmid,
                'pmcid': self.pmcid,
                'citations_list': self.citations_list
               }

class years(base):
    __tablename__ = 'years'

    doi = Column(String, primary_key=True)
    year = Column(String, primary_key=True)
    count = Column(String)

    def serialize(self):
        return {
                'year': self.year,
                'count': self.count
               }

class functions(base):
    __tablename__ = 'functions'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)
    uri = Column(String)

    def serialize(self):
        return {
                'term': self.term,
                'uri': self.uri
               }

class topics(base):
    __tablename__ = 'topics'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)
    uri = Column(String)

    def serialize(self):
        return {
                'term': self.term,
                'uri': self.uri
               }

class institutes(base):
    __tablename__ = 'institutes'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def serialize(self):
        return {
                'name': self.name
               }

class platforms(base):
    __tablename__ = 'platforms'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def serialize(self):
        return {
                'name': self.name
               }

class tool_types(base):
    __tablename__ = 'tool_types'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def serialize(self):
        return {
                'name': self.name
               }

class inputs(base):
    __tablename__ = 'inputs'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)

    def serialize(self):
        return {
                'term': self.term
               }

class outputs(base):
    __tablename__ = 'outputs'

    bio_id = Column(String, primary_key=True)
    term = Column(String, primary_key=True)

    def serialize(self):
        return {
                'term': self.term
               }

class collection_ids(base):
    __tablename__ = 'collection_ids'

    bio_id = Column(String, primary_key=True)
    coll_id = Column(String, primary_key=True)

    def serialize(self):
        return {
                'coll_id': self.coll_id
        }

class elixir_platforms(base):
    __tablename__ = 'elixir_platforms'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def serialize(self):
        return {
            'name': self.name
        }

class elixir_nodes(base):
    __tablename__ = 'elixir_nodes'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    
    def serialize(self):
        return {
            'name': self.name
        }

class elixir_communities(base):
    __tablename__ = 'elixir_communities'

    bio_id = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def serialize(self):
        return {
            'name': self.name
        }

class queries(base):
    __tablename__ = 'queries'

    id = Column(Integer, primary_key=True)
    collection_id = Column(String)
    topic = Column(String)
    tools_list = Column(String)
    only_names = Column(String)

    def serialize(self):
        if self.collection_id:
            return {
                'id': self.id,
                'collection_id': self.collection_id,
                'only_names': self.only_names
            }
        elif self.topic:
            return {
                'id': self.id,
                'topic': self.topic,
                'only_names': self.only_names
            }
        elif self.tools_list:
            return {
                'id': self.id,
                'tools_list': self.tools_list,
                'only_names': self.only_names
            }

base.metadata.create_all(engine)
