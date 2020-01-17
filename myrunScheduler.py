# -*- coding: utf-8 -*-
import module
import tutor
import ReaderWriter
import timetable
import scheduler
import random

# RANDOM = True
RANDOM = True
def pause(p = ""):
	print(scheduler.format_table(tt))
	print(str(tt.schedule))
	if tt.scheduleChecker(tutorList, moduleList):
		print("Schedule is legal.")
		print("Schedule has a cost of " + str(tt.cost))
		print(str(tt.schedule))
	while p != "y":
		p = input("Proceed? (y/n) ")



rw = ReaderWriter.ReaderWriter()

r = random.Random()
if RANDOM:
	prob = "ExampleProblems/Problem{0}.txt".format(r.choice(range(1,9)))
	[tutorList, moduleList] = rw.readRequirements(prob)
	r.shuffle(tutorList)
	r.shuffle(moduleList)
else:
	prob = "ExampleProblems/Problem1.txt"
	[tutorList, moduleList] = rw.readRequirements(prob)
sch = scheduler.Scheduler(tutorList, moduleList)


# this method will be used to create a schedule that solves task 1
tt = sch.createSchedule()
pause()

# This method will be used to create a schedule that solves task 2
tt = sch.createLabSchedule()
pause()

#this method will be used to create a schedule that solves task 3
tt = sch.createMinCostSchedule()
pause()


# pause()