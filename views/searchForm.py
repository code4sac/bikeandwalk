"""
Some routines that I will use in a semi generic searh form for lists and maps
"""

from bikeandwalk import db


def orgsToDict(myDictionary):
    '''create an element in queryData dict that contains a list of 
       dicts of data from the organiztions table
    '''

    # myDictionary is a dictionary
    myDictionary["orgs"] = []
    sql = "select * from organization where 1=1 "
    sql += " order by 'name'"

    orgs = db.engine.execute(sql).fetchall()

    if orgs:
        for org in orgs:
            d = {'name':org.name, 'ID':str(org.ID)}
            myDictionary['orgs'].append(d)
            
            
    # get the events
def eventsToDict(queryData):
    searchOrgs = queryData.get('searchOrgs',None)
    theEvents = ""
    sql = "select * from count_event "
    
    if searchOrgs and len(searchOrgs) > 0 and '0' not in searchOrgs:
        for i in range(len(searchOrgs)):
            if i != '0' and searchOrgs[i].isdigit():
                theEvents+= searchOrgs[i]+ ","
        if theEvents != "":
            sql += " where count_event.organization_ID in (%s) " % (theEvents[0:-1])

    sql += " order by startDate desc"
    
    events = db.engine.execute(sql).fetchall()
    if events:
        queryData['events'] = []
        for event in events:
            d = {'name':event.title, 'ID':str(event.ID)}
            queryData['events'].append(d)
            

def getSelectValues(requestForm,searchOrgs,searchEvents):
    """
    populate the searchOrgs and searchEvents lists with values 
    from the form select objects
    """
    # all parameters must be empty lists
    # lists will be manipulated directly. 
    # DON'T ASSIGN VALUES TO LISTS - USE .append()

    if requestForm and 'searchOrgs' in requestForm.keys():
        tempList = requestForm.getlist('searchOrgs')
        if '0' in tempList:
            # if 'ALL' is selected just show all
            searchOrgs.append('0')
        else:
            for i in tempList:
                searchOrgs.append(i)
    else:
        searchOrgs.append('0')

    if requestForm and 'searchEvents' in requestForm.keys():
        tempList = requestForm.getlist('searchEvents')
        if '0' in tempList:
            # if 'ALL' is selected just show all
            searchEvents.append('0')
        else:
            for i in tempList:
                searchEvents.append(i)
    else:
        searchEvents.append('0')