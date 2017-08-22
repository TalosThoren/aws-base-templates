#!/usr/bin/env python
#
#   Copyright 2017 David Hayden
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Imports from os.
from os import sys

# Imports from troposphere.
from troposphere import Template
from troposphere import Parameter
from troposphere import Ref
from troposphere import Select
from troposphere import GetAZs
from troposphere import GetAtt
import troposphere.ec2 as ec2

# Imports from argparse.
import argparse

# addVpc adds a vpc resource to the template.
def addVpc( template ):
    # Add VPC Parameters
    vpcCidrParam = template.add_parameter( Parameter(
        'vpcCidrBlock',
        Type = 'String',
        Description = 'The CIDR block for the VPC, we recommend a /16 bitmask for VPCs.',
        AllowedPattern = '(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})',
        ConstraintDescription = 'Must be a valide IP CIDR range: x.x.x.x/x.',
        Default = '10.0.0.0/16'
    ))
    vpcNameParam = template.add_parameter( Parameter(
        'vpcNameTag',
        Type = 'String',
        Description = 'A Name tag for your VPC.',
        Default = 'BaseNetworkVpc'
    ))
    # Add VPC to template
    vpc = ec2.VPC(
        'baseNetworkVpc',
        CidrBlock = Ref( vpcCidrParam ),
        Tags = [
            { 'Key': 'Name', 'Value': Ref( vpcNameParam ) }
        ]
    )
    template.add_resource( vpc )
    return vpc

# addSubnet adds a subnet resource to the template.
def addSubnet( template, vpc, subnetType, count, azNum):
    # Settings
    assignPubIp = 'false'
    if( subnetType == 'public' ):
        assignPubIp = 'true'
    # Add Subnet Parameters
    prefix = subnetType + 'Subnet' + str( count ) + 'Az' + str( azNum )
    subnetCidrParam = template.add_parameter( Parameter(
        prefix + 'CidrParam',
        Type = 'String',
        AllowedPattern = '(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})',
        ConstraintDescription = 'Must be a valide IP CIDR range: x.x.x.x/x.',
        Description = 'The CIDR block for the subnet. Must be within the VPC\'s CIDR range.'
    ))
    # Add Subnet to template
    subnet = ec2.Subnet(
        prefix,
        MapPublicIpOnLaunch = assignPubIp,
        AvailabilityZone = Select( azNum, GetAZs( '' ) ),
        VpcId = Ref( vpc ),
        CidrBlock = Ref( subnetCidrParam ),
    )
    template.add_resource( subnet )
    return subnet

# addInternetGateway adds an internet gateway resource to the template.
def addInternetGateway( template ):
    # Add Internet Gateway Parameters
    igwNameParam = template.add_parameter( Parameter(
        'igwNameTag',
        Type = 'String',
        Description = 'A Name tag for your Internet Gateway.',
        Default = 'BaseNetworkIgw'
    ))
    # Add Internet Gateway to template
    igw = ec2.InternetGateway(
        'baseNetworkIgw',
        Tags = [
            { 'Key': 'Name', 'Value': Ref( igwNameParam ) }
        ]
    )
    template.add_resource( igw )
    return igw


# addAssociation adds an association resource to the template.
def addAssociation( template, subnet, rtType, routeTable, count, azNum ):
    prefix = rtType + 'SubnetRouteTableAssociation' + str( count ) + 'Az' + str( azNum )
    subnetRouteTableAssociation = ec2.SubnetRouteTableAssociation(
        prefix,
        RouteTableId = Ref( routeTable ),
        SubnetId = Ref( subnet )
    )
    template.add_resource( subnetRouteTableAssociation )
    return subnetRouteTableAssociation

# addAttachment adds an attachment resource to the template.
def addAttachment( template, vpc, gw ):
    vpcAttachment = ''
    if( gw.resource_type == 'AWS::EC2::InternetGateway' ):
        vpcAttachment = ec2.VPCGatewayAttachment(
            'igwVpcAttachment',
            VpcId = Ref( vpc ),
            InternetGatewayId = Ref( gw )
        )
    elif( gw.resource_type == 'AWS::EC2::VPNGateway' ):
        vpcAttachment = ec2.VPCGatewayAttachment(
            'vpnVpcAttachment',
            VpcId = Ref( vpc ),
            VpnGatewayId = Ref( gw )
        )

    template.add_resource( vpcAttachment )
    return vpcAttachment

# addRouteTable adds a route table resource to the template.
def addRouteTable( template, vpc, rtType, count, azNum ):
    prefix = rtType + 'RouteTable' + str( count ) + 'Az' + str( azNum )
    # Add route table to template
    routeTable = ec2.RouteTable(
        prefix,
        VpcId = Ref( vpc ),
        Tags = [
            { 'Key': 'Name', 'Value': prefix }
        ]
    )
    template.add_resource( routeTable )
    return routeTable

# addRoute adds a route resource to the template.
def addRoute( template, routeTable, gw, count, azNum ):
    route = ''
    if( gw.resource_type == 'AWS::EC2::InternetGateway' ):
        prefix = 'publicRoute' + str( count ) + 'Az' + str( azNum )
        route = ec2.Route(
            prefix,
            GatewayId = Ref( gw ),
            RouteTableId = Ref( routeTable ),
            DestinationCidrBlock = '0.0.0.0/0'
        )
    elif( gw.resource_type == 'AWS::EC2::NatGateway' ):
        prefix = 'privateRoute' + str( count ) + 'Az' + str( azNum )
        route = ec2.Route(
            prefix,
            NatGatewayId = Ref( gw ),
            RouteTableId = Ref( routeTable ),
            DestinationCidrBlock = '0.0.0.0/0'
        )
    template.add_resource( route )
    return route

# addElasticIp adds an elastic IP (EIP or Eip) resource to the template.
def addElasticIp( template, vpc, count, azNum ):
    prefix = 'natEip' + str( count ) + 'Az' + str( azNum )
    eip = ec2.EIP(
        prefix,
        Domain = Ref( vpc )
    )
    template.add_resource( eip )
    return eip

# addNatGateway adds a NAT Gateway Resource to the template.
def addNatGateway( template, eip, subnet, count, azNum ):
    prefix = 'natGateway' + str( count ) + 'Az' + str( azNum )
    natGateway = ec2.NatGateway(
        prefix,
        AllocationId = GetAtt( eip, 'AllocationId' ),
        SubnetId = Ref( subnet )
    )
    template.add_resource( natGateway )
    return natGateway

# Control Function.
def main( cliArgs ):
    # Parse command line args
    parser = argparse.ArgumentParser( description='Generate a base vpc template.' )
    parser.add_argument( '--availability-zone-count',
        '-az',
        help = 'Number of Availability Zones to build in.',
        metavar = 'N',
        dest = 'azCount',
        default = '2',
        type = int
    )
    parser.add_argument( '--private-subnets-per-az',
        '-pr',
        help = 'Number of private subnets per Availability Zone.',
        metavar = 'N',
        dest = 'privSubnetCount',
        default = '1',
        type = int
    )
    parser.add_argument( '--public-subnets-per-az',
        '-pu',
        help = 'Number of public subnets per Availability Zone.',
        metavar = 'N',
        dest = 'pubSubnetCount',
        default = '1',
        type = int
    )
    options = parser.parse_args( cliArgs )
    # Instantiate template object.
    template = Template()
    # Add VPC resource to template.
    vpc = addVpc( template )
    # Add IGW resource to template.
    igw = addInternetGateway( template )
    # Attach IGW to VPC
    vpcAttachment = addAttachment( template, vpc, igw )

    # Create public subnets and associated resources
    azSentinel = 0
    subnetSentinel = 0
    natGatewayList = []
    while( azSentinel < options.azCount ):
        while( subnetSentinel < options.pubSubnetCount ):
            subnet = addSubnet( template, vpc, 'public', subnetSentinel, azSentinel )
            routeTable = addRouteTable( template, vpc, 'public', subnetSentinel, azSentinel )
            route = addRoute( template, routeTable, igw, subnetSentinel, azSentinel )
            subnetRouteTableAssociation = addAssociation( template, subnet, 'public', routeTable, subnetSentinel, azSentinel )
            if( 0 == subnetSentinel ):
                eip = addElasticIp( template, vpc, subnetSentinel, azSentinel )
                natGateway = addNatGateway( template, eip, subnet, subnetSentinel, azSentinel )
                natGatewayList.append( natGateway )
            subnetSentinel += 1
        subnetSentinel = 0
        azSentinel += 1

    # Create private subnets and associated resources
    azSentinel = 0
    subnetSentinel = 0
    while( azSentinel < options.azCount ):
        while( subnetSentinel < options.privSubnetCount ):
            subnet = addSubnet( template, vpc, 'private', subnetSentinel, azSentinel )
            routeTable = addRouteTable( template, vpc, 'private', subnetSentinel, azSentinel )
            route = addRoute( template, routeTable, natGatewayList[ azSentinel ], subnetSentinel, azSentinel )
            subnetRouteTableAssociation = addAssociation( template, subnet, 'private', routeTable, subnetSentinel, azSentinel )
            subnetSentinel += 1
        subnetSentinel = 0
        azSentinel += 1

    # Print template to stdout in json format.
    print( template.to_json() )

# Run main if called as a script directly.
if __name__ == "__main__":
    main( sys.argv[1:] )
