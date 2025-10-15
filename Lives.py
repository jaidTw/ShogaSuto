#!/usr/bin/env python3

from sqlitedict import SqliteDict
import datetime


def get_tour_name(tour):
    with SqliteDict("ztmy.sqlite", tablename="tours", autocommit=True) as tours:
        return tours[tour]['name']

def list_tours():
    msg = ""

    with SqliteDict("ztmy.sqlite", tablename="tours", autocommit=True) as tours:
        for k, v in tours.items():
            msg += f"({k}) {v['name']}\n"

    if any(msg):
        msg = "請代入欲查詢的巡演編號至`tour`參數：\n" + msg
    else:
        msg = "當前沒有巡演資料"
    return msg


def list_lives(tour):
    msg = ""

    try:
        tour_name = get_tour_name(tour)
    except KeyError:
        return "當前沒有公演資料"
    else:
        tour = int(tour)

        results = []
        with SqliteDict("ztmy.sqlite", tablename="lives", autocommit=True) as lives:
            for k, v in lives.items():
                if v['tour'] == tour:
                    results.append(v)

        results.sort(key=lambda x: x['date'])
        for i, v in enumerate(results, start=1):
            msg += f"({i}) {v['date'].strftime('%m/%d')} {v['location']}\n"

        if any(msg):
            msg = f"請代入欲參加的{tour_name}公演日期(MM/DD)至`date`參數：\n" + msg
        else:
            msg = "當前沒有公演資料"
    return msg


def list_tour_attendees(tour):
    msg = ""

    try:
        tour_name = get_tour_name(tour)
    except KeyError:
        return "當前沒有公演資料"
    else:
        tour = int(tour)

        result = []
        with SqliteDict("ztmy.sqlite", tablename="lives", autocommit=True) as lives:
            for k, v in lives.items():
                if v['tour'] == tour:
                    result.append(v)

        result.sort(key=lambda x: x['date'])

    return result

def reg_attend(tour, live, gid, uid):
    try:
        tour = int(tour)
        m, d = map(int, live.split("/"))
        with SqliteDict("ztmy.sqlite", tablename="lives", autocommit=True) as lives:
            to_reg = []
            for k, v in lives.items():
                if v['tour'] == tour and v['date'].month == m and v['date'].day == d:
                    to_reg.append((k, v))
            for k, v in to_reg:
                v['members'].add((gid, uid))
                lives[k] = v
        return 0
    except Exception:
        return 1


def list_attend(tour, live):
    try:
        tour = int(tour)
        m, d = map(int, live.split("/"))
        result = []
        with SqliteDict("ztmy.sqlite", tablename="lives", autocommit=True) as lives:
            for k, v in lives.items():
                if v['tour'] == tour and v['date'].month == m and v['date'].day == d:
                    result.append(v)
    except Exception:
        return []
    return result

def unreg_attend(tour, live, gid, uid):
    try:
        tour = int(tour)
        m, d = map(int, live.split("/"))
        with SqliteDict("ztmy.sqlite", tablename="lives", autocommit=True) as lives:
            to_unreg = []
            for k, v in lives.items():
                if v['tour'] == tour and v['date'].month == m and v['date'].day == d:
                    to_unreg.append((k, v))
            for k, v in to_unreg:
                v['members'].remove((gid, uid))
                lives[k] = v
        return 0
    except Exception:
        return 1
