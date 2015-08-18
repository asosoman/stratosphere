# -*- coding: utf-8 -*-
from troposphere import rds, elasticache, ec2, autoscaling, sns, sqs, elasticloadbalancing, Template, Ref, Parameter, Join, route53, cloudwatch
from types import *
import logging
from logging import debug, info, warning
import csv
from troposphere.validators import boolean, integer
import xlrd
import sys
import os
import argparse
from decimal import Decimal

serveis = {
    'AS:LC' : autoscaling.LaunchConfiguration ,
    'AS:MC' : autoscaling.MetricsCollection,
    'AS:NC' : autoscaling.NotificationConfigurations,
    'SNS:T' : sns.Topic ,
    'SQS:Q' : sqs.Queue,
    'ELB:LB' : elasticloadbalancing.LoadBalancer,
    'AS:ASG' : autoscaling.AutoScalingGroup,
    'R53:RSG': route53.RecordSetGroup,
    'R53:HZ' : route53.HostedZone,
    'CW:A': cloudwatch.Alarm,
    'CW:MD': cloudwatch.MetricDimension,
    'AS:SP': autoscaling.ScalingPolicy,
    'AS:T': autoscaling.Tag,
    'EC2:T': ec2.Tag,
    'EC2:VPC': ec2.VPC,
    'EC2:S': ec2.Subnet,
    'EC2:IG': ec2.InternetGateway,
    'EC2:VGA': ec2.VPCGatewayAttachment,
    'EC2:RT': ec2.RouteTable,
    'EC2:R': ec2.Route,
    'EC2:SRTA': ec2.SubnetRouteTableAssociation,
    'EC2:NA': ec2.NetworkAcl,
    'EC2:NAE': ec2.NetworkAclEntry,
    'EC2:SNAA': ec2.SubnetNetworkAclAssociation,
    'RDS:DBSG': rds.DBSubnetGroup,
    'EC:SG': elasticache.SubnetGroup
    }

vars = {}
objectes = {}
params = {}
default = {}
for k in serveis.iterkeys():
    default[k] = {}
fitxer = []
headers = ""

t = Template()

def parse_args():
    parser = argparse.ArgumentParser(description="Process an xls into a CloudFront JSON file using Troposphere.")
    parser.add_argument("file", help="Name of xls file to open.")
    parser.add_argument("-sheet", help="Name of sheet to process.",default="")
    return parser.parse_args()

def change_params(texte):
    # Looks if the text is a parameter, in that case changes it to a Join or Ref.
    debug("Init Change Params "+str(texte))
    for par in params:
        if texte.find(par) <> -1:
            # We found a Parameter! Check if the parameter is all the text or only the first part.
            if len(par) < len(texte):
                if texte[len(par)] == "-":
                    rest = texte[len(par)+1:]
                    texte = Join("-", [Ref(objectes[par]),rest])
                else:
                    rest = texte[len(par):]
                    texte = Join("", [Ref(objectes[par]),rest])
            else:
                texte = Ref(objectes[par])
    debug("End Change Params "+str(texte))
    return texte

def crear_dict (row,headers):
    # Creates the dictionary of headers / values
    tmp_d = {}
    for x in range(len(headers)):
        if headers[x].strip() and str(row[x]).strip():
            try:
                tmp_d[headers[x].strip()] = str(int(float(row[x])))
            except ValueError:
                tmp_d[headers[x].strip()] = str(row[x]).strip()
    return tmp_d

def open_xls(filename):
    # Opens the sheet xls and gets the info needed to work
    if not os.path.isfile(filename):
        print "ERROR: File '{0}' not found.".format(filename)
        exit()
    return xlrd.open_workbook(filename)

def open_sheet(xls_book,sheet):
    fitxer = []
    if sheet == "": sheet = xls_book.sheet_names()[0]
    if sheet in xls_book.sheet_names():
        xls_sheet = xls_book.sheet_by_name(sheet)
        for x in range(xls_sheet.nrows):
            fitxer.append(xls_sheet.row_values(x))
    else:
        if sys._getframe(1).f_code.co_name == "process":
            print "ERROR: Include statement tries to add non existant sheet '{0}'".format(sheet)
            print "Try any of the following {0}".format(xls_book.sheet_names())
        else:
            print "ERROR: Non existant sheet '{0}' in {1}".format(sheet,args.file)
            print "Try any of the following {0}".format(xls_book.sheet_names())
        exit()
    return fitxer

def process(fitxer):
    #process the file and create the Troposphere template objects.
    for index, row in enumerate(fitxer):
        camp0 = row[0].strip()
        if camp0 == 'param':
            info('({idx}) Creating parameter {value}'.format(value=row[1],idx=index))
            d = crear_dict(row,headers)
            params[row[1]] = d
            objectes[row[1]] = t.add_parameter(Parameter(row[1],**d))
        elif camp0 == 'vars':
            info('({idx}) Creating variable: {value}'.format(value=row[1],idx=index))
            d = crear_dict(row,headers)
            for x in d:
                d[x] = change_params(d[x])
            vars[row[1]] = d.copy()
            debug('({idx}) Variable: {var} -> {value}'.format(var = row[1],value=vars[row[1]],idx=index))
        elif camp0 in serveis:
            info('({idx}) {value} in services'.format(value=row[0],idx=index))
            if row[0] in default:
                d = default[row[0]]
                d.update(crear_dict(row,headers))
            else:
                d = crear_dict(row,headers)
            for key in d:
                # Check the type of each key
                if key in serveis[row[0]].props:
                    info('({idx}) Creating {value} in {servei}'.format(servei=row[0],value=key,idx=index))
                    tipus_camp = serveis[row[0]].props[key][0]
                    if tipus_camp is integer:
                        debug('({idx}) {value} is Integer'.format(servei=row[0],value=key,idx=index))
                        # Validation on getting values. d[key] = float(d[key])
                    elif tipus_camp is boolean:
                        debug('({idx}) {value} is Boolean'.format(servei=row[0],value=key,idx=index))
                        #bool -> No hem de tocar res.
                        pass
                    elif tipus_camp is basestring:
                        debug('({idx}) {value} is Basestring'.format(servei=row[0],value=key,idx=index))
                        # comprobar els tres casos: OBJECTE (REF), variable (DICT) o texte directe.
                        if d[key] in objectes:
                            d[key] = Ref(d[key].strip())
                        elif d[key] in vars:
                            d[key] = vars[d[key]]
                        else:
                            #Comprobar si hi ha algún parametre global
                            d[key] = change_params(d[key])
                        debug('({idx}) {value} -> {final}'.format(final=d[key],value=key,idx=index))
                    elif tipus_camp is list:
                        debug('({idx}) {value} is List'.format(servei=row[0],value=key,idx=index))
                        # comprobar els tres casos: OBJECTE (REF), variable (DICT) o texte directe.
                        if d[key].split(',')[0] in objectes:
                            d[key] = [ Ref(x) for x in d[key].split(',')]
                        elif d[key].split(',')[0] in vars:
                            d[key] = [ vars[x] for x in d[key].split(',')]
                        else:
                            d[key] = [ x.strip() for x in d[key].split(',') ]
                        debug('({idx}) {value} -> {final}'.format(final=d[key],value=key,idx=index))
                    elif type(tipus_camp) is ListType:
                        tipus_camp2 = serveis[row[0]].props[key][0][0]
                        if tipus_camp2 is basestring:
                            debug('({idx}) {value} is ListType - Basestring'.format(servei=row[0],value=key,idx=index))
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
                elif key in ['DependsOn']:
                    d[key] = [ x.strip()  for x in d[key].split(',') ]
                else:
                    warning('({idx}) {key} dont exist in {value}'.format(key=key,value=row[0],idx=index))
            instancia = serveis[row[0]](row[1],**d)
            objectes[row[1]] = instancia
            try:
                if serveis[row[0]].resource_type:
                    t.add_resource(instancia)
            except:
                pass
        elif camp0 == "":
            print row
            if "".join(row).strip() == "":
                info('({idx}) Blank line'.format(idx=index))
            else:
                headers = row
                info('({idx}) Header'.format(idx=index))
        elif camp0 == "default":
            d = crear_dict(row,headers)
            default[row[1]].update(d)
        elif camp0 == "#":
            info('({idx}) Comment'.format(idx=index))
        elif camp0 == "include":
            fitxer = open_sheet(xls_file,row[1])
            process(fitxer)
        else:
            warning('({idx}) {value} is not found in any valid value.'.format(value=row[0],idx=index))

if __name__ == "__main__":
    args = parse_args()
    logname = sys.argv[0]+'.log'
    with open(logname, 'w'):
        pass
    logging.basicConfig(format='%(levelname)s:%(message)s',filename=logname,level=logging.DEBUG)
    xls_file = open_xls(args.file)
    fitxer = open_sheet(xls_file,args.sheet)
    process(fitxer)
    print t.to_json()
