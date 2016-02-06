from flask import g, redirect, url_for, abort, \
     render_template, flash
from bikeandwalk import app, db, mail
from flask_mail import Message
from views.utils import printException, cleanRecordID
from models import Organization

def sendInvite(assignment,user,countEventDict):
    """ Send a single counting Assignment email """
    hostName = app.config["HOST_NAME"]
    organization = Organization.query.get(cleanRecordID(g.orgID))
    
    with mail.record_messages() as outbox:
        if user and assignment and organization:
            subject = "Your assignment from %s" % (organization.name)
            msg = Message( subject,
                          sender=(organization.name, organization.email),
                          recipients=[(user.name, user.email)])

            msg.body = render_template("email/standardInvite.txt", 
                assignment=assignment,
                countEventDict=countEventDict,
                user=user,
                hostName = hostName,
                )
            msg.html = render_template("email/standardInvite.html", 
                    assignment=assignment,
                    countEventDict=countEventDict,
                    user=user,
                    hostName = hostName,
                    )
        else:
            mes = "Email is missing parameters"
            printException(mes,"error",e)
            return (False, mes)
        
        try:
            mail.send(msg)
        except Exception as e:
            mes = "Error Sending email"
            printException(mes,"error",e)
            return (False, mes)
    
    if mail.suppress:
        mes = '%d email(s) would have been sent if we were not testing' % (len(outbox))
        return (True, mes )
        
    return (True, "Email Sent Successfully")
    