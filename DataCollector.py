import praw
import threading
import time
import os
import json
from config import *
class DataCollector(threading.Thread):
    def __init__(self,client_secret,client_id,user_agent,folder="Data",wait=21600,sub="jailbreak",mod_message="has been removed"):
        threading.Thread.__init__(self)
        self.client_secret=client_secret
        self.client_id=client_id
        self.user_agent=user_agent
        self.r=self.new_reddit()
        self.sub=self.r.subreddit(sub)
        self.mod_message=mod_message
        self.folder=folder
        self.wait=wait
        self.to_check=[]
        if os.path.exists(folder+"/to_check.json"):
            with open(folder+"/to_check.json") as f:
                self.to_check=json.loads(f.read())
        self.deleted=[]
        self.survived=[]
        self.del_no_reply=[]
        self.last={"comment":list(self.sub.comments(limit=1))[0].created,
                   "submission":list(self.sub.new(limit=1))[0].created} #Get timestamps for newest comment and submission so that we only grab the new ones
        self.alive=True
        self.get_c=threading.Thread(target=self.get_comments)
        self.get_s=threading.Thread(target=self.get_submissions)
        self.process=threading.Thread(target=self.process_data)
        self.get_c.start()
        self.get_s.start()
        self.process.start()
        self.start()
    def run(self):
        last=0
        while self.alive:
            try:
                if self.to_check[-1]["created"]>last:
                    with open(self.folder+"/to_check.json","w") as f:
                        stuff=json.dumps(self.to_check,indent=2,sort_keys=True) #Make sure the json looks pretty for my stupid human eyes
                        f.write(stuff)
                    last=self.to_check[-1]["created"]
            except IndexError:
                pass
            #The next three for loops won't save things in proper json format because it won't have brackets at the ends and will have a hanging comma at the end
            #It was done this way so that it wouldn't have to read the whole file and then write it all again because the file will get big
            #It wasn't done with to_check because items in it need to be removed, which would be tricky and probably not worth it to do efficiently if it weren't in proper json format
            for t in self.deleted:
                with open(self.folder+"/deleted.json","a") as f:
                    f.write(json.dumps(t,indent=2,sort_keys=True)+",\n")
            self.deleted=[]
            for t in self.survived:
                with open(self.folder+"/survived.json","a") as f:
                    f.write(json.dumps(t,indent=2,sort_keys=True)+",\n")
            self.survived=[]
            for t in self.del_no_reply:
                with open(self.folder+"/del_no_reply.json","a") as f:
                    f.write(json.dumps(t,indent=2,sort_keys=True)+",\n")
            self.del_no_reply=[]
    def get_comments(self):
        while self.alive:
            try:
                for c in self.sub.stream.comments():
                    if c.created>self.last["comment"]:
                        data=DataCollector.organize_data(c)
                        self.to_check.append(data)
                        print("Appended "+c.fullname+" to to_check")
                    if not self.alive:
                        break
            except Exception as e: #If Reddit session stops working for whatever reason, renew it
                print(str(e))
                self.r=self.new_reddit()
    def get_submissions(self):
        while self.alive:
            try:
                for s in self.sub.stream.submissions():
                    if s.created>self.last["submission"]:
                        data=DataCollector.organize_data(s)
                        self.to_check.append(data)
                        print("Appended "+s.fullname+" to to_check")
                    if not self.alive:
                        break
            except Exception as e: #If Reddit session stops working for whatever reason, renew it
                print(str(e))
                self.r=self.new_reddit()
    def process_data(self):
        while self.alive:
            try:
                for i in self.to_check:
                    if i["fullname"][1]=="1":
                        comment=True
                        t=self.r.comment(i["fullname"][3:])
                        try:
                            t.refresh()
                        except: #If there was an exception, the comment was deleted by the author
                            self.del_no_reply.append(i)
                            print("Appended "+i["fullname"]+" to del_no_reply")
                            self.to_check.remove(i)
                            continue
                    else:
                        comment=False
                        t=self.r.submission(i["fullname"][3:])
                    deleted=False
                    try:
                        if comment:
                            replies=t.replies
                        else:
                            replies=t.comments
                    except: #If there was an exception, the object has no replies/comments
                        replies=None
                    if replies:
                        replies.replace_more(limit=None)
                        for c in replies:
                            if self.mod_message in c.body and c.distinguished: #If a moderator replies with the standard message when something has been removed
                                temp=i
                                temp["score"]=t.score
                                temp["mod_reply"]=DataCollector.organize_data(c)
                                self.deleted.append(temp)
                                deleted=True
                                print("Appended "+i["fullname"]+" to deleted")
                                self.to_check.remove(temp)
                                break
                    if deleted:
                        continue
                    if not comment and t.selftext=="[deleted]":
                        self.del_no_reply.append(i)
                        print("Appended "+i["fullname"]+" to del_no_reply")
                        
                    else:
                        if time.time()-i["accessed"]<self.wait: #If not enough time has passed to be confident that the comment won't be deleted. It's 6 hours by default
                            continue
                        temp=i
                        temp["score"]=t.score
                        self.survived.append(temp)
                        print("Appended "+i["fullname"]+" to survived")
                    self.to_check.remove(i)
            except Exception as e: #If Reddit session stops working for whatever reason, renew it
                print(str(e))
                self.r=self.new_reddit()
    def kill(self): #Will stop all threads
        self.alive=False
    def new_reddit(self):
        return praw.Reddit(client_secret=self.client_secret,client_id=self.client_id,user_agent=self.user_agent)
    @staticmethod
    def organize_data(t): #Returns a dictionary of all the important bits of a comment/submission
        try:
            temp={}
            temp["accessed"]=time.time()
            temp["fullname"]=t.fullname
            temp["created"]=t.created
            temp["author"]=t.author.name
            if type(t)==praw.models.Comment:
                temp["content"]=t.body
            elif type(t)==praw.models.Submission:
                temp["title"]=t.title
                if t.url=="https://www.reddit.com"+t.permalink:
                        content=t.selftext
                else:
                    content=t.url
                temp["content"]=content
            return temp
        except AttributeError:
            raise TypeError("Input must either be a Comment or Submission")
if __name__=="__main__":
    if not os.path.exists("Data"):
        os.mkdir("Data")
    collector=DataCollector(client_secret=rsecret,client_id=rid,user_agent=ua)
