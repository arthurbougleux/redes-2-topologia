import itertools
import math
import pygraphviz as pg
import pycountry as pc
from subprocess import *
import os
import pathlib

colors = {

    "AU":"navy:red:navy",
    "BR":"springgreen4:yellow:springgreen4",
    "CA":"red2:white:red2",
    "CN":"red2:yellow:yellow:red2",
    "CO":"yellow:navy:red",
    "EC":"yellow:brown:navy:red:",
    "GB":"navy:white:red:white:navy",
    "IT":"green:white:red",
    "JP":"white:red:white",
    "RU":"white:navy:red",
    "UY":"white:yellow:white:blue:white",
    "VE":"yellow:navy:white:navy:red",
    "ZA":"red:white:springgreen4:yellow:springgreen4:white:blue"
}

home = "Home"

def parse_route(route):

    resp = []

    route.pop(0)

    for r in route:

        r = r.split()[1:]
        ips = []

        times = []
        while len(r):

            i = r.pop()

            if i == "ms":

                times.append(float(r.pop()))

            if i.startswith("("):

                ips.append([i.strip("()"), times.copy()])
                times = []
            
        resp.append(ips)

    return resp

def who_are_ya(ip):

    org_name = country = False

    out = run(["whois", ip], text=True, stdout=PIPE).stdout
    out = list(map(lambda x: x.upper(), out.split("\n")))

    org_name = list(filter(lambda x: x.upper().startswith("ORGNAME"), out))
    country = list(filter(lambda x: x.upper().startswith("COUNTRY"), out))

    if len(org_name):
        org_name = org_name[0]
    if len(country):
        country = country[0]

    return org_name, country




g = pg.AGraph(directed=True, bgcolor="seashell")
g.add_node(home)
cluster = {}

for file in os.listdir(pathlib.Path().resolve()):

    if not file.endswith(".link"):
        continue

    cod = file[0:-5].upper()
    target = pc.countries.get(alpha_2=cod)

    f = open(file)

    for l in f:

        url = l.split()[1][8:]
        #print(url)

        route = run(["traceroute", url], text=True, stdout=PIPE).stdout

        #print(route)
        route = parse_route(route.split("\n"))
        #for l in route:
            #print(l)

        for r in route:          

            for router in r:

                ip = router[0]

                org_name, country = who_are_ya(ip)

                label = ip
                if org_name:
                    label = " ".join(org_name.split()[1:])

                if country:

                    country = country.split()[1]

                    if not country in cluster.keys():
                        cluster[country] = []

                    cluster[country].append(ip)
                
                
                g.add_node(ip, label=label)
            
            if len(route[0]):
                g.add_edge("Home", route[0][0][0], color=colors[cod])

            for ant, suc in itertools.pairwise(route):

                if ant == [] or suc == []:
                    continue

                for r1 in ant:

                    ip1 = r1[0]
                    avg1 = sum(r1[1])/len(r1[1])

                    for r2 in suc:

                        ip2 = r2[0]

                        avg2 = sum(r2[1])/len(r2[1])
                        avg = avg2-avg1

                        if avg <= 0:
                            avg = 0.001

                        #Usando log pra distância não ficar ridícula mas ainda crescer
                        g.add_edge(ip1, ip2, color=colors[cod], minlen=math.log(avg))

    f.close()


#print(cluster)
for country, nodes in cluster.items():
    #print(country)
    #print(nodes)

    label = pc.countries.get(alpha_2=country).name
    g.add_subgraph(cluster[country], "cluster_"+country, color="springgreen4", label=label)

g.write("out.dot")


