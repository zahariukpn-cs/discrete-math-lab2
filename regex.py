from __future__ import annotations
from abc import ABC, abstractmethod


class State(ABC):

    def __init__(self) -> None:
        self.next_states: list[State] = []

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        function checks whether occured character is handled by current ctate
        """
        pass

    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise NotImplementedError("rejected string")


class StartState(State):

    def __init__(self):
        super().__init__()

    def check_self(self, char: str) -> bool:
        """не мав би перевірятися"""
        return False


class TerminationState(State):

    def __init__(self):
        super().__init__()

    def check_self(self, char: str) -> bool:
        """вже заключний стан а символи ще є"""
        return False


class DotState(State):
    """
    state for . character (any character accepted)
    """

    def __init__(self):
        super().__init__()

    def check_self(self, char: str) -> bool:
        """будь-який символ пдіходить"""
        return True


class AsciiState(State):
    """
    state for alphabet letters or numbers
    """

    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.curr_sym = symbol

    def check_self(self, curr_char: str) -> bool:
        return curr_char == self.curr_sym


class StarState(State):

    def __init__(self, checking_state: State):
        super().__init__()
        self.checking_state = checking_state

    def check_self(self, char: str) -> bool:
        for state in self.next_states:
            if state.check_self(char):
                return True

        return False


class PlusState(State):

    def __init__(self, checking_state: State):
        super().__init__()
        self.checking_state = checking_state

    def check_self(self, char: str) -> bool:
        return self.checking_state.check_self(char)


class RegexFSM:

    def __init__(self, regex_expr: str) -> None:
        self.curr_state = StartState()

        prev_state = self.curr_state
        tmp_next_state = self.curr_state

        for char in regex_expr:
            tmp_next_state = self.__init_next_state(char, prev_state, tmp_next_state)
            prev_state.next_states.append(tmp_next_state)

    def __init_next_state(
        self, next_token: str, prev_state: State, tmp_next_state: State
    ) -> State:
        new_state = None

        match next_token:
            case next_token if next_token == ".":
                new_state = DotState()

            case next_token if next_token == "*":
                new_state = StarState(tmp_next_state)
                # here you have to think, how to do it.
                # i handled it in def _match
                # "a*" = AsciiState("a") + StarState(a)

            case next_token if next_token == "+":
                new_state = PlusState(tmp_next_state)

            case next_token if next_token.isascii():
                new_state = AsciiState(next_token)

            case _:
                raise AttributeError("Character is not supported")

        return new_state

    def check_string(self, input_string: str) -> bool:
        """
        Recursive backtracking matcher over the flat state list.

        States in curr_state.next_states are ordered sequentially.
        For 'a*4.+hi':
          [AsciiState_a, StarState_a, AsciiState_4, DotState, PlusState_dot, AsciiState_h, AsciiState_i]

        StarState and PlusState store the checking_state (the literal before them).
        I handle them with backtracking so the regex is not greedy.
        """
        states = self.curr_state.next_states
        return self._match(states, 0, input_string, 0)

    def _match(self, states: list, state_index: int, s: str, char_index: int) -> bool:
        """Recursively try to match states[state_index:] against s[ci:]."""
        n_states = len(states)
        n_chars = len(s)

        if state_index == n_states:
            return char_index == n_chars

        state = states[state_index]

        #is this literal state followed immediately by a StarState/PlusState wrapping it?
        next_is_star = (
            state_index + 1 < n_states
            and isinstance(states[state_index + 1], StarState)
            and states[state_index + 1].checking_state is state
        )
        next_is_plus = (
            state_index + 1 < n_states
            and isinstance(states[state_index + 1], PlusState)
            and states[state_index + 1].checking_state is state
        )

        if isinstance(state, StarState):
            #0 or more: first try skipping entirely, then consume (if can)
            if self._match(states, state_index + 1, s, char_index):
                return True
            if char_index < n_chars and state.checking_state.check_self(s[char_index]):
                return self._match(states, state_index, s, char_index + 1)
            return False

        elif isinstance(state, PlusState):
            #preceding literal already consumed the mandatory first char
            #PlusState handles zero or more additional matches (so that non-greedy)
            if char_index < n_chars and state.checking_state.check_self(s[char_index]):
                return (
                    self._match(states, state_index + 1, s, char_index)     #stop here (cause non-greedy)
                    or self._match(states, state_index, s, char_index + 1)  #consume one more
                )
            return self._match(states, state_index + 1, s, char_index)  #char doesn't match so it moves on

        elif next_is_star:
            #jump straight to StarState (zero occurrences is valid)
            return self._match(states, state_index + 1, s, char_index)

        elif next_is_plus:
            #match at least once here, then hand off to PlusState
            if char_index < n_chars and state.check_self(s[char_index]):
                return self._match(states, state_index + 1, s, char_index + 1)
            return False

        else:
            #plain state: consume exactly one matching char
            if char_index < n_chars and state.check_self(s[char_index]):
                return self._match(states, state_index + 1, s, char_index + 1)
            return False


if __name__ == "__main__":
    regex_pattern = "a*4.+hi"

    regex_compiled = RegexFSM(regex_pattern)

    print(regex_compiled.check_string("aaaaaa4uhi"))  # True
    print(regex_compiled.check_string("4uhi"))        # True
    print(regex_compiled.check_string("meow"))        # False

    print("---------------")
    regex_pattern = "A*.end"

    regex_compiled = RegexFSM(regex_pattern)

    print(regex_compiled.check_string("AAAAAAAAAAAAAA1end"))    # True
    print(regex_compiled.check_string("Aend"))                  # True
    print(regex_compiled.check_string("AAaaaaaaaend"))          # False
    print(regex_compiled.check_string("AAAAAAAAA"))             # False
    print(regex_compiled.check_string("the1end"))               # False

    print("----------")
    regex_pattern = "a+b"
    regex_compiled = RegexFSM(regex_pattern)
    print(regex_compiled.check_string("ab"))      # True
    print(regex_compiled.check_string("aaaaab"))  # True
    print(regex_compiled.check_string("b"))       # False
    print(regex_compiled.check_string("a"))       # False

    print("----------")
    regex_pattern = ".+end"
    regex_compiled = RegexFSM(regex_pattern)
    print(regex_compiled.check_string("theend"))   # True
    print(regex_compiled.check_string("1end"))     # True
    print(regex_compiled.check_string("end"))      # False
