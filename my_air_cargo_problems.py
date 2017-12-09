import copy

from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import (
    Node, Problem,
)
from aimacode.utils import expr
from lp_utils import (
    FluentState, encode_state, decode_state,
)
from my_planning_graph import PlanningGraph

from functools import lru_cache


class AirCargoProblem(Problem):
    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem
        :param planes: list of str
            planes in the problem
        :param airports: list of str
            airports in the problem
        :param initial: FluentState object
            positive and negative literal fluents (as expr) describing initial state
        :param goal: list of expr
            literal fluents required for goal test
        """
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal)
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        """
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        """

        # TODO create concrete Action objects based on the domain action schema for: Load, Unload, and Fly
        # concrete actions definition: specific literal action that does not include variables as with the schema
        # for example, the action schema 'Load(c, p, a)' can represent the concrete actions 'Load(C1, P1, SFO)'
        # or 'Load(C2, P2, JFK)'.  The actions for the planning problem must be concrete because the problems in
        # forward search and Planning Graphs must use Propositional Logic

        def load_actions():
            """Create all concrete Load actions and return a list

            :return: list of Action objects
            """
            loads = []
            # TODO create all load ground actions from the domain Load action
            for cargo in self.cargos:
                for plane in self.planes:
                    for airport in self.airports:
                        precond_pos = [expr('At({}, {})'.format(cargo, airport)),
                                       expr('At({}, {})'.format(plane, airport))
                                       ]
                        precond_neg = []
                        effect_add = [expr('In({}, {})'.format(cargo, plane))]
                        effect_rem = [expr('At({}, {})'.format(cargo, airport))]
                        loadaction = expr('Load({}, {}, {})'.format(cargo, plane, airport))
                        loads.append(Action(loadaction,
                                            [precond_pos, precond_neg],
                                             [effect_add, effect_rem]))

            return loads

        def unload_actions():
            """Create all concrete Unload actions and return a list

            :return: list of Action objects
            """
            unloads = []
            # TODO create all Unload ground actions from the domain Unload action
            for cargo in self.cargos:
                for plane in self.planes:
                    for airport in self.airports:
                        precond_pos = [expr('In({}, {})'.format(cargo, plane)),
                                       expr('At({}, {})'.format(plane, airport))
                                       ]
                        precond_neg = []
                        effect_add = [expr('At({}, {})'.format(cargo, airport))]
                        effect_rem = [expr('In({}, {})'.format(cargo, plane))]
                        unloadaction = expr('Unload({}, {}, {})'.format(cargo, plane, airport))
                        unloads.append(Action(unloadaction,
                                              [precond_pos, precond_neg],
                                              [effect_add, effect_rem]))
            return unloads

        def fly_actions():
            """Create all concrete Fly actions and return a list

            :return: list of Action objects
            """
            flys = []
            for fr in self.airports:
                for to in self.airports:
                    if fr != to:
                        for p in self.planes:
                            precond_pos = [expr("At({}, {})".format(p, fr)),
                                           ]
                            precond_neg = []
                            effect_add = [expr("At({}, {})".format(p, to))]
                            effect_rem = [expr("At({}, {})".format(p, fr))]
                            fly = Action(expr("Fly({}, {}, {})".format(p, fr, to)),
                                         [precond_pos, precond_neg],
                                         [effect_add, effect_rem])
                            flys.append(fly)
            return flys

        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """

        def check_action_preconditions(action, fluentstate):
          for precond_pos in action.precond_pos:
            if not precond_pos in fluentstate.pos:
              return False

          for precond_neg in action.precond_neg:
            if not precond_neg in fluentstate.neg:
              return False

          return True

        # TODO implement
        fs = decode_state(state, self.state_map)
        possible_actions = []
        all_actions = self.get_actions()
        for action in all_actions:

          if check_action_preconditions(action, fs):
            possible_actions.append(action)

        return possible_actions

    def result(self, state: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).

        :param state: state entering node
        :param action: Action applied
        :return: resulting state after action
        """
        # TODO implement
        #new_state = FluentState([], [])
        #return encode_state(new_state, self.state_map)

        new_state = FluentState([], [])
        old_state = decode_state(state, self.state_map)
        for fluent in old_state.pos:
          if fluent not in action.effect_rem:
            new_state.pos.append(fluent)
        for fluent in action.effect_add:
          if fluent not in new_state.pos:
            new_state.pos.append(fluent)
        for fluent in old_state.neg:
          if fluent not in action.effect_add:
            new_state.neg.append(fluent)
        for fluent in action.effect_rem:
          if fluent not in new_state.neg:
            new_state.neg.append(fluent)
        return encode_state(new_state, self.state_map)

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached

        :param state: str representing state
        :return: bool
        """
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                return False
        return True

    def h_1(self, node: Node):
        # note that this is not a true heuristic
        h_const = 1
        return h_const

    @lru_cache(maxsize=8192)
    def h_pg_levelsum(self, node: Node):
        """This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        """
        # requires implemented PlanningGraph class
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        return pg_levelsum

    @lru_cache(maxsize=8192)
    def h_ignore_preconditions(self, node: Node):
        """This heuristic estimates the minimum number of actions that must be
        carried out from the current state in order to satisfy all of the goal
        conditions by ignoring the preconditions required for an action to be
        executed.
        """
        # TODO implement (see Russell-Norvig Ed-3 10.2.3  or Russell-Norvig Ed-2 11.2)
        count = 0

        fs = decode_state(node.state, self.state_map)

        #print('goal is:')
        #print(self.goal)
        #print('fs.pos is:')
        #print(fs.pos)

        for goal in self.goal:
            if goal not in fs.pos:
                count += 1


        # print(len(self.actions(node.state)))

        # for action in self.actions(node.state):
        #     action_copy = copy.deepcopy(action)
        #     action_copy.precond_pos = []
        #     action_copy.precond_neg = []
        #     current_state = self.result(current_state, action_copy)
        #     count += 1
        #     if self.goal_test(current_state):
        #         break

        # while 1:
        #     actions_at_current_state = self.actions(current_state)
        #     print(actions_at_current_state)
        #     if len(actions_at_current_state) == 0:
        #         raise ValueError('no more actions can be taken')
        #
        #     # Remove the action preconditions.  Build a copy of the action so we don't end up
        #     # modifying the underlying action.
        #     action_copy = copy.deepcopy(actions_at_current_state[0])
        #     action_copy.precond_pos = []
        #     action_copy.precond_neg = []
        #     current_state = self.result(current_state, action_copy)
        #     count += 1
        #     if self.goal_test(current_state):
        #         break

        return count


def air_cargo_p1() -> AirCargoProblem:
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    neg = [expr('At(C2, SFO)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('At(C1, JFK)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('At(P1, JFK)'),
           expr('At(P2, SFO)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    # TODO implement Problem 2 definition

    # Init(At(C1, SFO) ∧ At(C2, JFK) ∧ At(C3, ATL)
    # ∧ At(P1, SFO) ∧ At(P2, JFK) ∧ At(P3, ATL)
    # ∧ Cargo(C1) ∧ Cargo(C2) ∧ Cargo(C3)
    # ∧ Plane(P1) ∧ Plane(P2) ∧ Plane(P3)
    # ∧ Airport(JFK) ∧ Airport(SFO) ∧ Airport(ATL))
    # Goal(At(C1, JFK) ∧ At(C2, SFO) ∧ At(C3, SFO))

    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['SFO', 'JFK', 'ATL']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           expr('At(P3, ATL)'),
           ]
    neg = [expr('At(C1, JFK)'),
           expr('At(C1, ATL)'),
           expr('At(C2, SFO)'),
           expr('At(C2, ATL)'),
           expr('At(C3, SFO)'),
           expr('At(C3, JFK)'),
           expr('At(P1, JFK)'),
           expr('At(P1, ATL)'),
           expr('At(P2, SFO)'),
           expr('At(P2, ATL)'),
           expr('At(P3, SFO)'),
           expr('At(P3, JFK)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('In(C1, P3)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('In(C2, P3)'),
           expr('In(C3, P1)'),
           expr('In(C3, P2)'),
           expr('In(C3, P3)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, SFO)'),
            ]

    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p3() -> AirCargoProblem:
    # TODO implement Problem 3 definition

    # Init(At(C1, SFO) ∧ At(C2, JFK) ∧ At(C3, ATL) ∧ At(C4, ORD)
    # ∧ At(P1, SFO) ∧ At(P2, JFK)
    # ∧ Cargo(C1) ∧ Cargo(C2) ∧ Cargo(C3) ∧ Cargo(C4)
    # ∧ Plane(P1) ∧ Plane(P2)
    # ∧ Airport(JFK) ∧ Airport(SFO) ∧ Airport(ATL) ∧ Airport(ORD))
    # Goal(At(C1, JFK) ∧ At(C3, JFK) ∧ At(C2, SFO) ∧ At(C4, SFO))

    cargos = ['C1', 'C2', 'C3', 'C4']
    planes = ['P1', 'P2']
    airports = ['SFO', 'JFK', 'ATL', 'ORD']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(C4, ORD)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    neg = [expr('At(C1, JFK)'),
           expr('At(C1, ATL)'),
           expr('At(C1, ORD)'),
           expr('At(C2, SFO)'),
           expr('At(C2, ATL)'),
           expr('At(C2, ORD)'),
           expr('At(C3, SFO)'),
           expr('At(C3, JFK)'),
           expr('At(C3, ORD)'),
           expr('At(C4, SFO)'),
           expr('At(C4, JFK)'),
           expr('At(C4, ATL)'),
           expr('At(P1, JFK)'),
           expr('At(P1, ATL)'),
           expr('At(P1, ORD)'),
           expr('At(P2, SFO)'),
           expr('At(P2, ATL)'),
           expr('At(P2, ORD)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('In(C3, P1)'),
           expr('In(C3, P2)'),
           expr('In(C4, P1)'),
           expr('In(C4, P2)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, JFK)'),
            expr('At(C4, SFO)'),
            ]

    return AirCargoProblem(cargos, planes, airports, init, goal)
