# *- coding: utf-8 -*-
from typing import Optional


def _create_mutex_a(mutex_attributes: Optional[None], initial_owner: bool, name: str):
    """
    С++
    HANDLE CreateMutexA(
        LPSECURITY_ATTRIBUTES lpMutexAttributes,
        BOOL                  bInitialOwner,
        LPCSTR                lpName
    );
    link: https://docs.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createmutexa
    """

    from ctypes import windll
    return windll.kernel32.CreateMutexA(mutex_attributes, initial_owner, name)


def _get_win_error(code: Optional[int], description: Optional[str]) -> OSError:
    from ctypes import WinError
    return WinError(code, description)


def check_clone() -> int:
    ERROR_ALREADY_EXISTS: int = 183

    mutex: int = _create_mutex_a(None, False, "Knowledge Base Constructor")
    error: OSError = _get_win_error(None, None)
    win_error_code = error.args[3]

    if win_error_code == ERROR_ALREADY_EXISTS:
        return ERROR_ALREADY_EXISTS
    return 0


if __name__ == '__main__':
    check_clone()
    input()
