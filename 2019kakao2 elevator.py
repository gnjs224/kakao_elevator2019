
import requests
import json
import copy
import time
url= "http://localhost:8000"

def start(user, problem, num):
    return requests.post(url+"/start/"+str(user)+"/"+str(problem)+"/"+str(num)).json()
def oncalls(token):
    return requests.get(url+"/oncalls",headers={"X-Auth-Token":token}).json()
def action(token,commands):
    return requests.post(url+"/action",headers={"X-Auth-Token":token},json={"commands":commands}).json()

s1 = start("tester",2,4)
token = s1['token']
calls = oncalls(token)['calls']
a=calls
print(calls)
evdir=[[0,[],[]] for _ in range(4)]
count=0
end=False
while not end:
    oncall = oncalls(token)
#     print("\n\n\n=========================timestamp 증가=========================\n")
    still=[]
    for i in range(4):
        for evd in evdir[i][2]:
            still.append(evd)
    calls = oncall['calls']
#     print("\ncalls",calls)
    elevators = oncall['elevators']
    for call in calls:
        choose=-1
        m2 = float("inf")
        newdir = []
        if call['id'] in still:
            still.remove(call['id'])
            continue
        for idx in range(4):
            e = elevators[idx]
            if len(e['passengers'])==8 or len(evdir[idx][2]) > 7:
                continue
            for i in range(len(evdir[idx][1])+1):
                for j in range(0,len(evdir[idx][1])+1):
                    if j+i+1< len(evdir[idx][1])+2:
                        evdir[idx][1].insert(j,call['start'])
                        evdir[idx][1].insert(j+i+1,call['end'])
                        tempdir=[]
                        d=abs(e['floor']-evdir[idx][1][0])
                        l = len(evdir[idx][1])
                        for k in range(l-1):
                            interval = abs(evdir[idx][1][k]-evdir[idx][1][k+1])
                            d+=interval
                            if interval:
                                tempdir.append(evdir[idx][1][k])
                        tempdir.append(evdir[idx][1][l-1])
                        d+=len(tempdir)*3-1
                        exit = False
                        enter = False
                        manin = []
                        currentfloor = e['floor']
                        for p in e['passengers']:
                            manin.append(p['id'])
                            if p['end']==currentfloor:
                                exit=True
                                break
                        for call2 in calls:
                            if call2['id'] in evdir[idx][2] and not call2['id'] in manin:
                                if currentfloor == call2['start']:
                                    enter = True
                                    break

                        if e['status'] == 'STOPPED':
                            if enter or exit:
                                d+=2
                                if enter:
                                    d+=1
                                if exit:
                                    d+=1
                        if e['status'] == 'OPENED':
                            d+=1
                            if enter:
                                d+=1
                            if exit:
                                d+=1
                        if m2>d:
                            choose=idx
                            m2=d
                            newdir = copy.deepcopy(tempdir)
                        evdir[idx][1].pop(j)
                        evdir[idx][1].pop(j+i)
        if choose!=-1:
            evdir[choose][1] = copy.deepcopy(newdir)
            evdir[choose][2].append(call['id'])

    commands = [{"elevator_id": i,"command": "STOP"} for i in range(4)]

    for i in range(4):
        c = 'STOP'
        currentfloor = elevators[i]['floor']
        currentstatus = elevators[i]['status']
        exitlist=[]
        manin = []
        for p in elevators[i]['passengers']:
            manin.append(p['id'])
            if p['end']==currentfloor:
                exitlist.append(p['id'])
        enterlist=[]
        
        calllist=[]
        for call in calls:
            if call['start']==currentfloor:
                calllist.append(call['id'])
        for ed in evdir[i][2]:
            if ed in calllist:
                enterlist.append(ed)
        if len(enterlist)+len(elevators[i]['passengers'])>8:
            out = len(enterlist)+len(elevators[i]['passengers'])-8
            table = []
            for ent in enterlist:
                for call in calls:
                    if call['id']==ent:
                        table.append([ent,abs(call['start']-call['end'])])
                        break
            table.sort(key=lambda x:x[1])
            for idx in range(out):
                enterlist.remove(table[idx][0])
                evdir[i][2].remove(table[idx][0])        

        if currentstatus=='STOPPED':
            if evdir[i][1]:
                if exitlist or enterlist:
                    c='OPEN'
                else:
                    if evdir[i][1][0] > currentfloor:
                        c='UP'
                    elif evdir[i][1][0] < currentfloor:
                        c='DOWN'
                if  evdir[i][1][0] == currentfloor:
                    evdir[i][1].pop(0)
        elif currentstatus=='OPENED':
            if exitlist:
                c='EXIT'
                commands[i]['call_ids']=copy.deepcopy(exitlist)
                count+=len(exitlist)
#                 print("exit전")
#                 print("evdir[i][2]: ", evdir[i][2])
#                 print("exitlist", exitlist)
                for aa in reversed(exitlist):
                    if aa in evdir[i][2]:
                        evdir[i][2].remove(aa)
                        exitlist.remove(aa)
#                 print("exit후")
#                 print("evdir[i][2]: ", evdir[i][2])
#                 print("exitlist", exitlist)
            elif enterlist:
                c='ENTER'
                commands[i]['call_ids']=copy.deepcopy(enterlist)
            else:
                c='CLOSE'
        elif currentstatus=='UPWARD':
            if  evdir[i][1][0] > currentfloor:
                c='UP'
        else:
            if  evdir[i][1][0] < currentfloor:
                c='DOWN'
        commands[i]['command']=c
    a = action(token,commands)
#     print("\n\n액션 후 엘리베이터 상태")
#     for aaa in a['elevators']:
#         print("\n",aaa)   
#     print("\n\ncommands", commands)
#     print("\n=============================================================\n")
    end = a['is_end']
#     print("call처리수: ", count, "타임스탬프: ", a['timestamp'])




