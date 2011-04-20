#!/usr/bin/env python
# encoding: utf-8
"""
aukpilot.py

Created by Sean Redmond on 2011-04-20.
Copyright (c) 2011 Sean Redmond. All rights reserved.
"""

__author__ =  'Sean Redmond'
__version__=  '0.1'

import urllib
import httplib
import simplejson as json

class AukPilotBase(object):
    API = "api.klout.com"
    VER = 1
    FORMAT = 'json'
    KEY = None
    CONN = None

    def __init__(self, key):
        self.KEY = key
        self.CONN = httplib.HTTPConnection(self.API)


    def _get(self, url, **kwargs):
        self.CONN.request('GET', self._url(url, **kwargs))
        resp = self.CONN.getresponse()
        data = resp.read()
        try:
            if resp.status == 200:
                return json.loads(data)
            else:
                raise AukPilotRequestError(resp.status)
        except json.decoder.JSONDecodeError:
            print d

    def _url(self, url, **kwargs):
        """Return URL to fetch data."""
        kwargs['key'] = self.KEY
        return "/%i/%s.%s?%s" % (self.VER, url, self.FORMAT, 
                                 urllib.unquote(urllib.urlencode(kwargs)))

class AukPilot(AukPilotBase):
    """ 
    Interface to Klout (http://klout.com) API
    
    Auk Pilot is an anagram of Klout API. So is Oak Tulip, but Auk Pilot
    is more fun.
    """
        
    def __init__(self, key):
        super(AukPilot, self).__init__(key)
        
        
    def scores(self, users):
        """Return the klout scores for one or more users.

        Arguments:
        users -- A list or tuple of containing user names or comma-delimited 
        list string containing user names.

        Returns:
        A list of tuples in the form [('user1', score1), ('user2', score2)...]
        Names are returned as unicode strings and scores as floats

        """
        if isinstance(users, (list, tuple)):
            params = {'users': ','.join(users)}
        else:
            params = {'users': users}
        data = self._get('klout', **params)
        return  [(r['twitter_screen_name'], r['kscore']) for r in data['users']] 

    def users(self, users):
        if isinstance(users, (list, tuple)):
            params = {'users': ','.join(users)}
        else:
            params = {'users': users}
        data = self._get('users/show', **params)
        return [User(d, self.KEY) for d in data['users']] 

class User(AukPilotBase):
    def __init__(self, data, key):
        super(User, self).__init__(key)
        self._topics = None
        self._influencers = None
        self._influencees = None
        self._data = []

        if isinstance(data, dict):
            self._data = data
        else:
            self._data = self._get('users/show', users=data)['users'][0]
            
    def name(self):
        """Return the user's twitter screen name"""
        return self._data['twitter_screen_name']
        
    def id(self):
        """Return the user's twitter id"""
        return self._data['twitter_id']

    def klout(self):
        """Return the user's klout score (as a float)"""
        return self._data['score']['kscore']
        
    def true_reach(self):
        """Return the user's true reach (as in int)"""
        return self._data['score']['true_reach']
        
    def amplification(self):
        """Return the user's amplification score (as a float)"""
        return self._data['score']['amplification_score']
        
    def network(self):
        """Return the user's network score (as a float)"""
        return self._data['score']['network_score']
        
    def classification(self):
        """Return the user's klout classification"""
        return self._data['score']['kclass']
        
    def topics(self, **kwargs):
        """Return a list of topics in which the user is most active"""
        if self._topics is None:
            data = self._get('users/topics', users=self.name())
            if data['users']:
                self._topics = data['users'][0]['topics']
            else:
                self._topics = []
        return self._topics
        
    def influencers(self):
        """Return a list of users who influence this user"""
        if self._influencers is None:
            data = self._get('soi/influenced_by', users=self.name())
            try:
                if data['users'][0]['influencers']:
                    self._influencers = [u['twitter_screen_name'] 
                        for u in data['users'][0]['influencers']]
                else:
                    self._influencers = []
            except AukPilotRequestError, e:
                if e.value == 404:
                    self._influencers = []
                else:
                    raise e
        return self._influencers

    def influencees(self):
        """Return a list of users whom this user influences"""
        if self._influencees is None:
            try:
                data = self._get('soi/influencer_of', users=self.name())
                if data['users'][0]['influencees']:
                    self._influencees = [u['twitter_screen_name'] 
                        for u in data['users'][0]['influencees']]
                else:
                    self._influencees = []
            except AukPilotRequestError, e:
                if e.value == 404:
                    self._influencees = []
                else:
                    raise e
        return self._influencees
        
    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError("No attribute named '%s'" % (name))


class AukPilotError(Exception):
    """Base class for errors in the AukPilot package."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class AukPilotRequestError(AukPilotError):
    pass

