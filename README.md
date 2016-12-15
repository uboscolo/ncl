ncl
===

The new Champions' league

A python implementation of my view of the Champions' league 

===

To start the simualtion use:
 ncl.py <xml_file>

Conferences, divisions and teams are imported by reading the xml file, an even number of conferences, divisions and teams is expected
Each team is assigned a strength which is based on their participation to 11 years of Champions' league (from 2003 to 2014) 
 [enhancement update with more recent results]
Strenghts are assigned this way:
 - if ended up in the top 32 teams get 1 point unless
 - if ended up in the top 16 teams get 2 points unless
 - if ended up in the top 8 teams get 4 points unless
 - if ended up in the top 4 teams get 8 points unless
 - if ended up in the top 2 teams (final) get 16 points
 - normalize points to total points assigned
Team strengths are losely used during match simulation


