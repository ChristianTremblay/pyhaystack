__author__ = 'Yafit'
import requests

ip = 'http://52.16.65.135:8080'

#TODO : See Haystack client as a template.

def loginApi(ip,username, password):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'password': password}
    r = requests.get(ip + '/rest/v1/login/' + username, headers=myHeader)
    print r.status_code
    setCookie = r.headers['Set-Cookie']
    print setCookie
    print r.content
    return setCookie


def usersApi(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Query Users
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users', headers=myHeader, cookies=reqCookie)
    #print r.status_code
    #print r.content


def currentUser(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get current user
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/current', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def explainQuery(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get Explaination For Query
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/explain-query', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersList(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return:Get all user
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/list', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def getNewUser(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return:Get new user
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/new/user', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersPremissions(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get User Permissions Information for all users
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/permissions', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content


def usersPremissionsGroups(ip,reqCookie):
    """
    :param ip:
    :param reqCookie:
    :return: Get All User Groups
    """
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/users/permissions-groups', headers=myHeader, cookies=reqCookie)
    print r.status_code
    print r.content

def dataPointsApi(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-points',headers=myHeader,cookies=reqCookie)
    #print r.status_code
    #print r.content


def dataPointsSummary(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-point-summaries',headers=myHeader,cookies=reqCookie)
    #print r.status_code
   # print r.content


def dataSources(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/data-sources/list',headers=myHeader,cookies=reqCookie)
    print r.status_code
    #print r.content


def eventsApi(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/events',headers=myHeader,cookies=reqCookie)
    print r.status_code
    print r.content


def userComments(ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/comments',headers=myHeader,cookies=reqCookie)
    print r.status_code
    print r.content


def logoutApi (ip, reqCookie):
    myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    r = requests.get(ip + '/rest/v1/logout',headers=myHeader,cookies=reqCookie)
    #print r.status_code
    #print r.content


def parseMyCookie(reqCookie):
    tempCookie = reqCookie.split(';')[0]
    myCookie = {tempCookie.split('=')[0] :tempCookie.split('=')[1]}
    return myCookie

username = '###'
password = '#####'
myCookie = loginApi(ip,username,password) #must login before doing anything else!!!
parsedCookie =  parseMyCookie(myCookie)

#usersApi(ip, parsedCookie)
currentUser(ip, parsedCookie)

#dataPointsApi(ip, parsedCookie)
#dataPointsSummary(ip, parsedCookie)
#dataSources(ip, parsedCookie)
#eventsApi(ip, parsedCookie)
#userComments(ip, parsedCookie)
#logoutApi(ip, parsedCookie)

