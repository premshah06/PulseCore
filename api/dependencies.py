"""FastAPI dependency functions for injecting app-level singletons."""

from fastapi import Request


def get_db(request: Request):
    return request.app.state.db


def get_ws_manager(request: Request):
    return request.app.state.ws_manager
