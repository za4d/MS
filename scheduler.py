# -*- coding: utf-8 -*-

import module
import tutor
import ReaderWriter
import timetable
import random
import math

# TODO!!!! COMMENTS
# TODO!!!! CLEAN
# TODO !!! Convert tabs to spaces

def format_table(time_table):
    str_tab = '_' * 200 + '\n'

    for day in DAYS:
        s = lambda m, p: (m + "*" if p == "lab" else m).ljust(6)
        l = list(time_table.schedule[day].items())
        l.sort(key=lambda tup: tup[0])
        assignment = map(lambda t: "{0} {1} {2} ".format(t[0], s(t[1][1].name, t[1][2]), t[1][0].name), l)
        line = '\u007C'.join(str(x).ljust(20) for x in assignment)
        str_tab += " {0}".format(day[:3]).ljust(3) + " |" + line + '\n'

    str_tab += ' \u0305' * 200 + '\n'
    return str_tab

# Type Aliases
Day = str
Timeslot = int
# Session =
Type = str
Tutor = tutor.Tutor
Module = module.Module
Timetable = timetable.Timetable


class SchedulingTable(object):
    # TODO OLD domains   : { (Module, Type): [(Tutor, Day, Timeslot)] } variables and their domains
    # domains   : { (Module, Type): {Tutor: {Day: Timeslot}} } variables and their domains
    # NOTE: structured like this to make up (?)
    # scheduled : [(Day, Timeslot, Tutor, Module, Type)]
    # credits   : { Tutor: int }
    # NOTE: Tutors are keys are all constraints can be expressed in terms of tutor except the 1:1 module slot which
    #   can be implementing trivially/implicit

    def __init__(self, modules: [Module], tutors: [Tutor], task_num: int):
        self.TASK_NUM = task_num
        self.TUTORS = tutors
        self.MODULES = modules

        # 1. Initilise domains
        if task_num != 1:
            self.SLOT_COUNT = 10
            types = {"module", "lab"}
        else:
            self.SLOT_COUNT = 5
            types = {"module"}

        # initlise all possibles values a module can be assigned
        self.values: Tree(Type, Tutor, Day) = Tree()
        for tutor in self.TUTORS:
            for typ in types:
                for day in DAYS:
                    self.values.insert(typ, tutor, day)

        # domain of valid assignments for each module
        self.domains: Tree(Module, Type, Tutor, Day) = Tree()
        is_qual = {"module": lambda t, m: set(m.topics) <= set(t.expertise),
                   "lab": lambda t, m: set(m.topics) & set(t.expertise)}
        # populate domains with tutors the meet the requirements
        for typ in types:
            for module in self.MODULES:
                for tutor in self.TUTORS:
                    if is_qual[typ](tutor, module):
                        self.domains.insert(module, typ, tutor, self.values[typ][tutor])

        # 2. create empty scheduled list
        self.scheduled: Tree(Day, Tutor, Type, Module) = Tree()

        # List of tutors and credits on a given day
        self.credits: {(Tutor, Day): int} = {}

    def add(self, module, typ, tutor, day):

        self.scheduled.insert(day, tutor, typ, module)

        del self.domains[module][typ]
        if len(self.domains[module]) == 0:
            del self.domains[module]

        if self.scheduled.lookup(day).count() == self.SLOT_COUNT:
            # if len(self.scheduled[day]) == self.SLOT_COUNT:
            for typ_, tutor_ in self.values.tuples(2):
                self.values.remove(typ_, tutor_, day)

        credit = 1 if typ == "lab" else 2
        self.credits[tutor, day] = credit + self.get_credits(tutor, day)

        # Update domains
        self.update_values(day, tutor, typ)

    # TODO comabine add and update?
    def update_values(self, day, tutor, typ, simulation=False):
        values = self.values.copy() if simulation else self.values

        if typ == "module":
            values.remove("module", tutor, day)
            values.remove("lab", tutor, day)
        elif typ == "lab":
            values.remove("module", tutor, day)
            if self.get_credits(tutor, day) == 2:
                values.remove("lab", tutor, day)

        if self.get_credits(tutor) == 4:
            values.lookup("module", tutor).clear()
            values.lookup("lab", tutor).clear()
        elif self.get_credits(tutor) == 3:
            values.lookup("module", tutor).clear()

        return values

    def get_credits(self, tutor, day=None):
        if day is not None:
            return self.credits.get((tutor, day), 0)
        else:
            return sum(self.credits.get((tutor, d), 0) for d in DAYS)

    def copy(self):
        new_st = type(self).__new__(self.__class__)
        new_st.TASK_NUM = self.TASK_NUM
        new_st.SLOT_COUNT = self.SLOT_COUNT
        new_st.scheduled = self.scheduled.copy()
        new_st.credits = self.credits.copy()
        new_st.values = self.values.copy()
        new_st.domains = Tree()
        for module, typ, tutor in self.domains.tuples(3):
            new_st.domains.insert(module, typ, tutor, new_st.values[typ][tutor])
        return new_st

    def to_timetable(self):
        time_table = timetable.Timetable(self.TASK_NUM)
        slot = 0
        for day, tutor, typ, module in self.scheduled.tuples():
            slot = (slot % self.SLOT_COUNT) + 1
            time_table.addSession(day, slot, tutor, module, typ)
        return time_table

    def __repr__(self):
        return format_table(self.to_timetable())


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

class Scheduler:

    def __init__(self, tutorList, moduleList):
        self.tutorList = tutorList
        self.moduleList = moduleList

    def lcv(self, module, typ, domain, scheduling_table):
        possible_sizes: {Tutor: int} = {}
        for tutor, day in domain:
            if possible_sizes.get(tutor, None):
                continue
            else:
                vals = scheduling_table.update_values(day, tutor, typ, simulation=True)
                possible_sizes[tutor] = vals.count()

        # NOTE: days differ by at most 1and the only time the day matters is when you working on that day or not
        #   most cases your not except in one situaion where your already teaching a lab and can teach another, in this
        #   this is rare as you also have to be the min and even then the differnce is atmost 1 as
        #   if your assiged to the working day the only the nonworking day remains
        #   but if you choose the non working day you can still work on either the next day
        m_tutor = min(possible_sizes.keys(), key=lambda k: possible_sizes[k])
        tutor, day = next((tutor, day) for tutor, day in domain if tutor == m_tutor)
        domain.remove((tutor, day))
        return tutor, day


    def mrv(self, domains):

        domain_size = lambda module, typ: domains[module][typ].count()

        min_list = mins(domains.tuples(depth=2), lambda x: domain_size(*x))

        # NOTE:  dergree heuristic approx by assigning modules first
        module, typ = max(min_list, key=lambda module_typ: module_typ[1])
        domain = domains[module][typ].list_tuples()
        return module, typ, domain

    def backtrack(self, scheduling_table):
        ### 0. Check if complete (base case)
        if not scheduling_table.domains:
            return scheduling_table

        ### 1. Select a var
        ### ...get variable's domain

        module, typ, domain = self.mrv(scheduling_table.domains)

        s = module.name if typ == "module" else module.name + "L"

        ### 2. For each value in domain of var
        while domain:

            # Note: only use lcv ar the start where its most impactfull and domain is large
            if scheduling_table.domains.count(depth=2) < 25:
                tutor, day = self.lcv(module, typ, domain, scheduling_table)
            else:
                tutor, day = domain.pop(0)

            ss = "{0} {1}".format(tutor.name, day[:3])

            new_scheduling_table = scheduling_table.copy()

            new_scheduling_table.add(module, typ, tutor, day)

            ### 3. If assignment would breaks constraints Then try next value

            ### 4. Otherwable.domainsise assign var = value

            ### 5. recursive call on csp with new assignment(timetable)
            final_table = self.backtrack(new_scheduling_table)
            ### 6. if recurive call does NOT fail () then return the solution
            if final_table is not None:
                return final_table

            ### 7. else remove the assignment and try next
        ### 6. If no value found return fail to parent call
        return None

    def schedule(self, task_num):
        st = SchedulingTable(self.moduleList, self.tutorList, task_num)
        return self.backtrack(st)

    def createSchedule(self):
        return self.schedule(1).to_timetable()

    def createLabSchedule(self):
        return self.schedule(2).to_timetable()

    def createMinCostSchedule(self):
        # Do not change this line
        NUM_OF_STEPS = 5000
        NUM_OF_TABLES = 50
        best = math.inf


        for i in range(NUM_OF_TABLES):
            tab = self.schedule(3)
            cost, tab = self.simulate_anneal(tab, NUM_OF_STEPS)
            if cost < best:
                best_tab = tab
                best = cost
            random.shuffle(self.moduleList)
            random.shuffle(self.tutorList)

        return best_tab

    def simulate_anneal(self, tab, num_of_steps):
        sch = tab.scheduled
        # START
        can_teach = self.make_can_teach()
        best_cost = math.inf
        # random_slot = lambda: random.choice(sch[k])
        random_slot = lambda assignments: random.choice(assignments)
        # Generate initial population
        # copy_schedule = lambda sch: {k: v.copy() for k, v in sch.items()}
        for c in range(num_of_steps):
            new_sch = sch.copy()
            # day = random.choice(DAYS)
            module_or_tutor = random.random()
            assignments = list(sch.list_tuples())
            day, tutor, typ, module = assignments[c % len(assignments)]
            for i in range(50):
                day_, tutor_, typ_, module_ = random_slot(assignments)
                if can_teach(module, typ, tutor_) and can_teach(module_, typ_, tutor):
                    # Otherwise swap tutors keep mo the same
                    if typ != typ_:
                        continue

                    if module_or_tutor > 0.5 and module != module_:
                        # swap modules keep tutors the same
                        del new_sch[day][tutor][typ][module]
                        del new_sch[day_][tutor_][typ_][module_]
                        new_sch.insert(day, tutor, typ, module_)
                        new_sch.insert(day_, tutor_, typ_, module)
                        break

                    try:
                        tutor_day_count = sch.lookup(day_, tutor, typ).count()
                        new_tutor_day_count = sch.lookup(day, tutor_, typ_).count()
                    except:
                        continue

                    if typ == "module":
                        if tutor_day_count != 0 or new_tutor_day_count != 0:
                            continue
                    elif typ == "lab":
                        if tutor_day_count > 1 or new_tutor_day_count > 1:
                            continue
                    # If swap is legal implement it
                    new_sch.remove(day, tutor, typ, module)
                    new_sch.remove(day_, tutor_, typ_, module_)
                    new_sch.insert(day, tutor_, typ, module)
                    new_sch.insert(day_, tutor, typ_, module_)
                    break
            else:
                continue
            t = num_of_steps / (c + 1)
            cost = self.cost(sch)
            new_cost = self.cost(new_sch)
            if new_cost < cost or random.random() < math.exp((new_cost - cost) / t):
                sch = new_sch
                if new_cost < best_cost:
                    best = new_sch
                    best_cost = new_cost

        scheduling_table = SchedulingTable(self.moduleList, self.tutorList, 3)
        scheduling_table.scheduled = best
        print(scheduling_table)
        best_table = scheduling_table.to_timetable()
        return best_cost, best_table

    def schedule_to_timetable(self, schedule):
        time_table = timetable.Timetable(self.TASK_NUM)
        slot = 0
        # for day, tutor, typ, module in self.scheduled.tuples():
        for day, allocation in schedule.items():
            for module, typ, tutor in allocation:
                slot = (slot % self.SLOT_COUNT) + 1
                time_table.addSession(day, slot, tutor, module, typ)
        return time_table

    def make_can_teach(self):
        st = SchedulingTable(self.moduleList, self.tutorList, 3)
        def can_teach(module, typ, tutor):
            return bool(st.domains.lookup(module, typ, tutor))
        return can_teach

    def perportional_choose(self, population):
        total = sum(p[1] for p in population)

        def choose():
            x = 0
            r = random.uniform(0, total)
            for p, f in population:
                x += (total - f)
                if x > r:
                    return p

        return choose

    def cost(self, schedule):
        tutor_count = dict()
        modules_assigned = list()
        labs_assigned = list()
        schedule_cost = 0
        mod_count = dict()
        lab_count = dict()
        taught_module_yesterday = list()

        for tutor in self.tutorList:
            mod_count[tutor.name] = 0
            lab_count[tutor.name] = 0
            tutor_count[tutor.name] = 0

        for day in DAYS:
            tutors_today = dict()
            possible_discount = dict()
            taught_module_today = list()

            # process the validity of each entry
            for tut, typ, mod in schedule.lookup(day).tuples():
                if typ == "module":
                    modules_assigned.append(mod.name)
                else:
                    labs_assigned.append(mod.name)

                if tut.name in tutors_today:
                    if typ == "module":
                        tutors_today[tut.name] = tutors_today[tut.name] + 2
                        taught_module_today.append(tut)
                        mod_count[tut.name] = mod_count[tut.name] + 1
                        if mod_count[tut.name] == 1:
                            schedule_cost = schedule_cost + 500
                        elif tut in taught_module_yesterday:
                            schedule_cost = schedule_cost + 100
                        else:
                            schedule_cost = schedule_cost + 300
                    else:
                        tutors_today[tut.name] = tutors_today[tut.name] + 1
                        lab_count[tut.name] = lab_count[tut.name] + 1
                        initial_lab_cost = (300 - (50 * lab_count[tut.name])) / 2
                        schedule_cost = schedule_cost + initial_lab_cost

                        if tut.name in possible_discount:
                            schedule_cost = schedule_cost - possible_discount.pop(tut.name)
                else:
                    if typ == "module":
                        tutors_today[tut.name] = 2
                        taught_module_today.append(tut)
                        mod_count[tut.name] = mod_count[tut.name] + 1
                        if mod_count[tut.name] == 1:
                            schedule_cost = schedule_cost + 500
                        elif tut in taught_module_yesterday:
                            schedule_cost = schedule_cost + 100
                        else:
                            schedule_cost = schedule_cost + 300
                    else:
                        tutors_today[tut.name] = 1
                        lab_count[tut.name] = lab_count[tut.name] + 1
                        initial_lab_cost = (300 - (50 * lab_count[tut.name]))
                        schedule_cost = schedule_cost + initial_lab_cost
                        possible_discount[tut.name] = initial_lab_cost / 2

            # One last check to make sure daily credits haven't been exceeded
            taught_module_yesterday = taught_module_today

        # If we get here, schedule is legal, so we assign the cost and return True
        return schedule_cost




def mins(list, key=lambda x: x):
    min_list = []
    min = math.inf
    for x in list:
        k = key(x)
        if k > min:
            continue
        elif k == min:
            min_list.append(x)
        else:
            min = k
            min_list = [x]
    return min_list


# TODO remove () as leaves with (value)
# Extends dict
class Tree(dict):
    def insert(self, *keys):
        *ks, k, v = keys
        d = self
        for key in ks:
            d = d.setdefault(key, Tree())
        if isinstance(v, Tree):
            d[k] = v
        else:
            d = d.setdefault(k, Tree())
            d[v] = ()  # leaf is ()

    def copy(self, dic=None):
        if dic is None:
            dic = self
        try:
            cpy = Tree()
            for k, v in dic.items():
                cpy[k] = self.copy(v) if v is not None else None
            return cpy
        except AttributeError:
            return dic

    def lookup(self, *keys):
        d = self
        for key in keys:
            try:
                d = d[key]
            except (TypeError, KeyError) as e:
                return {}
        return d

    def remove(self, *keys):
        *ks, k = keys
        d = self
        try:
            for key in ks:
                d = d[key]
            d[k] = None
        except (TypeError, KeyError) as e:
            pass

    # TODO rename 'tuples'
    def tuples(self, depth=-1):
        return self.all_tuples() if depth==-1 else self.layer_tuples(depth)


    def all_tuples(self):
        # todo: one line for is None assignments
        for k, v in self.items():
            try:
                for v_ in v.all_tuples():
                    yield (k, *v_)
            except AttributeError:
                if v is not None:
                    yield (k,)

    def layer_tuples(self, depth):
        # todo: one line for is None assignments
        for k, v in self.items():
            if v is None:
                continue
            elif not isinstance(v, Tree) or depth == 1:
                yield (k,)
            else:
                for v_ in v.layer_tuples(depth - 1):
                    yield (k, *v_)

    def list_tuples(self):
        return list(self.all_tuples())

    def count(self, depth=math.inf):
        return len(list(self.tuples(depth)))



    # def tuples_(self, depth=math.inf):
    #     # todo: one line for is None assignments
    #     for k, v in self.items():
    #         try:
    #             for v_ in v.tuples_(depth-1):
    #                 yield (k, *v_)
    #         except AttributeError: # v is not nested dic
    #             if v is not None or depth == 1:
    #                 yield (k,)

# def multi_min(list, key=lambda x:x):
#     m = key(min(list,key=key))
#     l = [x for x in list if key(x)==m]
#     l.sort(key=lambda tup: len(tup[0].expertise))
#     return l[0]
