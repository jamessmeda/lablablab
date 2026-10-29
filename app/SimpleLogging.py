from time import *

rfc822Time = '%a, %d %b %Y %H:%M:%S %Z'

class SimpleLogger:
    
    def __init__(self,logpath):
        
        self.logpath = logpath
        logfile = open(self.logpath,'a')
        
        print >> logfile,"***************************** log started at %s *****************************" %\
                (strftime(rfc822Time),)
        logfile.flush()
        logfile.close()
                
    def logger(self, msg):
        
        logfile = open(self.logpath,'a')
        print >> logfile, "%s : %s" % (strftime(rfc822Time),msg)
        logfile.flush()
        logfile.close()
        
class SimpleAuditor:
    
    def __init__(self,auditpath):
        
        self.auditpath = auditpath
        auditfile = open(self.auditpath,'a')
        
        print >> auditfile,"************************** audit log started at %s *************************" %\
                (strftime(rfc822Time),)
        auditfile.flush()
        auditfile.close()
                
    def auditor(self, msg):
        
        auditfile = open(self.auditpath,'a')
        print >> auditfile, "%s : %s" % (strftime(rfc822Time),msg)
        auditfile.flush()
        auditfile.close()
        
        