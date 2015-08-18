# -*- coding: utf-8 -*-
from troposphere import autoscaling, sns, sqs, elasticloadbalancing, Template, Ref, Parameter, Join
from types import *
import logging
from logging import debug, info, warning
import csv
from troposphere.validators import boolean, integer

with open('cfv2.log', 'w'):
    pass
logging.basicConfig(format='%(levelname)s:%(message)s',filename='cfv2.log',level=logging.DEBUG)

serveis = {
    'AS:LC' : autoscaling.LaunchConfiguration ,
    'AS:MC' : autoscaling.MetricsCollection,
    'SNS:T' : sns.Topic ,
    'SQS:Q' : sqs.Queue,
    'ELB:LB' : elasticloadbalancing.LoadBalancer,
    'AS:ASG' : autoscaling.AutoScalingGroup
    }
vars = {}
objectes = {}
params = {}
fitxer = []
headers = ""
t = Template()

def crear_dict (row,headers):
    tmp_d = {}
    for x in range(len(headers)):
        if headers[x].strip() and row[x].strip():
            tmp_d[headers[x].strip()] = row[x].strip()
    return tmp_d

with open('WP-env.csv', 'rb') as csvfile:
     fitxer_temp = csv.reader(csvfile, delimiter=',', quotechar='"')
     for x in fitxer_temp: fitxer.append(x)

for index, row in enumerate(fitxer):
    camp0 = row[0].strip()
    if camp0 == 'param':
        info('({idx}) Creant parametre {value}'.format(value=row[1],idx=index))
        d = crear_dict(row,headers)
        params[row[1]] = d
        objectes[row[1]] = t.add_parameter(Parameter(row[1],**d))
    elif camp0 == 'vars':
        info('({idx}) Creant variable: {value}'.format(value=row[1],idx=index))
        vars[row[1]] = crear_dict(row,headers)
        debug('({idx}) Variable: {var} -> {value}'.format(var = row[1],value=vars[row[1]],idx=index))
    elif camp0 in serveis:
        info('({idx}) {value} en serveis'.format(value=row[0],idx=index))
        d = crear_dict(row,headers)
        for key in d:
            # mirar el tipus de camp que ens demana per cada una de les keys i adaptarlo segons necessitat.
            if key in serveis[row[0]].props:
                info('({idx}) Creant {value} en {servei}'.format(servei=row[0],value=key,idx=index))
                tipus_camp = serveis[row[0]].props[key][0]
                if tipus_camp is integer:
                    debug('({idx}) {value} es Integer'.format(servei=row[0],value=key,idx=index))
                    #integer -> No hem de tocar res.
                    pass
                elif tipus_camp is boolean:
                    debug('({idx}) {value} es Boolean'.format(servei=row[0],value=key,idx=index))
                    #bool -> No hem de tocar res.
                    pass
                elif tipus_camp is basestring:
                    debug('({idx}) {value} es Basestring'.format(servei=row[0],value=key,idx=index))
                    # comprobar els tres casos: OBJECTE (REF), variable (DICT) o texte directe.
                    if d[key] in objectes:
                        d[key] = Ref(d[key].strip())
                    elif d[key] in vars:
                        d[key] = vars[d[key]]
                    else:
                        #Comprobar si hi ha algún parametre global
                        for par in params:
                            if d[key].find(par) <> -1:
                                # Si trobem un parametre al texte que hi ha.
                                print index, "TROBAT PARAM", par
                                if len(par) < len(d[key]):
                                    if d[key][len(par)+1] == "-":
                                        texte = d[key][len(par)+1:]
                                    else:
                                        texte = d[key][len(par):]
                                d[key] = Join("-", [Ref(objectes[par]),texte])


                    debug('({idx}) {value} -> {final}'.format(final=d[key],value=key,idx=index))
                elif tipus_camp is list:
                    debug('({idx}) {value} es List'.format(servei=row[0],value=key,idx=index))
                    # comprobar els tres casos: OBJECTE (REF), variable (DICT) o texte directe.
                    if d[key].split(',')[0] in objectes:
                        d[key] = [ Ref(x) for x in d[key].split(',')]
                    elif d[key].split(',')[0] in vars:
                        d[key] = [ vars[x] for x in d[key].split(',')]
                    else:
                        d[key] = [ d[key]]
                    debug('({idx}) {value} -> {final}'.format(final=d[key],value=key,idx=index))
                elif type(tipus_camp) is ListType:
                    tipus_camp2 = serveis[row[0]].props[key][0][0]
                    if tipus_camp2 is basestring:
                        debug('({idx}) {value} es ListType - Basestring'.format(servei=row[0],value=key,idx=index))
                        if d[key].split(',')[0] in objectes:
                            d[key] = [ Ref(x) for x in d[key].split(',')]
                        elif d[key].split(',')[0] in vars:
                            d[key] = [ vars[x] for x in d[key].split(',')]
                        else:
                            d[key] = [d[key]]
                    else:
                        #Serà crear la llista d'objectes
                        if d[key].split(',')[0] in objectes:
                            d[key] = [objectes[x] for x in d[key].split(',')]
                        else:
                            d[key] = [tipus_camp2(x,**vars[x]) for x in d[key].split(',')]
                    debug('({idx}) {value} -> {final}'.format(final=d[key],value=key,idx=index))
            else:
                warning('({idx}) {key} no existeix a {value}'.format(key=key,value=row[0],idx=index))
        instancia = serveis[row[0]](row[1],**d)
        objectes[row[1]] = instancia
        t.add_resource(instancia)
    elif camp0 == "":
        if "".join(row).strip() == "":
            info('({idx}) Linia en blanc'.format(idx=index))
        else:
            headers = row
            info('({idx}) Capçaleres'.format(idx=index))
    elif camp0 == "#":
        info('({idx}) Comentari'.format(idx=index))
        pass
    else:
        warning('({idx}) {value} no es res'.format(value=row[0],idx=index))

print t.to_json()
