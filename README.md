# Base CloudFormation Template Repository

# Description

This is our collection of generic, base CloudFormation templates. The files
you'll find here are intended to genericize common infrastructure components.

It is the goal of this repository to either supply templates or a way to
generate modular templating of infrastructure components, to ease the burden of
design and build when standing up new footprints in Amazon Web Services.

Templates supplied here may make certain assumptions or enforce certain
standards that should be checked against the needs of your organization prior to
use. Where applicable, the authors will strive to document such choices and why
those choices were made.

## Common Components

- VPC and Subnets
- Security Groups
- Auto-Scale Groups
- DBaaS
- Route53 and Domains
- Cloudwatch Alarms
- Dashboards
- Log Aggregation
- Code Delivery/Deployment

This is a living list; it may grow at any time. It is not necessarily the goal
of this repository to cover every common component or component group on the
list. Some common components may not be supported by or fully exposed through
CloudFormation, and some may simply not be able to be genericized in a portable
way.
