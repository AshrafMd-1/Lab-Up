import streamlit as st

from utility import login_user, got_page, got_details, got_subjects, get_open_lab_worksheets, \
    show_uploaded_lab_worksheets, uploadable_weeks, upload_worksheet, got_name, user_page

if 'cookies' not in st.session_state:
    st.session_state['cookies'] = None

if 'user_details' not in st.session_state:
    st.session_state['user_details'] = {
        "img": None,
        "name": None,
        "branch": None,
    }

if 'details' not in st.session_state:
    st.session_state['details'] = {
        'ay': None,
        'roll': None,
        'batch': None,
        'sem': None
    }

if 'worksheet' not in st.session_state:
    st.session_state['worksheet'] = {
        'subjects': None,
        "choosen_subject": None,
        "uploaded_worksheet_table": None,
    }


def main():
    st.title(":rainbow[LAB-UP]")
    st.subheader(
        "Upload your worksheets directly to Samvidha without any hassle")

    if st.session_state['cookies']:
        cookies = st.session_state['cookies']
        img = st.session_state['user_details']['img']
        name = st.session_state['user_details']['name']
        branch = st.session_state['user_details']['branch']
        ay = st.session_state['details']['ay']
        roll = st.session_state['details']['roll']
        batch = st.session_state['details']['batch']
        sem = st.session_state['details']['sem']
        subjects = st.session_state['worksheet']['subjects']

        st.success("You have logged in successfully")
        st.write("\n\n")

        if not img or not name or not branch:
            with st.spinner("Loading user details..."):
                st.session_state['user_details']['name'], st.session_state['user_details']['branch'], \
                    st.session_state['user_details']['img'] = got_name(
                    cookies)
        user_page(st.session_state['user_details']['name'], st.session_state['user_details']['branch'],
                  st.session_state['user_details']['img'])
        if st.button("Logout", type="primary"):
            st.session_state['cookies'] = None
            st.session_state['user_details'] = {
                "img": None,
                "name": None,
                "branch": None,
            }
            st.session_state['details'] = {
                'ay': None,
                'roll': None,
                'batch': None,
                'sem': None
            }
            st.session_state['worksheet'] = {
                'subjects': None,
                "choosen_subject": None
            }
            st.rerun()
        st.header('', divider='rainbow')

        if not ay or not roll or not batch or not sem or not subjects:
            with st.spinner('Loading Subjects...'):
                lab_page = got_page(cookies)
                st.session_state['details']['ay'], st.session_state['details']['roll'], st.session_state['details'][
                    'batch'], st.session_state['details']['sem'] = got_details(lab_page)
                st.session_state['worksheet']['subjects'] = got_subjects(
                    lab_page)
        st.session_state['worksheet']['choosen_subject'] = st.selectbox(
            'Select Subject',
            st.session_state['worksheet']['subjects'],
            index=None,
            placeholder="Choose Subject...",
        )
        choosen_subject = st.session_state['worksheet']['choosen_subject']
        if not choosen_subject:
            st.write("Please choose a subject")
            return

        sub_code = choosen_subject.split("-")[0].strip()
        with st.spinner('Loading Open Worksheets...'):
            open_worksheet_table = get_open_lab_worksheets(
                cookies, st.session_state['details']['ay'], sub_code)
        if open_worksheet_table.empty:
            st.error("No open worksheets found")
            return
        st.subheader("Your open worksheets")
        st.table(open_worksheet_table)
        st.header('', divider='rainbow')

        st.header("Uploaded Worksheets")
        with (st.spinner('Loading Uploaded Worksheets...')):
            st.session_state['worksheet']['uploaded_worksheet_table'] = show_uploaded_lab_worksheets(
                st.session_state['details']['roll'], st.session_state['details']['ay'], sub_code)

        uploaded_worksheet_table = st.session_state['worksheet']['uploaded_worksheet_table']
        if uploaded_worksheet_table.empty:
            st.error("No uploaded worksheets found")
            return
        st.table(uploaded_worksheet_table)
        if st.button("Refresh", type="primary"):
            st.session_state['worksheet']['uploaded_worksheet_table'] = show_uploaded_lab_worksheets(
                st.session_state['details']['roll'], st.session_state['details']['ay'], sub_code)
            st.rerun()
        st.header('', divider='rainbow')

        st.header("Upload your Worksheets")
        weeks, titles = uploadable_weeks(
            open_worksheet_table, uploaded_worksheet_table)
        if len(weeks) == 0:
            st.error("No worksheets to upload")
            return
        choosen_week = st.selectbox(
            'Choose your week',
            weeks,
            index=None,
            placeholder="Choose your week"
        )
        if not choosen_week:
            st.write("Please choose a week")
            return

        week_no = choosen_week.split("-")[1]
        title = titles[weeks.index(choosen_week)]
        upload_form = st.form("upload_form")
        upload_form.text_input("Academic Year", value=st.session_state['details']['ay'], disabled=True)
        upload_form.text_input("Semester", value=st.session_state['details']['sem'], disabled=True)
        upload_form.text_input(
            "Subject Code", value=sub_code, disabled=True)
        upload_form.text_input(
            "Week", value=choosen_week, disabled=True)
        roll = upload_form.text_input("Roll Number", value=st.session_state['details']['roll'])
        batch = upload_form.text_input("Batch", value=st.session_state['details']['batch'])
        title = upload_form.text_input(
            "Worksheet Title", value=title)
        file = upload_form.file_uploader("Upload your worksheet", type=['pdf'])
        upload_button = upload_form.form_submit_button("Upload", type="primary")

        if upload_button:
            if not file or not roll or not batch or not title:
                st.error("Please fill all the fields")
                return
            with st.spinner('Uploading...'):
                log = upload_worksheet(cookies, st.session_state['details']['ay'], st.session_state['details']['sem'],
                                       sub_code,
                                       week_no, roll, batch, title, file)
            st.info(f"Status: {log['status']}")
            st.info(f"Message: {log['msg']}")
            if log['status'] == 'success':
                st.success("Worksheet uploaded successfully")
            else:
                st.error("Worksheet upload failed")

    else:
        st.write("\n\n")
        st.text("Provide your Samvidha login credentials")

        login_form = st.form("login_form")
        username = login_form.text_input(
            "Username", placeholder="Username", autocomplete="username")
        password = login_form.text_input(
            "Password", type="password", placeholder="Password", autocomplete="current-password")
        submit_button = login_form.form_submit_button("Login")

        if submit_button:
            if not username or not password:
                st.error("Please fill all the fields")
                return
            with st.spinner('Logging in...'):
                session_cookies = login_user(
                    username, password)
            if session_cookies:
                st.session_state['cookies'] = session_cookies
                st.rerun()
            else:
                st.toast("Login failed, Please check your credentials", icon="😭")


main()