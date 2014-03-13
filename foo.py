#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytagcloud import create_tag_image, make_tags
from pytagcloud.lang.counter import get_tag_counts
 
TEXT = '''
Why is Free/Libre Software Important to Education?


The Expanding Role of Computing in Education

In a 2009-10 study in Montevideo, primary-school students used computers not just for playing games, but also for reading, writing, chatting, making music and videos, drawing, searching for information, and programming. They played -- they are children after all -- but they also used computation as a tool for communication -- “a thing with which to be social and expressive ” -- and problem-solving -- “a thing to think with”. Skills that they will be able to draw upon not just in school but in life.

How did this happen and how do we further promote and sustain it?


The True Cost of Proprietary Software

Change is the one thing that is consistent in computing. Most of the knowledge of IT taught in primary and middle schools some years ago is completely deprecated due to rapid changes in software and devices. This necessitates that software, knowledge and techniques should be updated frequently. 

A frequently cited reason for using Free/Libre Software is that is it free: upgrades are available at no cost. It is true that Free Software allows schools to free themselves of the costs associated with proprietary software and reduce the dependence of software vendor. However, cost savings is a Red Herring: there are maintenance costs associated with all software, regardless of whether or not one has to pay a licensing fee. (One upside to Free/Libre Software is that the investment you make in maintenance can be used as a source of nurturing local talent.)

The hidden cost of proprietary software is more insidious: it takes away from the user the opportunity to achieve autonomy, mastery, and a sense of purpose. In the context of school, it channels education into consumption, passivity, and acceptance. Free/Libre Software, on the other hand, focuses the student on creativity, activity, and intellectual risk taking. The student (and teacher) has the license to learn and, when properly staged, provides the means to leverage the opportunities afforded by the license.


A Culture of Autonomy and Responsibility

The “free” in Free/Libre Software refers to freedom. Users have the license to use, share or modify it according to their needs. The reality is that even for small software companies, an individual school or classroom is too small of a market to consider important. With Free/Libre Software, you don’t have to depend on third parties to do things for you. You are empowered to shape the tools to meet your own needs. It is only way to be freed from external dependencies. (Because your can share Free/Libre Software, you need not act alone: you can work within a community; communities arise where ever Free/Libre Software is used and are often global in reach). With autonomy comes responsibility: thus the culture of Free/Libre Software is a culture of individualism coupled with personal and communal responsibility. Not bad traits to instill in our children.


The Means of Mastery

With Free/Libre Software there is an increased opportunity to provide direct feedback between users and developers since there is no reason to build a “firewall” between them. This means that learners and educators can collaborate together with software developers in the design of educational software and create software which fits better in classrooms. A common forum for this interaction is “chat”. Many Free/Libre Software projects use open chat-rooms as a place for developers to discuss their work. Anyone is welcome to “listen” as domain experts openly discuss the problems with which they are wrestling. 

The interaction between learners and domain experts makes possible the transition from a learner to a software developer and become a contributor of a Free/Libre Software project. The Free/Libre Software community is a meritocracy: all that matters is what you do, not who you are. So there is room for personal growth. There is an open door to mastery within Free/Libre Software that is usually closed with proprietary software. Free/Libre software gives everyone the opportunity to be both a learner and a teacher.


A Sense of Purpose

Nothing motivates learning more than a sense of purpose. Neither carrots or sticks come close. Free/Libre Software gives the learner the opportunity to “scratch an itch” -- to pursue a problem of passion and purpose. It is while engaging in authentic problem-solving where one acquires the problem-solving skills that transfer across domains and are applicable beyond the walls of the classroom.

Within the Free/Libre Software community, we do not passively accept the status quo as inevitable, but actively embark upon making things better. Instilling that habit of mind in the next generation is perhaps the most valuable contribution Free/Libre Software makes to Education.


A Call to Action

The cultivation of Free/Libre Software in education doesn’t happen on its own. The proprietary software industry will fight to maintain a model of schools and learners as consumers. We need to protect our freedom to create. It is our responsibility. It won’t be done for us. If we don’t invest in the next generation of leadership, we will be overwhelmed.

The Free/Libre Software movement needs to foster growth and leadership among the next generation. We need to provide both the license and the means to exercise this license.

The next generation might have reasons to spread the Free/Libre Software culture, because they will be educated in that way. The most important factors are the deployment of Free/Libre Software in classrooms and the existence of an open community that facilitates feedback with schools.
'''
 
tags = make_tags(get_tag_counts(TEXT), maxsize=150)
 
create_tag_image(tags, 'cloud_large.png', size=(900, 600))
