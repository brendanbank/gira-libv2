from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload
import sqlalchemy 

import logging, sys
import json

logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger(__name__)



Base = declarative_base()

class Setting(Base):
    __tablename__ = 'server_cache'
    
    instance = Column((String(255)), primary_key=True)
    key_id = Column(String(255), primary_key=True)
    value = Column(Text(4294000000))

    # Lets us print out a user object conveniently.
    def __repr__(self):
        return f"<Setting(instance='{self.instance}' id='{self.key_id}', value='{self.value}'>"

class ServerCache(object):
    
    _ignore_ = ['instance', 'engine', 'sessionmaker', 'session', 'get_variable',  'set_variable', '__dict__', 
                'ignore', 
                'set_ignore']
                    
    def __init__(self, dburi, instance, echo=False, future=True):

        self.engine = sqlalchemy.create_engine(dburi, echo=echo, future=True)
        Base.metadata.create_all(self.engine) 
        self.instance = instance
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.session = self.sessionmaker()
        self.ignore = []
        
    def invalidate(self):
        self.session.query(Setting).filter(Setting.instance==self.instance).delete()
        self.session.commit()        
                
    def set_variable(self,key_id,value):
        
        if (key_id in self.ignore):
            return(None)

        setting = self.session.query(Setting).filter(Setting.instance == self.instance, Setting.key_id == key_id).first()        
        
        if not (setting):
            setting = Setting(instance=self.instance, key_id=key_id, value=value)
            self.session.add(setting)
        else:
            setting.value = value
        
        self.session.commit()
        return(None)


    def get_variable(self,key_id):
        
        
        if (key_id in self.ignore):
            return(None)

        setting = self.session.query(Setting).filter(Setting.instance == self.instance, Setting.key_id == key_id).first()
        if setting:
            return setting.value
        
        return(None)
    
    def set_ignore(self,ignore_list):
        self.ignore = self.ignore + ignore_list
    
class CacheObject(ServerCache):

    def __setattr__(self, name, value):
        if not name in super(CacheObject, self)._ignore_:
            super(CacheObject, self).set_variable(name,value)
            
        super(CacheObject, self).__dict__[name] = value

    # Gets called when an attribute is accessed
    def __getattribute__(self, name):
        
        if not name in super(CacheObject, self)._ignore_ and name in super(CacheObject, self).__dict__ and super(CacheObject, self).__dict__[name] == None:
    
            setting = super(CacheObject, self).get_variable(name)
            if setting:
                super(CacheObject, self).__dict__[name] = setting
            else:
                super(CacheObject, self).__dict__[name] = None
    
        # Calling the super class to avoid recursion
        return super(CacheObject, self).__getattribute__(name)
    
    # Gets called when the item is not found via __getattribute__
    def __getattr__(self, name):
                    
        if not name in super(CacheObject, self)._ignore_:
            setting = super(CacheObject, self).get_variable(name)
            if setting:
                super(CacheObject, self).__dict__[name] = setting
                return(setting)

        # Calling the super class to avoid recursion
        return super(CacheObject, self).__setattr__(name, None)

# if __name__ == '__main__':
#
#     # server = CacheObject(gira_settings.get_property('SQLALCHEMY_DATABASE_URI'), 'srv1.bgwlan.nl')
#     # server.hostname = 'srv1'
#
#     # server = Test(gira_settings.get_property('SQLALCHEMY_DATABASE_URI'), 'srv1.bgwlan.nl')
#     # new = Test()
#     # new.test = "a"
#     # print (vars(new))
#
#
#
#     x = CacheObject(gira_settings.get_property('SQLALCHEMY_DATABASE_URI'), 'srv1.bgwlan.nl')
#     x._token = None
#     x.config_version = None
#
#     log.debug (x._token)
#     log.debug (x._token)
