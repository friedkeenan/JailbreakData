import json
import os
import datetime as dt
import matplotlib.pyplot as plt
data={}
for file in os.listdir("Data"): #Put each data file into a dictionary so you can just do `data["deleted"]` instead of getting the data each time
    with open("Data/"+file) as f:
        data[file[:-5]]=json.loads(f.read())
def plot_mod_proportion():
    mods=[]
    num_deleted=[]
    for t in data["deleted"]:
        m=t["mod_reply"]["author"]
        if m not in mods:
            mods.append(m)
            num_deleted.append(0)
        num_deleted[mods.index(m)]+=1
    plt.pie(num_deleted,
            labels=mods,
            startangle=90,
            explode=[0.05]*len(num_deleted),
            autopct=lambda x:int(round(x*len(data["deleted"])/100)))
    plt.title("Number of Things Deleted by Each Moderator",color="b")
    plt.show()
def plot_reason_proportion():
    reasons=[]
    num_deleted=[]
    for t in data["deleted"]:
        r=t["mod_reply"]["content"]
        if t["mod_reply"]["author"]!="AutoModerator":
            if "not jailbreak related" in r.lower(): #Put this in to deal with peculiarities
                r={"Not jailbreak related"}
            elif "duplicate" in r.lower():
                r={"Duplicate"}
            else:
                r=r.split("**")
                r=[r[x] for x in range(1,len(r),2)]
                if len(r)>1 and r[1]=="No misleading or sensationalized titles. Titles should be detailed and descriptive.": #Had to put this in because of Hipp013's slightly malformed notice
                    r=r[:-1]
                if r==[]: #For ones that don't fit nicely into the rules or were malformed
                    r=["Other"]
                r=set(r)
        else:
            if "correct tag" in r:
                r={"Incorrect tag"}
            elif "minimum posting requirements" in r:
                r={"Under Required"}
        for reas in r:
            if reas not in reasons:
                reasons.append(reas)
                num_deleted.append(0)
            num_deleted[reasons.index(reas)]+=1
    #Next few lines are to stop stuff from overlapping
    i=reasons.index("Rule 2")
    v=num_deleted[i]
    reasons[i]=reasons[-3]
    num_deleted[i]=num_deleted[-3]
    reasons[-3]="Rule 2"
    num_deleted[-3]=v
    i=reasons.index("Under Required")
    v=num_deleted[i]
    reasons[i]=reasons[2]
    num_deleted[i]=num_deleted[2]
    reasons[2]="Under Required"
    num_deleted[2]=v
    plt.pie(num_deleted,
            labels=reasons,
            startangle=90,
            explode=[0.05]*len(num_deleted),
            autopct=lambda x:int(round(x*len(data["deleted"])/100)))
    plt.title("Number of Times Something was Deleted for a Reason",color="b")
    plt.show()
def plot_time_deleted():
    hours=list(range(24))
    num_deleted=[0 for x in range(24)]
    for t in data["deleted"]:
        num_deleted[int(dt.datetime.fromtimestamp(t["mod_reply"]["created"]).strftime("%H"))]+=1 #Get hour from timestamp
    plt.bar(hours,num_deleted)
    plt.xlabel("Hour of the day")
    plt.ylabel("Number of deleted items")
    plt.title("How Many Items were Deleted in Each Hour")
    plt.show()
def plot_time_amount():
    hours=list(range(24))
    num={"comments":[0 for x in range(24)],
         "submissions":[0 for x in range(24)]}
    for t in data["survived"]:
        index=int(dt.datetime.fromtimestamp(t["created"]).strftime("%H")) #Get hour from timestamp
        if t["fullname"].startswith("t1_"):
            num["comments"][index]+=1
        else:
            num["submissions"][index]+=1
    plt.bar(hours,num["comments"])
    plt.xlabel("Hour of the day")
    plt.ylabel("Amount")
    plt.title("Amount of Comments in Each Hour")
    plt.show()
    plt.bar(hours,num["submissions"])
    plt.xlabel("Hour of the day")
    plt.ylabel("Amount")
    plt.title("Amount of Submissions in Each Hour")
    plt.show()
def plot_deleted_survived():
    _,_,txts=plt.pie([len(data["deleted"]),len(data["survived"])],
            labels=["Deleted","Survived"],
            startangle=90,
            autopct=lambda x:int(round(x*(len(data["deleted"])+len(data["survived"]))/100)))
    for txt in txts:
        txt.set_color("w")
    plt.title("Amount of Deleted Items vs. Survived Items")
    plt.show()
def get_avg_surv_score():
    comm={"score":0,"num":0}
    sub={"score":0,"num":0}
    for t in data["survived"]:
        if t["fullname"].startswith("t1_"):
            comm["score"]+=t["score"]
            comm["num"]+=1
        else:
            sub["score"]+=t["score"]
            sub["num"]+=1
    avg_score={"comments":comm["score"]/comm["num"],
               "submissions":sub["score"]/sub["num"]}
    print(avg_score)
def get_avg_del_score():
    comm={"score":0,"num":0}
    sub={"score":0,"num":0}
    for t in data["deleted"]:
        if t["fullname"].startswith("t1_"):
            comm["score"]+=t["score"]
            comm["num"]+=1
        else:
            sub["score"]+=t["score"]
            sub["num"]+=1
    avg_score={"comments":comm["score"]/comm["num"],
               "submissions":sub["score"]/sub["num"]}
    print(avg_score)
