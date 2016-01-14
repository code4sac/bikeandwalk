#Overview of web request handling

> All requests are initially routed to bikeandwalk.py
>> The method `before_request` is called to
   log user in if needed.

>> After log in the globals g.email, g.role, & g.orgID will be set

> Request is then routed to the requested view controller (views.count, views.user, etc.)
>> The view controller is responsible to returning the result of the request 
  (usually HTML rendered from a template)