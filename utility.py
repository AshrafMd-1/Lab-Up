import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import random
import string
from requests_toolbelt import MultipartEncoder
import streamlit as st


def login_user(username_f, password_f):
    login_url = "https://samvidha.iare.ac.in/pages/login/checkUser.php"
    payload = {
        "username": username_f,
        "password": password_f
    }
    res = requests.post(login_url, data=payload)
    log = json.loads(res.content)
    if log["status"] == "1":
        print("Logged in succesfully")
        return res.cookies.get_dict()
    else:
        print(log["msg"])
        return None

def got_name(cookies):
    home_url = "https://samvidha.iare.ac.in/home?action=profile"
    res=requests.get(home_url, cookies=cookies)
    soup = BeautifulSoup(res.text, features="html.parser")
    details = soup.select(".box-profile")[0]
    img_src = details.select("img")[0].get("src")
    name = details.select(".profile-username")[0].text
    branch = details.select(".text-muted")[0].text
    return name, branch, img_src


def user_page(name, branch, img_src):
    html = f"""
    <style>
    .container {{
        display: flex;
        flex-direction: row;
        align-items: center;
    }}
    .container > div {{
        margin: 10px;
    }}
    </style>

    <div class="container">
    <div>
    <img src="{img_src}" alt="Profile Picture" width="100" height="100" style="border-radius: 50%;">
    </div>
    <div>
    <h3>{name}</h3>
    <h5>{branch}</h5>
    </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def got_page(cookies):
    lab_url = "https://samvidha.iare.ac.in/home?action=labrecord_std"
    r = requests.get(lab_url, cookies=cookies)
    soup = BeautifulSoup(r.text, features="html.parser")
    return soup


def got_details(soup):
    ay = soup.select("#ay")[0].get("value")
    roll = soup.select("#rollno")[0].get("value")
    batch = soup.select("#lab_batch_no")[0].get("value")
    sem = soup.select("#current_sem")[0].get("value")
    return ay, roll, batch, sem




def got_subjects(soup):
    full_table = soup.select("#sub_code option")[1:]
    sub = []
    for i in full_table:
        sub.append(i.text)
    return sub


def get_open_lab_worksheets(cookies, ay, sub_code):
    open_worksheet_url = "https://samvidha.iare.ac.in/pages/student/lab_records/ajax/day2day.php"
    payload = {
        "ay": ay,
        "sub_code": sub_code,
        "action": "get_exp_list"
    }
    res = requests.post(open_worksheet_url, data=payload, cookies=cookies)
    soup = BeautifulSoup(res.content, features="html.parser")
    if len(soup.select("tr")) > 0:
        header_tr = soup.select("tr")[0]
        data_tr = soup.select("tr")[1:]
    else:
        header_tr = []
        data_tr = []
    header = []
    data = []
    if len(header_tr) > 0:
        for i in header_tr.select("td"):
            i = i.text.strip()
            header.append(i)
    if len(data_tr) > 0:
        for i in data_tr:
            row = []
            for j in i.select("td"):
                j = j.text.strip()
                row.append(j)
            data.append(row)
    df = pd.DataFrame(data)
    df.columns = header
    return df


def show_uploaded_lab_worksheets(roll, ay, sub_code):
    uploaded_worksheet_url = "https://samvidha.iare.ac.in/pages/student/lab_records/ajax/day2day.php"
    payload = {
        "rollno": roll,
        "ay": ay,
        "sub_code": sub_code,
        "action": "day2day_lab"
    }
    res = requests.post(uploaded_worksheet_url, data=payload)
    uploads_data = json.loads(res.content)
    header_u = []
    if len(uploads_data["data"]) > 0:
        for i in uploads_data["data"][0]:
            header_u.append(i.strip())
    data_u = []
    for i in uploads_data["data"]:
        row = []
        for j in i.values():
            if str(j).isnumeric():
                row.append(int(str(j).strip()))
            else:
                row.append(str(j).strip())
        data_u.append(row)
    df = pd.DataFrame(data_u)
    df.columns = header_u
    return df


def uploadable_weeks(open_worksheet_table, uploaded_worksheet_table):
    weeks = []
    titles = []
    det_w = list(open_worksheet_table["Week-#"])
    det_h = list(open_worksheet_table["Experiment Title"])
    det_t = list(open_worksheet_table["ExperimentSubmission Date"])
    for i, j in enumerate(det_t):
        a = [x for x in j.split("-")]
        a[2] = a[2][2:]
        j = "-".join(a)
        if datetime.datetime.strptime(j, '%d-%m-%y').date() >= datetime.date.today():
            weeks.append(det_w[i])
            titles.append(det_h[i])
    # for i in uploaded_worksheet_table['week_no']:
    #     already_uploaded = f'Week-{i}'
    #     if already_uploaded in weeks:
    #         weeks.pop(weeks.index(already_uploaded))
    return weeks, titles


def upload_worksheet(cookies, ay, sem, sub_code, week_no, roll, batch, title, file):
    upload_url = "https://samvidha.iare.ac.in/pages/student/lab_records/ajax/day2day"
    payload = {
        "ay": ay,
        "rollno": roll,
        'current_sem': sem,
        'sub_code': sub_code,
        "lab_batch_no": batch,
        "week_no": week_no,
        "exp_title": title,
        'prog_doc': ("application/pdf", file.getvalue()),
        'action': 'upload_lab_record_student'
    }
    boundary = '----WebKitFormBoundary' + \
        ''.join(random.sample(string.ascii_letters + string.digits, 16))
    m = MultipartEncoder(fields=payload, boundary=boundary)
    headers = {
        "Content-Type": m.content_type
    }
    res = requests.post(upload_url, data=m, headers=headers, cookies=cookies)
    log = json.loads(res.content)
    return log