from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base

# engine = create_engine('sqlite:////home/ubuntu/flaskapp/sqlalchemy.sqlite', # For ubuntu
#                         connect_args={'check_same_thread': False})
# engine = create_engine('sqlite:///sqlalchemy.sqlite', # For windows
#                         connect_args={'check_same_thread': False})

engine = create_engine('mysql+pymysql://biotoolsDB:kappa123@localhost/biotoolsDB29')
base = declarative_base()

class tools(base):
    __tablename__ = 'tools'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255))
    version = Column(String(255))
    bio_link = Column(String(255))
    homepage = Column(String(255))
    description = Column(String(1024))
    maturity = Column(String(255))
    license = Column(String(255))
    citation_count = Column(Integer)
    impact_factor = Column(Float)
    journals = Column(String(255))
    availability = Column(Integer)
    documentation = Column(String(255))
    github_url = Column(String(255))
    github_created_at = Column(String(255))
    github_updated_at = Column(String(255))
    github_forks = Column(Integer)
    github_contributions = Column(Integer)
    last_updated = Column(Date)
    min_year = Column(String(255))
    max_year = Column(String(255))
    matrix_queries = []
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
                'name': self.name,
                'version': self.version,
                'bio_link': self.bio_link,
                'homepage': self.homepage,
                'description': self.description,
                'maturity': self.maturity,
                'license': self.license,
                'citation_count': self.citation_count,
                'impact_factor': self.impact_factor,
                'journals': self.journals,
                'availability': self.availability,
                'documentation': self.documentation,
                'github_url': self.github_url,
                'github_created_at': self.github_created_at,
                'github_updated_at': self.github_updated_at,
                'github_forks': self.github_forks,
                'github_contributions': self.github_contributions,
                'matrix_queries': self.matrix_queries,
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
                'elixir_communities': self.elixir_communities,
                'min_year': self.min_year,
                'max_year': self.max_year
               }

    def serialize_name_only(self):
        return {
            'bio_id': self.bio_id
        }

class publications(base):
    __tablename__ = 'publications'

    doi = Column(String(255), primary_key=True)
    bio_id = Column(String(255), primary_key=True)
    pmid = Column(String(255))
    pmcid = Column(String(255))
    citations_source = Column(String(255))
    journal = Column(String(255))
    impact_factor = Column(Float)
    citation_count = Column(Integer)
    citations_list = []

    def serialize(self):
        return {
                'doi': self.doi,
                'pmid': self.pmid,
                'pmcid': self.pmcid,
                'citations_source': self.citations_source,
                'citations_list': self.citations_list,
               }

class years(base):
    __tablename__ = 'years'

    doi = Column(String(255), primary_key=True)
    year = Column(String(255), primary_key=True)
    count = Column(String(255))

    def serialize(self):
        return {
                'year': self.year,
                'count': self.count
               }

class functions(base):
    __tablename__ = 'functions'

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)
    uri = Column(String(255))

    def serialize(self):
        return {
                'term': self.term,
                'uri': self.uri
               }

class topics(base):
    __tablename__ = 'topics'

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)
    uri = Column(String(255))

    def serialize(self):
        return {
                'term': self.term,
                'uri': self.uri
               }

class institutes(base):
    __tablename__ = 'institutes'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'name': self.name
               }

class platforms(base):
    __tablename__ = 'platforms'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'name': self.name
               }

class tool_types(base):
    __tablename__ = 'tool_types'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'name': self.name
               }

class inputs(base):
    __tablename__ = 'inputs'

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'term': self.term
               }

class outputs(base):
    __tablename__ = 'outputs'

    bio_id = Column(String(255), primary_key=True)
    term = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'term': self.term
               }

class collection_ids(base):
    __tablename__ = 'collection_ids'

    bio_id = Column(String(255), primary_key=True)
    coll_id = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'coll_id': self.coll_id
        }

class elixir_platforms(base):
    __tablename__ = 'elixir_platforms'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {
            'name': self.name
        }

class elixir_nodes(base):
    __tablename__ = 'elixir_nodes'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)
    
    def serialize(self):
        return {
            'name': self.name
        }

class elixir_communities(base):
    __tablename__ = 'elixir_communities'

    bio_id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)

    def serialize(self):
        return {
            'name': self.name
        }

class queries(base):
    __tablename__ = 'queries'

    id = Column(String(255), primary_key=True)
    collection_id = Column(String(255))
    topic = Column(String(255))
    tools_list = Column(String(255))
    display_type = Column(String(255))
    only_names = Column(String(255))

    def serialize(self):
        if self.collection_id:
            return {
                'id': self.id,
                'collection_id': self.collection_id,
                'only_names': self.only_names,
                'display_type': self.display_type
            }
        elif self.topic:
            return {
                'id': self.id,
                'topic': self.topic,
                'only_names': self.only_names,
                'display_type': self.display_type
            }
        elif self.tools_list:
            return {
                'id': self.id,
                'tools_list': self.tools_list,
                'only_names': self.only_names,
                'display_type': self.display_type
            }

class matrix_queries(base):
    __tablename__ = 'matrix_queries'

    bio_id = Column(String(255), primary_key=True)
    matrix_query = Column(String(255), primary_key=True)

    def serialize(self):
        return {
                'matrix_query': self.matrix_query
        }


base.metadata.create_all(engine)
